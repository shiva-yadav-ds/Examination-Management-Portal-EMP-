from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    make_response,
)
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from decorators import role_required
from extensions import db
from models import (
    Booking,
    Course,
    Evaluation,
    Examination,
    ExaminerProfile,
    ExamSlot,
    Rubric,
    User,
)
from services import (
    BOOKING_CLOSED_STATUS,
    LEGACY_BOOKING_CLOSED_STATUSES,
    begin_immediate_write_transaction,
    find_student_time_conflict,
    get_incomplete_bookings_for_exam,
    get_rubric_total,
    lock_examination_for_lifecycle_change,
    release_slot_seat,
    reserve_slot_seat,
)
from utils import (
    get_booking_window_info,
    get_slot_creation_window_info,
    is_booking_open,
    is_slot_creation_open,
)

# Admin controller for creating the data that other roles consume. A Course
# leads to an Examination, an Examination owns Rubrics and ExamSlots, and the
# final lifecycle actions inspect Bookings/Evaluations. Every route below is
# protected by both Flask-Login and role_required("admin") before it can change
# those shared records.
admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# Administrator dashboard.
# Aggregates system metrics (courses, examinations, active examiners, registered students,
# pending examiner approvals, total slots, total bookings) for the high-level portal overview.
@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    course_count = Course.query.count()
    examination_count = Examination.query.count()

    examiner_count = User.query.filter_by(role="examiner").count()
    student_count = User.query.filter_by(role="student").count()

    pending_examiner_count = User.query.filter_by(
        role="examiner", status="pending"
    ).count()

    slot_count = ExamSlot.query.count()
    booking_count = Booking.query.count()

    return render_template(
        "admin/dashboard.html",
        course_count=course_count,
        examination_count=examination_count,
        examiner_count=examiner_count,
        student_count=student_count,
        pending_examiner_count=pending_examiner_count,
        slot_count=slot_count,
        booking_count=booking_count,
    )


# Course management directory.
# Lists all registered academic subjects and courses in reverse chronological order.
@admin_bp.route("/courses")
@login_required
@role_required("admin")
def courses():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("admin/courses.html", courses=courses)


# Creates a new academic course.
# Validates code uniqueness across the portal before inserting.
@admin_bp.route("/courses/create", methods=["POST"])
@login_required
@role_required("admin")
def create_course():
    code = request.form.get("code", "").strip().upper()
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not code or not name:
        flash("Course code and name are required.", "danger")
        return redirect(url_for("admin.courses"))

    if Course.query.filter_by(code=code).first():
        flash("A course with this code already exists.", "danger")
        return redirect(url_for("admin.courses"))

    db.session.add(Course(code=code, name=name, description=description or None))
    db.session.commit()
    flash("Course created successfully.", "success")
    return redirect(url_for("admin.courses"))


# Updates course metadata in-place.
# Ensures the modified course code does not clash with any other existing course.
@admin_bp.route("/courses/<int:course_id>/edit", methods=["POST"])
@login_required
@role_required("admin")
def edit_course(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("admin.courses"))

    code = request.form.get("code", "").strip().upper()
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not code or not name:
        flash("Course code and name are required.", "danger")
        return redirect(url_for("admin.courses"))

    if Course.query.filter(Course.code == code, Course.id != course_id).first():
        flash("Another course already uses this code.", "danger")
        return redirect(url_for("admin.courses"))

    course.code = code
    course.name = name
    course.description = description or None
    db.session.commit()

    flash("Course updated successfully.", "success")
    return redirect(url_for("admin.courses"))


# Soft-deactivates an academic course.
# Keeps historical examinations intact while preventing new exams from being assigned to it.
@admin_bp.route("/courses/<int:course_id>/deactivate", methods=["POST"])
@login_required
@role_required("admin")
def deactivate_course(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("admin.courses"))

    course.status = "inactive"
    db.session.commit()
    flash("Course deactivated successfully.", "success")
    return redirect(url_for("admin.courses"))


# Examiner directory.
# Shows all faculty accounts, their approval statuses (active/pending/inactive), and department info.
@admin_bp.route("/examiners")
@login_required
@role_required("admin")
def examiners():
    all_examiners = (
        User.query
        .filter_by(role="examiner")
        .order_by(User.created_at.desc())
        .all()
    )
    return render_template("admin/examiners.html", examiners=all_examiners)


# Direct creation of examiner accounts by administrator.
# Unlike self-signup, this creates an immediately active faculty account with attached profile.
@admin_bp.route("/examiners/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_examiner():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()
        contact = request.form.get("contact", "").strip()

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("admin/examiners_add.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("admin/examiners_add.html")

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="examiner",
            status="active",
        )
        db.session.add(user)
        db.session.flush()

        db.session.add(ExaminerProfile(
            user_id=user.id,
            department=department or None,
            contact=contact or None,
        ))
        db.session.commit()

        flash(f"Examiner {name} added and activated successfully.", "success")
        return redirect(url_for("admin.examiners"))

    return render_template("admin/examiners_add.html")


# Approves a self-registered examiner account.
# Transitions user status from 'pending' to 'active', allowing faculty to log in.
@admin_bp.route("/examiners/<int:examiner_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve_examiner(examiner_id):
    examiner = db.session.get(User, examiner_id)
    if not examiner or examiner.role != "examiner":
        flash("Examiner not found.", "danger")
        return redirect(url_for("admin.examiners"))

    examiner.status = "active"
    db.session.commit()
    flash(f"{examiner.name} approved and activated.", "success")
    return redirect(url_for("admin.examiners"))


# Revokes faculty access by setting status to 'inactive'.
@admin_bp.route("/examiners/<int:examiner_id>/deactivate", methods=["POST"])
@login_required
@role_required("admin")
def deactivate_examiner(examiner_id):
    examiner = db.session.get(User, examiner_id)
    if not examiner or examiner.role != "examiner":
        flash("Examiner not found.", "danger")
        return redirect(url_for("admin.examiners"))

    examiner.status = "inactive"
    db.session.commit()
    flash(f"{examiner.name} has been deactivated.", "warning")
    return redirect(url_for("admin.examiners"))


# Restores active status to a previously deactivated examiner.
@admin_bp.route("/examiners/<int:examiner_id>/reactivate", methods=["POST"])
@login_required
@role_required("admin")
def reactivate_examiner(examiner_id):
    examiner = db.session.get(User, examiner_id)
    if not examiner or examiner.role != "examiner":
        flash("Examiner not found.", "danger")
        return redirect(url_for("admin.examiners"))

    examiner.status = "active"
    db.session.commit()
    flash(f"{examiner.name} has been reactivated.", "success")
    return redirect(url_for("admin.examiners"))


# Supported examination evaluation types
EXAM_TYPES = ["Viva", "Practical", "Project Demo", "Assessment"]


# Examinations list.
# Shows all exams, their respective courses, statuses, and links to detailed management.
@admin_bp.route("/exams")
@login_required
@role_required("admin")
def exams():
    all_exams = Examination.query.order_by(Examination.created_at.desc()).all()
    active_courses = Course.query.filter_by(status="active").order_by(Course.name).all()
    return render_template(
        "admin/exams.html",
        exams=all_exams,
        courses=active_courses,
        exam_types=EXAM_TYPES,
    )


# Creates a new examination under an active course in 'Draft' status.
# Validates duration, max marks, and chronological ordering of timeline dates.
@admin_bp.route("/exams/create", methods=["POST"])
@login_required
@role_required("admin")
def create_exam():
    course_id = request.form.get("course_id", "").strip()
    name = request.form.get("name", "").strip()
    exam_type = request.form.get("type", "").strip()
    duration = request.form.get("duration", "").strip()
    max_marks = request.form.get("max_marks", "").strip()
    slot_creation_start = request.form.get("slot_creation_start", "").strip()
    slot_creation_end = request.form.get("slot_creation_end", "").strip()
    booking_start = request.form.get("booking_start", "").strip()
    booking_end = request.form.get("booking_end", "").strip()

    if not all([course_id, name, exam_type, duration, max_marks]):
        flash("Course, name, type, duration, and max marks are required.", "danger")
        return redirect(url_for("admin.exams"))

    try:
        duration = int(duration)
        max_marks = int(max_marks)
        assert duration > 0 and max_marks > 0
    except (ValueError, AssertionError):
        flash("Duration and max marks must be positive numbers.", "danger")
        return redirect(url_for("admin.exams"))

    # Helper function to parse ISO datetime strings from HTML datetime-local inputs
    def parse_dt(s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M") if s else None

    try:
        scs = parse_dt(slot_creation_start)
        sce = parse_dt(slot_creation_end)
        bs = parse_dt(booking_start)
        be = parse_dt(booking_end)
    except ValueError:
        flash("Invalid date format. Use the date-time picker.", "danger")
        return redirect(url_for("admin.exams"))

    # Validate timeline order if dates provided
    if scs and sce and scs >= sce:
        flash("Slot creation start must be before slot creation end.", "danger")
        return redirect(url_for("admin.exams"))
    if bs and be and bs >= be:
        flash("Booking start must be before booking end.", "danger")
        return redirect(url_for("admin.exams"))

    exam = Examination(
        course_id=int(course_id),
        name=name,
        type=exam_type,
        duration=duration,
        max_marks=max_marks,
        slot_creation_start=scs,
        slot_creation_end=sce,
        booking_start=bs,
        booking_end=be,
        status="Draft",
    )
    db.session.add(exam)
    db.session.commit()
    flash("Examination created successfully.", "success")
    return redirect(url_for("admin.exam_detail", exam_id=exam.id))


# Examination management hub.
# Shows timeline settings, status transition action buttons, and attached rubric criteria.
@admin_bp.route("/exams/<int:exam_id>")
@login_required
@role_required("admin")
def exam_detail(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam:
        flash("Examination not found.", "danger")
        return redirect(url_for("admin.exams"))

    active_courses = Course.query.filter_by(status="active").order_by(Course.name).all()
    rubric_total = sum(r.max_marks for r in exam.rubrics)
    response = make_response(render_template(
        "admin/exam_detail.html",
        exam=exam,
        courses=active_courses,
        exam_types=EXAM_TYPES,
        rubric_total=rubric_total,
    ))
    # Prevent browser caching of exam detail page to ensure fresh status after state changes
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Updates exam properties.
# Restricted to exams in 'Draft' status to prevent modifying rules once slots/bookings exist.
@admin_bp.route("/exams/<int:exam_id>/edit", methods=["POST"])
@login_required
@role_required("admin")
def edit_exam(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam:
        flash("Examination not found.", "danger")
        return redirect(url_for("admin.exams"))

    if exam.status not in ["Draft", "Slot Creation", "Booking Open"]:
        flash("Examinations can only be edited before booking is closed.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    name = request.form.get("name", "").strip()
    exam_type = request.form.get("type", "").strip()
    duration = request.form.get("duration", "").strip()
    max_marks = request.form.get("max_marks", "").strip()
    slot_creation_start = request.form.get("slot_creation_start", "").strip()
    slot_creation_end = request.form.get("slot_creation_end", "").strip()
    booking_start = request.form.get("booking_start", "").strip()
    booking_end = request.form.get("booking_end", "").strip()

    if not all([name, exam_type, duration, max_marks]):
        flash("Name, type, duration, and max marks are required.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    try:
        duration = int(duration)
        max_marks = int(max_marks)
        assert duration > 0 and max_marks > 0
    except (ValueError, AssertionError):
        flash("Duration and max marks must be positive numbers.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    def parse_dt(s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M") if s else None

    try:
        scs = parse_dt(slot_creation_start)
        sce = parse_dt(slot_creation_end)
        bs = parse_dt(booking_start)
        be = parse_dt(booking_end)
    except ValueError:
        flash("Invalid date format.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    if scs and sce and scs >= sce:
        flash("Slot creation start must be before slot creation end.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))
    if bs and be and bs >= be:
        flash("Booking start must be before booking end.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    exam.name = name
    exam.type = exam_type
    exam.duration = duration
    exam.max_marks = max_marks
    exam.slot_creation_start = scs
    exam.slot_creation_end = sce
    exam.booking_start = bs
    exam.booking_end = be
    db.session.commit()

    flash("Examination updated successfully.", "success")
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# State transition: Draft -> Slot Creation.
# Unlocks slot scheduling for faculty during the configured slot creation window.
@admin_bp.route("/exams/<int:exam_id>/open-slots", methods=["POST"])
@login_required
@role_required("admin")
def open_slot_creation(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam or exam.status != "Draft":
        flash("Exam must be in Draft status to open slot creation.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    if not exam.slot_creation_start or not exam.slot_creation_end:
        flash("Cannot open slot creation: Both slot creation start and end dates must be configured.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    if exam.slot_creation_start >= exam.slot_creation_end:
        flash("Cannot open slot creation: Slot creation start date must be earlier than slot creation end date.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    exam.status = "Slot Creation"
    db.session.commit()
    flash(
        f"Slot creation phase is now open for {exam.name}. "
        f"Faculty examiners can now create time slots within the configured window.",
        "success",
    )
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# State transition: Slot Creation -> Booking Open.
# Enforces business rules: At least one active slot must exist, and booking window must be valid.
# Opening booking does NOT automatically create or modify any slots.
@admin_bp.route("/exams/<int:exam_id>/open-booking", methods=["POST"])
@login_required
@role_required("admin")
def open_booking(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam or exam.status != "Slot Creation":
        flash("Exam must be in Slot Creation status before opening student booking.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    # Guard: At least one active/valid slot must exist
    valid_slots = [s for s in exam.slots if s.status != "Cancelled"]
    if not valid_slots:
        flash(
            f"Cannot open student booking for {exam.name}: At least one active exam slot must exist. "
            "Please wait for an examiner to create time slots first.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    # Guard: Booking start and end dates must be configured
    if not exam.booking_start or not exam.booking_end:
        flash(
            f"Cannot open student booking for {exam.name}: Both booking start and end dates must be configured.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    # Guard: Booking start must be before booking end
    if exam.booking_start >= exam.booking_end:
        flash(
            f"Cannot open student booking for {exam.name}: Booking start date must be earlier than booking end date.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    exam.status = "Booking Open"
    db.session.commit()
    extra = ""
    if is_slot_creation_open(exam):
        extra = (
            f" Slot creation window is still open until "
            f"{exam.slot_creation_end.strftime('%d %b %Y, %H:%M')} — examiners can still add more slots."
        )
    flash(
        f"Student booking is now open for {exam.name}. "
        f"Students can now reserve from {len(valid_slots)} available slot(s).{extra}",
        "success",
    )
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# State transition: Booking Open -> Booking Closed.
# Closes student reservation window prior to exam execution.
@admin_bp.route("/exams/<int:exam_id>/close-booking", methods=["POST"])
@login_required
@role_required("admin")
def close_booking(exam_id):
    begin_immediate_write_transaction()
    exam = lock_examination_for_lifecycle_change(exam_id)
    if not exam:
        db.session.rollback()
        flash("Examination not found.", "danger")
        return redirect(url_for("admin.exams"))

    if exam.status in LEGACY_BOOKING_CLOSED_STATUSES:
        db.session.rollback()
        flash("Booking is already closed for this examination.", "info")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    if exam.status != "Booking Open":
        db.session.rollback()
        flash(
            f"Cannot close booking while the exam is in '{exam.status}'. "
            "Open student booking first, then use Close Booking.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    now = datetime.now()
    # Align the booking window with the manual close so date checks and status agree.
    if exam.booking_end is None or exam.booking_end > now:
        exam.booking_end = now
    exam.status = BOOKING_CLOSED_STATUS
    db.session.commit()
    flash(
        "Booking closed. Students can no longer book or cancel slots. "
        "Examiners can continue evaluating booked students. When grading is done, mark the exam Completed and publish results.",
        "success",
    )
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# State transition: Booking Closed -> Completed.
# Marks the examination period as concluded once all slots and evaluations are finished.
@admin_bp.route("/exams/<int:exam_id>/complete", methods=["POST"])
@login_required
@role_required("admin")
def complete_exam(exam_id):
    begin_immediate_write_transaction()
    exam = lock_examination_for_lifecycle_change(exam_id)
    if not exam:
        db.session.rollback()
        flash("Examination not found.", "danger")
        return redirect(url_for("admin.exams"))

    if exam.status not in (*LEGACY_BOOKING_CLOSED_STATUSES, "Completed"):
        db.session.rollback()
        flash("Exam must be Booking Closed before marking as Completed.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    if exam.status == "Completed":
        db.session.rollback()
        flash("Examination is already marked as Completed.", "info")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    incomplete = get_incomplete_bookings_for_exam(exam)
    if incomplete:
        db.session.rollback()
        flash(
            f"Cannot complete {exam.name}: {len(incomplete)} active booking(s) still need complete evaluation.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    exam.status = "Completed"
    for slot in exam.slots:
        if slot.status != "Cancelled":
            slot.status = "Completed"
    db.session.commit()
    flash("Examination marked as Completed.", "success")
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# Releases official grades and rubric feedback to students.
# Sets results_published = True, unlocking scorecards on student dashboards.
@admin_bp.route("/exams/<int:exam_id>/publish-results", methods=["POST"])
@login_required
@role_required("admin")
def publish_results(exam_id):
    begin_immediate_write_transaction()
    exam = lock_examination_for_lifecycle_change(exam_id)
    if not exam:
        db.session.rollback()
        flash("Examination not found.", "danger")
        return redirect(url_for("admin.exams"))

    if exam.status != "Completed":
        db.session.rollback()
        flash(
            "Mark the examination Completed before publishing results.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    if exam.results_published:
        db.session.rollback()
        flash("Results are already published.", "info")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    rubric_total = get_rubric_total(exam)
    if not exam.rubrics or rubric_total != exam.max_marks:
        db.session.rollback()
        flash(
            f"Cannot publish results: rubric total must equal exam max marks ({exam.max_marks}). Current total: {rubric_total}.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    incomplete = get_incomplete_bookings_for_exam(exam)
    if incomplete:
        db.session.rollback()
        flash(
            f"Cannot publish results: {len(incomplete)} active booking(s) still have incomplete evaluations.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    exam.results_published = True
    db.session.commit()
    flash("Results published. Students can now view their scores.", "success")
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# Adds a grading criterion (rubric) to an examination.
# Enforces validation that the sum of all rubric max marks does not exceed the exam's total max marks.
@admin_bp.route("/exams/<int:exam_id>/rubrics/add", methods=["POST"])
@login_required
@role_required("admin")
def add_rubric(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam:
        flash("Examination not found.", "danger")
        return redirect(url_for("admin.exams"))

    criterion_name = request.form.get("criterion_name", "").strip()
    max_marks = request.form.get("max_marks", "").strip()
    weightage = request.form.get("weightage", "").strip()
    description = request.form.get("description", "").strip()

    if not criterion_name or not max_marks:
        flash("Criterion name and max marks are required.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    try:
        max_marks = int(max_marks)
        assert max_marks > 0
    except (ValueError, AssertionError):
        flash("Max marks must be a positive number.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    # Guard: sum of rubric max_marks must not exceed exam max_marks
    current_total = sum(r.max_marks for r in exam.rubrics)
    if current_total + max_marks > exam.max_marks:
        flash(
            f"Adding {max_marks} marks would exceed exam max marks ({exam.max_marks}). "
            f"Current rubric total: {current_total}.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    try:
        weightage_val = float(weightage) if weightage else None
    except ValueError:
        flash("Weightage must be a number.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    rubric = Rubric(
        exam_id=exam_id,
        criterion_name=criterion_name,
        max_marks=max_marks,
        weightage=weightage_val,
        description=description or None,
    )
    db.session.add(rubric)
    db.session.commit()
    flash(f'Rubric "{criterion_name}" added.', "success")
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# Edits an existing grading criterion before any scores have been recorded.
@admin_bp.route("/exams/<int:exam_id>/rubrics/<int:rubric_id>/edit", methods=["POST"])
@login_required
@role_required("admin")
def edit_rubric(exam_id, rubric_id):
    rubric = db.session.get(Rubric, rubric_id)
    if not rubric or rubric.exam_id != exam_id:
        flash("Rubric not found.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    if rubric.evaluations:
        flash("Cannot edit this rubric because evaluations have already been recorded against it.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    exam = rubric.examination
    criterion_name = request.form.get("criterion_name", "").strip()
    max_marks = request.form.get("max_marks", "").strip()
    weightage = request.form.get("weightage", "").strip()
    description = request.form.get("description", "").strip()

    if not criterion_name or not max_marks:
        flash("Criterion name and max marks are required.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    try:
        max_marks = int(max_marks)
        assert max_marks > 0
    except (ValueError, AssertionError):
        flash("Max marks must be a positive number.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    other_total = sum(r.max_marks for r in exam.rubrics if r.id != rubric.id)
    if other_total + max_marks > exam.max_marks:
        flash(
            f"Updating this criterion to {max_marks} marks would exceed exam max marks ({exam.max_marks}). "
            f"Other rubric total: {other_total}.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    try:
        weightage_val = float(weightage) if weightage else None
    except ValueError:
        flash("Weightage must be a number.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    rubric.criterion_name = criterion_name
    rubric.max_marks = max_marks
    rubric.weightage = weightage_val
    rubric.description = description or None
    db.session.commit()
    flash(f'Rubric "{criterion_name}" updated.', "success")
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# Deletes an evaluation rubric criterion.
# Blocked if evaluations have already been recorded against it to preserve data integrity.
@admin_bp.route("/exams/<int:exam_id>/rubrics/<int:rubric_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_rubric(exam_id, rubric_id):
    rubric = db.session.get(Rubric, rubric_id)
    if not rubric or rubric.exam_id != exam_id:
        flash("Rubric not found.", "danger")
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    if rubric.evaluations:
        flash(
            "Cannot delete this rubric - evaluations have already been recorded against it.",
            "danger",
        )
        return redirect(url_for("admin.exam_detail", exam_id=exam_id))

    db.session.delete(rubric)
    db.session.commit()
    flash(f'Rubric "{rubric.criterion_name}" deleted.', "success")
    return redirect(url_for("admin.exam_detail", exam_id=exam_id))


# Central slot management table across all examinations.
# Supports filtering by examination, faculty examiner, and slot availability status.
@admin_bp.route("/slots")
@login_required
@role_required("admin")
def slots():
    exam_id = request.args.get("exam_id", type=int)
    examiner_id = request.args.get("examiner_id", type=int)
    status_filter = request.args.get("status", "").strip()

    query = ExamSlot.query.order_by(ExamSlot.exam_date.desc(), ExamSlot.start_time.asc())
    if exam_id:
        query = query.filter(ExamSlot.exam_id == exam_id)
    if examiner_id:
        query = query.filter(ExamSlot.examiner_id == examiner_id)
    if status_filter:
        query = query.filter(ExamSlot.status == status_filter)

    all_slots = query.all()
    exams = Examination.query.order_by(Examination.name).all()
    examiners = User.query.filter_by(role="examiner", status="active").order_by(User.name).all()

    return render_template(
        "admin/slots.html",
        slots=all_slots,
        exams=exams,
        examiners=examiners,
        selected_exam_id=exam_id,
        selected_examiner_id=examiner_id,
        selected_status=status_filter,
    )


# Reassigns an existing slot to a different examiner.
# Enforces clash detection to prevent assigning an examiner who already has an overlapping slot.
@admin_bp.route("/slots/<int:slot_id>/change-examiner", methods=["POST"])
@login_required
@role_required("admin")
def change_examiner(slot_id):
    slot = db.session.get(ExamSlot, slot_id)
    if not slot:
        flash("Slot not found.", "danger")
        return redirect(url_for("admin.slots"))

    new_examiner_id = request.form.get("examiner_id", type=int)
    if not new_examiner_id:
        flash("Please select an examiner.", "danger")
        return redirect(url_for("admin.slots"))

    new_examiner = db.session.get(User, new_examiner_id)
    if not new_examiner or new_examiner.role != "examiner" or new_examiner.status != "active":
        flash("Selected user is not an active examiner.", "danger")
        return redirect(url_for("admin.slots"))

    if new_examiner.id == slot.examiner_id:
        flash("Selected examiner is already assigned to this slot.", "info")
        return redirect(url_for("admin.slots"))

    # Clash check: ensure new examiner has no overlapping slot on the same date
    clash = ExamSlot.query.filter(
        ExamSlot.examiner_id == new_examiner.id,
        ExamSlot.exam_date == slot.exam_date,
        ExamSlot.id != slot.id,
        ExamSlot.status != "Cancelled",
        ExamSlot.start_time < slot.end_time,
        ExamSlot.end_time > slot.start_time,
    ).first()

    if clash:
        flash(
            f"Examiner {new_examiner.name} has an overlapping slot on {slot.exam_date} "
            f"({clash.start_time.strftime('%H:%M')} - {clash.end_time.strftime('%H:%M')}).",
            "danger",
        )
        return redirect(url_for("admin.slots"))

    old_name = slot.examiner.name
    slot.examiner_id = new_examiner.id
    db.session.commit()
    flash(f"Slot reassigned from {old_name} to {new_examiner.name}.", "success")
    return redirect(url_for("admin.slots"))


# Portal-wide booking audit log.
# Displays all student reservations (Booked, Cancelled, Completed) with candidate slots for rescheduling.
@admin_bp.route("/bookings")
@login_required
@role_required("admin")
def bookings():
    exam_id = request.args.get("exam_id", type=int)
    status_filter = request.args.get("status", "").strip()

    query = Booking.query.order_by(Booking.booking_date.desc())
    if exam_id:
        query = query.filter(Booking.exam_id == exam_id)
    if status_filter:
        query = query.filter(Booking.status == status_filter)

    all_bookings = query.all()
    exams = Examination.query.order_by(Examination.name).all()

    # Provide candidate slots for rescheduling (Available slots with free seats)
    available_slots = (
        ExamSlot.query.filter(ExamSlot.status == "Available", ExamSlot.available_seats > 0)
        .order_by(ExamSlot.exam_date.asc(), ExamSlot.start_time.asc())
        .all()
    )

    return render_template(
        "admin/bookings.html",
        bookings=all_bookings,
        exams=exams,
        available_slots=available_slots,
        selected_exam_id=exam_id,
        selected_status=status_filter,
    )


# Administratively shifts a student's booking from one slot to another within the same exam.
# Atomically frees the old seat, occupies the new seat, and records the change in rescheduled_from.
@admin_bp.route("/bookings/<int:booking_id>/reschedule", methods=["POST"])
@login_required
@role_required("admin")
def reschedule_booking(booking_id):
    begin_immediate_write_transaction()
    booking = db.session.get(Booking, booking_id)
    if not booking:
        db.session.rollback()
        flash("Booking not found.", "danger")
        return redirect(url_for("admin.bookings"))

    if booking.status != "Booked":
        db.session.rollback()
        flash("Only active booked appointments can be rescheduled.", "danger")
        return redirect(url_for("admin.bookings"))

    if booking.evaluations:
        db.session.rollback()
        flash("Cannot reschedule a booking that has already been evaluated.", "danger")
        return redirect(url_for("admin.bookings"))

    new_slot_id = request.form.get("new_slot_id", type=int)
    if not new_slot_id:
        db.session.rollback()
        flash("Please select a target slot.", "danger")
        return redirect(url_for("admin.bookings"))

    new_slot = db.session.get(ExamSlot, new_slot_id)
    if not new_slot:
        db.session.rollback()
        flash("Selected slot not found.", "danger")
        return redirect(url_for("admin.bookings"))

    if new_slot.exam_id != booking.exam_id:
        db.session.rollback()
        flash("New slot must belong to the same examination.", "danger")
        return redirect(url_for("admin.bookings"))

    if new_slot.id == booking.slot_id:
        db.session.rollback()
        flash("Booking is already assigned to this slot.", "info")
        return redirect(url_for("admin.bookings"))

    if new_slot.status != "Available" or new_slot.available_seats <= 0:
        db.session.rollback()
        flash("Selected slot has no available seats.", "danger")
        return redirect(url_for("admin.bookings"))

    conflict = find_student_time_conflict(
        booking.student_id,
        new_slot,
        exclude_booking_id=booking.id,
    )
    if conflict:
        db.session.rollback()
        flash(
            "Cannot reschedule: the student already has an active booking that overlaps the target slot.",
            "danger",
        )
        return redirect(url_for("admin.bookings"))

    old_slot = booking.slot

    try:
        release_slot_seat(old_slot)
        if not reserve_slot_seat(new_slot):
            raise ValueError("Selected slot has no available seats.")

        booking.rescheduled_from = old_slot.id
        booking.slot_id = new_slot.id
        booking.rescheduled_at = datetime.now()

        db.session.commit()
    except (IntegrityError, ValueError):
        db.session.rollback()
        flash("Reschedule failed. The original booking was preserved.", "danger")
        return redirect(url_for("admin.bookings"))

    flash(
        f"Booking for {booking.student.name} successfully rescheduled to "
        f"{new_slot.exam_date} ({new_slot.start_time.strftime('%H:%M')}).",
        "success",
    )
    return redirect(url_for("admin.bookings"))


# Registered student directory.
# Supports live search by student name, email, or institutional roll number.
@admin_bp.route("/students")
@login_required
@role_required("admin")
def students():
    query_str = request.args.get("q", "").strip()
    query = User.query.filter_by(role="student").order_by(User.name)

    if query_str:
        query = query.filter(
            or_(
                User.name.ilike(f"%{query_str}%"),
                User.email.ilike(f"%{query_str}%"),
                User.roll_no.ilike(f"%{query_str}%"),
            )
        )

    all_students = query.all()
    return render_template("admin/students.html", students=all_students, query=query_str)


# Unified global search across multiple entities.
# Searches students, examiners, exams, courses, and booking records simultaneously.
@admin_bp.route("/search")
@login_required
@role_required("admin")
def search():
    q = request.args.get("q", "").strip()
    search_type = request.args.get("type", "all").strip().lower()

    results = {
        "students": [],
        "examiners": [],
        "exams": [],
        "courses": [],
        "bookings": [],
    }

    if q:
        term = f"%{q}%"
        if search_type in ("all", "student"):
            results["students"] = User.query.filter(
                User.role == "student",
                or_(User.name.ilike(term), User.email.ilike(term), User.roll_no.ilike(term)),
            ).all()

        if search_type in ("all", "examiner"):
            results["examiners"] = User.query.filter(
                User.role == "examiner",
                or_(User.name.ilike(term), User.email.ilike(term)),
            ).all()

        if search_type in ("all", "exam"):
            results["exams"] = Examination.query.filter(
                or_(Examination.name.ilike(term), Examination.type.ilike(term))
            ).all()

        if search_type in ("all", "course"):
            results["courses"] = Course.query.filter(
                or_(Course.code.ilike(term), Course.name.ilike(term))
            ).all()

        if search_type in ("all", "booking"):
            results["bookings"] = (
                Booking.query.join(User, Booking.student_id == User.id)
                .join(Examination, Booking.exam_id == Examination.id)
                .filter(
                    or_(
                        User.name.ilike(term),
                        User.roll_no.ilike(term),
                        Examination.name.ilike(term),
                    )
                )
                .all()
            )

    total_count = sum(len(items) for items in results.values())
    return render_template(
        "admin/search.html",
        q=q,
        search_type=search_type,
        results=results,
        total_count=total_count,
    )


# Master gradebook and historical results view.
# Displays all completed student evaluations for an examination along with per-rubric score breakdowns.
@admin_bp.route("/results")
@login_required
@role_required("admin")
def results():
    exam_id = request.args.get("exam_id", type=int)
    all_exams = Examination.query.order_by(Examination.created_at.desc()).all()

    selected_exam = None
    evaluated_bookings = []

    if exam_id:
        selected_exam = db.session.get(Examination, exam_id)
    elif all_exams:
        selected_exam = all_exams[0]

    if selected_exam:
        evaluated_bookings = (
            Booking.query.filter(
                Booking.exam_id == selected_exam.id,
                Booking.status == "Completed",
            )
            .order_by(Booking.booking_date.desc())
            .all()
        )

    return render_template(
        "admin/results.html",
        exams=all_exams,
        selected_exam=selected_exam,
        bookings=evaluated_bookings,
    )


# Administrator profile settings.
# Displays administrator identity, system summary metrics, and allows updating display name and contact phone.
@admin_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("admin")
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name:
            flash("Full name is required.", "danger")
            return redirect(url_for("admin.profile"))

        current_user.name = name
        current_user.phone = phone or None

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("admin.profile"))

    course_count = Course.query.count()
    examination_count = Examination.query.count()
    examiner_count = User.query.filter_by(role="examiner").count()
    student_count = User.query.filter_by(role="student").count()

    return render_template(
        "admin/profile.html",
        course_count=course_count,
        examination_count=examination_count,
        examiner_count=examiner_count,
        student_count=student_count,
    )
