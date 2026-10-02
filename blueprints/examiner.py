from datetime import date, datetime, timedelta

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import select

from decorators import role_required
from extensions import db
from models import Booking, Evaluation, Examination, ExaminerProfile, ExamSlot
from services import (
    BOOKING_CLOSED_STATUS,
    begin_immediate_write_transaction,
    get_evaluation_total,
    lock_examination_for_lifecycle_change,
)
from utils import (
    SLOT_CREATE_STATUSES,
    can_examiner_create_slots,
    get_slot_creation_window_info,
    is_booking_fully_evaluated,
    is_booking_open,
    is_slot_creation_visible_to_examiners,
)

examiner_bp = Blueprint(
    "examiner",
    __name__,
    url_prefix="/examiner"
)


# Examiner dashboard overview.
# Shows counts for exams accepting slots, examiner's scheduled slots, booked students,
# and highlights pending evaluations for past or today's slots needing grading.
@examiner_bp.route("/dashboard")
@login_required
@role_required("examiner")
def dashboard():
    slot_phase_exams = Examination.query.filter(
        Examination.status.in_(SLOT_CREATE_STATUSES)
    ).all()
    open_exams_count = sum(
        1 for ex in slot_phase_exams if is_slot_creation_visible_to_examiners(ex)
    )

    my_slots = ExamSlot.query.filter(
        ExamSlot.examiner_id == current_user.id,
        ExamSlot.status != "Cancelled"
    ).all()
    my_slots_count = len(my_slots)

    my_slot_ids = [s.id for s in my_slots]
    booked_candidates_count = (
        Booking.query.filter(
            Booking.slot_id.in_(my_slot_ids),
            Booking.status.in_(["Booked", "Completed"])
        ).count() if my_slot_ids else 0
    )

    # Pending = booked students on this examiner's slots who are not fully graded.
    # Evaluation is allowed as soon as a student is booked (ownership still enforced).
    pending_evaluations = []
    if my_slot_ids:
        candidate_bookings = (
            Booking.query.join(ExamSlot, Booking.slot_id == ExamSlot.id)
            .filter(
                ExamSlot.examiner_id == current_user.id,
                Booking.status == "Booked",
            )
            .order_by(ExamSlot.exam_date.asc(), ExamSlot.start_time.asc())
            .all()
        )
        pending_evaluations = [
            b for b in candidate_bookings if not is_booking_fully_evaluated(b)
        ]
    pending_count = len(pending_evaluations)

    return render_template(
        "examiner/dashboard.html",
        open_exams_count=open_exams_count,
        my_slots_count=my_slots_count,
        booked_candidates_count=booked_candidates_count,
        pending_count=pending_count,
        pending_evaluations=pending_evaluations,
    )


# Lists all examinations currently in 'Slot Creation' phase.
# Examiners can view exam details and click 'Add Slot' to schedule time for candidates.
@examiner_bp.route("/exams")
@login_required
@role_required("examiner")
def exams():
    # Keep exams visible while Slot Creation OR Booking Open, so faculty can
    # still add slots if the slot-creation window is open (windows may overlap).
    candidate_exams = (
        Examination.query.filter(Examination.status.in_(SLOT_CREATE_STATUSES))
        .order_by(Examination.slot_creation_end.asc())
        .all()
    )
    open_exams = [ex for ex in candidate_exams if is_slot_creation_visible_to_examiners(ex)]
    exam_window_status = {ex.id: get_slot_creation_window_info(ex) for ex in open_exams}
    exam_can_add = {ex.id: can_examiner_create_slots(ex) for ex in open_exams}
    return render_template(
        "examiner/exams.html",
        exams=open_exams,
        exam_window_status=exam_window_status,
        exam_can_add=exam_can_add,
        now=datetime.now(),
    )


# Lists all slots created by the currently logged-in examiner.
# Includes in-place controls to edit or cancel slots before booking begins.
@examiner_bp.route("/slots")
@login_required
@role_required("examiner")
def slots():
    my_slots = (
        ExamSlot.query.filter(
            ExamSlot.examiner_id == current_user.id,
            ExamSlot.status != "Cancelled"
        )
        .order_by(ExamSlot.exam_date.desc(), ExamSlot.start_time.asc())
        .all()
    )
    return render_template("examiner/slots.html", slots=my_slots, now=datetime.now())


# Slot creation form and handler.
# Validates slot creation window using current server datetime (not the scheduled slot date).
# Auto-computes end_time using exam.duration, and enforces time clash detection for faculty.
@examiner_bp.route("/slots/create", methods=["GET", "POST"])
@login_required
@role_required("examiner")
def create_slot():
    if request.method == "POST":
        exam_id = request.form.get("exam_id", type=int)
        slot_date_str = request.form.get("exam_date", "").strip()
        start_time_str = request.form.get("start_time", "").strip()
        capacity = request.form.get("capacity", type=int)

        if not exam_id or not slot_date_str or not start_time_str or not capacity:
            flash("Please fill in all required slot fields.", "danger")
            return redirect(url_for("examiner.create_slot", exam_id=exam_id))

        exam = db.session.get(Examination, exam_id)
        if not exam:
            flash("Examination not found.", "danger")
            return redirect(url_for("examiner.create_slot"))

        if exam.status not in SLOT_CREATE_STATUSES:
            flash(
                f"Cannot create slots for {exam.name}. Current exam phase is {exam.status}.",
                "danger",
            )
            return redirect(url_for("examiner.create_slot"))

        # Verify that slot creation timeline is currently open using current server datetime
        window_info = get_slot_creation_window_info(exam)
        if not window_info["is_open"]:
            flash(window_info["message"], "danger")
            return redirect(url_for("examiner.create_slot", exam_id=exam.id))

        try:
            exam_date = datetime.strptime(slot_date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
        except ValueError:
            flash("Invalid date or time format. Please provide valid date and start time.", "danger")
            return redirect(url_for("examiner.create_slot", exam_id=exam.id))

        if exam_date < date.today():
            flash("Scheduled examination date cannot be in the past.", "danger")
            return redirect(url_for("examiner.create_slot", exam_id=exam.id))

        if capacity < 1:
            flash("Capacity must be at least 1 student.", "danger")
            return redirect(url_for("examiner.create_slot", exam_id=exam.id))

        # Automatically calculate end_time from start_time + exam duration
        start_dt = datetime.combine(exam_date, start_time)
        end_dt = start_dt + timedelta(minutes=exam.duration)
        end_time = end_dt.time()

        # Guard: check for schedule collision with any active slot of this examiner
        clash = ExamSlot.query.filter(
            ExamSlot.examiner_id == current_user.id,
            ExamSlot.exam_date == exam_date,
            ExamSlot.status != "Cancelled",
            ExamSlot.start_time < end_time,
            ExamSlot.end_time > start_time,
        ).first()

        if clash:
            flash(
                f"You already have an active slot on {exam_date.strftime('%d %b %Y')} from {clash.start_time.strftime('%H:%M')} "
                f"to {clash.end_time.strftime('%H:%M')}.",
                "danger",
            )
            return redirect(url_for("examiner.create_slot", exam_id=exam.id))

        new_slot = ExamSlot(
            exam_id=exam.id,
            examiner_id=current_user.id,
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            available_seats=capacity,
            status="Available",
        )
        db.session.add(new_slot)
        db.session.commit()

        flash(
            f"Exam slot created successfully for {exam.name} on {exam_date.strftime('%d %b %Y')} "
            f"({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}, Capacity: {capacity}).",
            "success",
        )
        return redirect(url_for("examiner.slots"))

    open_exams = [
        ex for ex in Examination.query.filter(Examination.status.in_(SLOT_CREATE_STATUSES)).all()
        if is_slot_creation_visible_to_examiners(ex)
    ]
    preselect_exam_id = request.args.get("exam_id", type=int)

    exam_window_details = {
        str(ex.id): {
            "name": ex.name,
            "code": ex.course.code,
            "duration": ex.duration,
            "start": ex.slot_creation_start.strftime("%d %b %Y, %H:%M") if ex.slot_creation_start else None,
            "end": ex.slot_creation_end.strftime("%d %b %Y, %H:%M") if ex.slot_creation_end else None,
            "is_open": can_examiner_create_slots(ex),
            "phase": ex.status,
            "message": get_slot_creation_window_info(ex)["message"],
        }
        for ex in open_exams
    }

    return render_template(
        "examiner/create_slot.html",
        exams=open_exams,
        preselect_exam_id=preselect_exam_id,
        exam_window_details=exam_window_details,
        current_server_time=datetime.now(),
    )


# Updates an existing slot before bookings begin.
# Blocked if any candidate has already reserved a seat or if the booking window is open.
@examiner_bp.route("/slots/<int:slot_id>/edit", methods=["POST"])
@login_required
@role_required("examiner")
def edit_slot(slot_id):
    slot = db.session.get(ExamSlot, slot_id)
    if not slot:
        flash("Slot not found.", "danger")
        return redirect(url_for("examiner.slots"))

    # Security check: faculty can only edit their own slots
    if slot.examiner_id != current_user.id:
        abort(403)

    # Check if slot already has student bookings or booking is open
    active_bookings = Booking.query.filter(
        Booking.slot_id == slot.id,
        Booking.status == "Booked"
    ).count()

    if (
        active_bookings > 0
        or is_booking_open(slot.examination)
        or slot.examination.status in ("Booking Open", BOOKING_CLOSED_STATUS, "Closed", "Completed")
    ):
        flash("Cannot edit slot once booking has opened or students have reserved seats.", "danger")
        return redirect(url_for("examiner.slots"))

    capacity = request.form.get("capacity", type=int)
    slot_date_str = request.form.get("exam_date", "").strip()
    start_time_str = request.form.get("start_time", "").strip()

    if not capacity or not slot_date_str or not start_time_str:
        flash("All fields are required.", "danger")
        return redirect(url_for("examiner.slots"))

    try:
        exam_date = datetime.strptime(slot_date_str, "%Y-%m-%d").date()
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
    except ValueError:
        flash("Invalid date or time format.", "danger")
        return redirect(url_for("examiner.slots"))

    start_dt = datetime.combine(exam_date, start_time)
    end_dt = start_dt + timedelta(minutes=slot.examination.duration)
    end_time = end_dt.time()

    # Clash check excluding current slot
    clash = ExamSlot.query.filter(
        ExamSlot.examiner_id == current_user.id,
        ExamSlot.exam_date == exam_date,
        ExamSlot.id != slot.id,
        ExamSlot.status != "Cancelled",
        ExamSlot.start_time < end_time,
        ExamSlot.end_time > start_time,
    ).first()

    if clash:
        flash(f"Time clash with existing slot on {exam_date}.", "danger")
        return redirect(url_for("examiner.slots"))

    slot.exam_date = exam_date
    slot.start_time = start_time
    slot.end_time = end_time
    slot.capacity = capacity
    slot.available_seats = capacity
    db.session.commit()

    flash("Slot updated successfully.", "success")
    return redirect(url_for("examiner.slots"))


# Soft-cancels an unbooked slot.
# Deletion is prevented if any student holds an active booking on this slot.
@examiner_bp.route("/slots/<int:slot_id>/delete", methods=["POST"])
@login_required
@role_required("examiner")
def delete_slot(slot_id):
    slot = db.session.get(ExamSlot, slot_id)
    if not slot:
        flash("Slot not found.", "danger")
        return redirect(url_for("examiner.slots"))

    if slot.examiner_id != current_user.id:
        abort(403)

    active_bookings = Booking.query.filter(
        Booking.slot_id == slot.id,
        Booking.status == "Booked"
    ).count()

    if active_bookings > 0:
        flash("Cannot cancel a slot that has active student bookings. Contact admin first.", "danger")
        return redirect(url_for("examiner.slots"))

    slot.status = "Cancelled"
    db.session.commit()
    flash("Slot cancelled successfully.", "success")
    return redirect(url_for("examiner.slots"))


# Displays list of students booked for a specific slot.
# Ownership check prevents examiners from viewing other faculty's candidates.
@examiner_bp.route("/slots/<int:slot_id>/students")
@login_required
@role_required("examiner")
def slot_students(slot_id):
    slot = db.session.get(ExamSlot, slot_id)
    if not slot:
        flash("Slot not found.", "danger")
        return redirect(url_for("examiner.slots"))

    if slot.examiner_id != current_user.id:
        abort(403)

    bookings = Booking.query.filter(
        Booking.slot_id == slot.id,
        Booking.status.in_(["Booked", "Completed"])
    ).all()

    # Examiner may grade any booked student on their own slot.
    can_evaluate = True
    evaluation_ready = {b.id: is_booking_fully_evaluated(b) for b in bookings}

    return render_template(
        "examiner/students.html",
        slot=slot,
        bookings=bookings,
        can_evaluate=can_evaluate,
        evaluation_ready=evaluation_ready,
        slot_started=slot.exam_date <= date.today(),
    )


# Evaluates a student against the examination rubric criteria.
# Enforces bounds checks (0 <= marks <= max_marks), upserts evaluation records,
# and transitions the booking status to Completed.
@examiner_bp.route("/evaluate/<int:booking_id>", methods=["GET", "POST"])
@login_required
@role_required("examiner")
def evaluate(booking_id):
    if request.method == "POST":
        begin_immediate_write_transaction()
        booking = db.session.execute(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        ).scalar_one_or_none()
    else:
        booking = db.session.get(Booking, booking_id)
    if not booking:
        flash("Booking record not found.", "danger")
        return redirect(url_for("examiner.dashboard"))

    # Security check: only slot owner can grade the candidate
    if booking.slot.examiner_id != current_user.id:
        abort(403)

    if booking.status == "Cancelled":
        flash("Cannot evaluate a cancelled booking.", "danger")
        return redirect(url_for("examiner.slot_students", slot_id=booking.slot_id))

    exam = (
        lock_examination_for_lifecycle_change(booking.exam_id)
        if request.method == "POST"
        else booking.examination
    )

    if exam.results_published:
        flash("Results are already published. Evaluations can no longer be changed.", "danger")
        return redirect(url_for("examiner.slot_students", slot_id=booking.slot_id))

    rubrics = list(exam.rubrics)

    if not rubrics:
        flash(
            "This examination has no evaluation rubric yet. Ask admin to add criteria before grading.",
            "warning",
        )
        return redirect(url_for("examiner.slot_students", slot_id=booking.slot_id))

    if request.method == "POST":
        eval_records = []

        # Validate marks for each rubric criterion
        for r in rubrics:
            marks_str = request.form.get(f"marks_{r.id}", "").strip()
            remarks = request.form.get(f"remarks_{r.id}", "").strip()

            if not marks_str:
                flash(f"Please provide marks for: {r.criterion_name}", "danger")
                return redirect(url_for("examiner.evaluate", booking_id=booking_id))

            try:
                marks = float(marks_str)
                if marks < 0 or marks > r.max_marks:
                    flash(f"Marks for {r.criterion_name} must be between 0 and {r.max_marks}.", "danger")
                    return redirect(url_for("examiner.evaluate", booking_id=booking_id))
            except ValueError:
                flash(f"Invalid marks value for {r.criterion_name}.", "danger")
                return redirect(url_for("examiner.evaluate", booking_id=booking_id))

            eval_records.append((r.id, marks, remarks))

        total_marks = sum(marks for _, marks, _ in eval_records)
        if total_marks > exam.max_marks:
            flash(
                f"Total marks ({total_marks:g}) cannot exceed exam max marks ({exam.max_marks}).",
                "danger",
            )
            return redirect(url_for("examiner.evaluate", booking_id=booking_id))

        # Upsert: update existing score row or insert a new one
        for rubric_id, marks, remarks in eval_records:
            existing_eval = Evaluation.query.filter_by(booking_id=booking.id, rubric_id=rubric_id).first()
            if existing_eval:
                existing_eval.marks = marks
                existing_eval.remarks = remarks or None
                existing_eval.evaluated_at = datetime.now()
            else:
                new_eval = Evaluation(
                    booking_id=booking.id,
                    rubric_id=rubric_id,
                    marks=marks,
                    remarks=remarks or None,
                    evaluated_at=datetime.now()
                )
                db.session.add(new_eval)

        # Mark booking as completed once all criteria are graded
        booking.status = "Completed"
        db.session.commit()

        flash(f"Evaluation submitted successfully for {booking.student.name}.", "success")
        return redirect(url_for("examiner.slot_students", slot_id=booking.slot_id))

    existing_scores = {e.rubric_id: e for e in booking.evaluations}
    return render_template(
        "examiner/evaluate.html",
        booking=booking,
        exam=exam,
        rubrics=rubrics,
        existing_scores=existing_scores,
        existing_total=get_evaluation_total(booking),
    )


# Examiner profile settings.
# Updates faculty name and associated department/contact details in examiner_profiles.
@examiner_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("examiner")
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        contact = request.form.get("contact", "").strip()

        if not name:
            flash("Name is required.", "danger")
            return redirect(url_for("examiner.profile"))

        current_user.name = name
        if current_user.examiner_profile:
            current_user.examiner_profile.department = department or None
            current_user.examiner_profile.contact = contact or None
        else:
            new_profile = ExaminerProfile(
                user_id=current_user.id,
                department=department or None,
                contact=contact or None
            )
            db.session.add(new_profile)

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("examiner.profile"))

    total_slots = ExamSlot.query.filter_by(examiner_id=current_user.id).count()
    total_candidates = (
        Booking.query.join(ExamSlot, Booking.slot_id == ExamSlot.id)
        .filter(ExamSlot.examiner_id == current_user.id)
        .count()
    )
    completed_evaluations = (
        Booking.query.join(ExamSlot, Booking.slot_id == ExamSlot.id)
        .filter(ExamSlot.examiner_id == current_user.id, Booking.status == "Completed")
        .count()
    )

    return render_template(
        "examiner/profile.html",
        total_slots=total_slots,
        total_candidates=total_candidates,
        completed_evaluations=completed_evaluations,
    )
