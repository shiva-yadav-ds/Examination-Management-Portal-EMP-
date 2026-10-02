from datetime import date, datetime

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    make_response,
)
from flask_login import current_user, login_required
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from decorators import role_required
from extensions import db
from models import Booking, Course, Examination, ExamSlot
from services import (
    begin_immediate_write_transaction,
    find_student_time_conflict,
    has_active_exam_booking,
    lock_examination_for_lifecycle_change,
    release_slot_seat,
    reserve_slot_seat,
)
from utils import can_student_book, get_booking_window_info

# Student controller. It exposes only the logged-in student's schedule,
# bookings, profile, and published results. Its write endpoints coordinate with
# services.py so Booking rows and ExamSlot seat counts change atomically, even
# when two students try to reserve the same remaining seat.
student_bp = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


# Student home dashboard.
# Shows portal summary metrics (open exams, total bookings, published results)
# along with a list of upcoming confirmed exam appointments starting from today.
@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    today = date.today()

    # Query active upcoming bookings ordered chronologically
    upcoming_bookings = (
        Booking.query.join(ExamSlot, Booking.slot_id == ExamSlot.id)
        .filter(
            Booking.student_id == current_user.id,
            Booking.status == "Booked",
            ExamSlot.exam_date >= today,
        )
        .order_by(ExamSlot.exam_date.asc(), ExamSlot.start_time.asc())
        .all()
    )

    open_exams_count = Examination.query.filter_by(status="Booking Open").count()
    my_bookings_count = Booking.query.filter_by(student_id=current_user.id).count()

    # Count of evaluated exams whose results have been officially published by admin
    published_results_count = (
        Booking.query.join(Examination, Booking.exam_id == Examination.id)
        .filter(
            Booking.student_id == current_user.id,
            Booking.status == "Completed",
            Examination.results_published.is_(True),
        )
        .count()
    )

    return render_template(
        "student/dashboard.html",
        upcoming_bookings=upcoming_bookings,
        open_exams_count=open_exams_count,
        my_bookings_count=my_bookings_count,
        published_results_count=published_results_count,
    )


# Examination discovery page.
# Lists all exams currently in 'Booking Open' status.
# Supports optional filtering by course, exam type, and search keyword.
@student_bp.route("/exams")
@login_required
@role_required("student")
def exams():
    course_id = request.args.get("course_id", type=int)
    exam_type = request.args.get("type", "").strip()
    query_str = request.args.get("q", "").strip()

    query = Examination.query.filter_by(status="Booking Open")

    if course_id:
        query = query.filter(Examination.course_id == course_id)
    if exam_type:
        query = query.filter(Examination.type == exam_type)
    if query_str:
        query = query.filter(
            or_(
                Examination.name.ilike(f"%{query_str}%"),
                Examination.type.ilike(f"%{query_str}%"),
            )
        )

    all_exams = [
        exam for exam in query.order_by(Examination.created_at.desc()).all()
        if can_student_book(exam)
    ]
    courses = Course.query.filter_by(status="active").order_by(Course.code).all()

    # Track exams already booked by the student to show 'Already Booked' badge in UI
    active_booked_exam_ids = {
        b.exam_id
        for b in Booking.query.filter_by(
            student_id=current_user.id, status="Booked"
        ).all()
    }

    return render_template(
        "student/exams.html",
        exams=all_exams,
        courses=courses,
        active_booked_exam_ids=active_booked_exam_ids,
        selected_course_id=course_id,
        selected_type=exam_type,
        query_str=query_str,
    )


# Exam detail page.
# Displays exam metadata, rubric criteria breakdown, and all currently available slots.
@student_bp.route("/exams/<int:exam_id>")
@login_required
@role_required("student")
def exam_detail(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam:
        flash("Examination not found.", "danger")
        return redirect(url_for("student.exams"))

    # Check if student already holds a booked seat for this examination
    active_booking = Booking.query.filter_by(
        student_id=current_user.id, exam_id=exam.id, status="Booked"
    ).first()

    # Fetch slots that still have open seats
    available_slots = (
        ExamSlot.query.filter(
            ExamSlot.exam_id == exam.id,
            ExamSlot.status == "Available",
            ExamSlot.available_seats > 0,
        )
        .order_by(ExamSlot.exam_date.asc(), ExamSlot.start_time.asc())
        .all()
    )

    booking_open = can_student_book(exam)
    booking_window_info = get_booking_window_info(exam)

    response = make_response(render_template(
        "student/exam_detail.html",
        exam=exam,
        active_booking=active_booking,
        slots=available_slots,
        booking_open=booking_open,
        booking_window_info=booking_window_info,
        current_server_time=datetime.now(),
    ))
    # Prevent browser caching to ensure fresh booking status
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Slot reservation endpoint.
# Performs safety checks (booking status, booking window using current server datetime, capacity, duplicate check, schedule clash),
# creates the Booking row, and decrements available seats atomically.
@student_bp.route("/book/<int:slot_id>", methods=["POST"])
@login_required
@role_required("student")
def book_slot(slot_id):
    begin_immediate_write_transaction()
    exam_id = db.session.execute(
        select(ExamSlot.exam_id).where(ExamSlot.id == slot_id)
    ).scalar_one_or_none()
    if exam_id is None:
        db.session.rollback()
        flash("Selected slot not found.", "danger")
        return redirect(url_for("student.exams"))

    # Lock the exam before reading its status. Close Booking acquires this
    # same lock, so a stale student page can never create a booking after the
    # close transaction has committed.
    exam = lock_examination_for_lifecycle_change(exam_id)
    if not exam:
        db.session.rollback()
        flash("Selected examination is no longer available.", "danger")
        return redirect(url_for("student.exams"))

    slot = db.session.execute(
        select(ExamSlot).where(ExamSlot.id == slot_id).with_for_update()
    ).scalar_one_or_none()
    if not slot or slot.exam_id != exam.id:
        db.session.rollback()
        flash("Selected slot is no longer available.", "danger")
        return redirect(url_for("student.exams"))

    # Verify that booking is open by both admin status and the date window
    if not can_student_book(exam):
        if exam.status != "Booking Open":
            flash(
                f"Student booking is not currently open for {exam.name} (Current phase: {exam.status}).",
                "danger",
            )
        else:
            flash(get_booking_window_info(exam)["message"], "danger")
        db.session.rollback()
        return redirect(url_for("student.exam_detail", exam_id=exam.id))

    # Verify slot has free capacity
    if slot.status != "Available" or slot.available_seats <= 0:
        db.session.rollback()
        flash("Selected slot is no longer available.", "danger")
        return redirect(url_for("student.exam_detail", exam_id=exam.id))

    # Guard: prevent duplicate booking for the same examination
    existing_booking = has_active_exam_booking(current_user.id, exam.id)

    if existing_booking:
        db.session.rollback()
        flash("You already have an active booking for this examination.", "danger")
        return redirect(url_for("student.exam_detail", exam_id=exam.id))

    # Guard: prevent student from booking two overlapping slots on the same date
    clash = find_student_time_conflict(current_user.id, slot)

    if clash:
        db.session.rollback()
        flash(
            f"You already have a booked slot on {slot.exam_date.strftime('%d %b %Y')} overlapping this time.",
            "danger",
        )
        return redirect(url_for("student.exam_detail", exam_id=exam.id))

    # Create new booking record with current local server timestamp
    booking = Booking(
        student_id=current_user.id,
        exam_id=exam.id,
        slot_id=slot.id,
        status="Booked",
        booking_date=datetime.now(),
    )

    try:
        if not reserve_slot_seat(slot):
            raise ValueError("Selected slot is no longer available.")
        db.session.add(booking)
        db.session.commit()
    except (IntegrityError, ValueError):
        db.session.rollback()
        flash(
            "Booking could not be completed because the slot or your schedule changed. Please try another slot.",
            "danger",
        )
        return redirect(url_for("student.exam_detail", exam_id=exam.id))

    flash(
        f"Slot successfully booked for {exam.name} on {slot.exam_date.strftime('%d %b %Y')} "
        f"({slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}).",
        "success",
    )
    return redirect(url_for("student.bookings"))


# Cancels an active booking before the deadline.
# Releases the reserved seat and restores slot status to Available.
@student_bp.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
@role_required("student")
def cancel_booking(booking_id):
    begin_immediate_write_transaction()
    booking = db.session.execute(
        select(Booking).where(Booking.id == booking_id).with_for_update()
    ).scalar_one_or_none()
    if not booking:
        db.session.rollback()
        flash("Booking not found.", "danger")
        return redirect(url_for("student.bookings"))

    # Security check: ensure student owns this booking
    if booking.student_id != current_user.id:
        db.session.rollback()
        abort(403)

    # Only active Booked records can be cancelled
    if booking.status != "Booked":
        db.session.rollback()
        flash("Only active bookings can be cancelled.", "danger")
        return redirect(url_for("student.bookings"))

    # Check cancellation deadline using current server datetime
    exam = lock_examination_for_lifecycle_change(booking.exam_id)
    now = datetime.now()
    if exam.status != "Booking Open" or (exam.booking_end and now > exam.booking_end):
        db.session.rollback()
        flash(
            f"Cancellation is no longer allowed for {exam.name}. Booking has been closed.",
            "danger",
        )
        return redirect(url_for("student.bookings"))

    slot = booking.slot

    # Soft cancel: keep record for audit history with timestamp
    booking.status = "Cancelled"
    booking.cancelled_at = datetime.now()

    # Restore seat to slot
    release_slot_seat(slot)

    db.session.commit()

    flash(
        f"Booking cancelled successfully for {exam.name}. Your seat has been released.",
        "success",
    )
    return redirect(url_for("student.bookings"))


# Full booking history page (Booked, Cancelled, and Completed).
@student_bp.route("/bookings")
@login_required
@role_required("student")
def bookings():
    my_bookings = (
        Booking.query.filter_by(student_id=current_user.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )
    now = datetime.now()
    return render_template("student/bookings.html", bookings=my_bookings, now=now)


# Chronological schedule of active upcoming exam appointments.
@student_bp.route("/schedule")
@login_required
@role_required("student")
def schedule():
    scheduled_bookings = (
        Booking.query.join(ExamSlot, Booking.slot_id == ExamSlot.id)
        .filter(
            Booking.student_id == current_user.id,
            Booking.status == "Booked",
        )
        .order_by(ExamSlot.exam_date.asc(), ExamSlot.start_time.asc())
        .all()
    )
    return render_template("student/schedule.html", bookings=scheduled_bookings)


# Official published examination results and scorecards.
# Only completed evaluations whose examination has results_published=True are shown.
@student_bp.route("/results")
@login_required
@role_required("student")
def results():
    completed_bookings = (
        Booking.query.join(Examination, Booking.exam_id == Examination.id)
        .filter(
            Booking.student_id == current_user.id,
            Booking.status == "Completed",
            Examination.results_published.is_(True),
        )
        .order_by(Booking.booking_date.desc())
        .all()
    )
    awaiting_publication = (
        Booking.query.join(Examination, Booking.exam_id == Examination.id)
        .filter(
            Booking.student_id == current_user.id,
            Booking.status == "Completed",
            Examination.results_published.is_(False),
        )
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template(
        "student/results.html",
        bookings=completed_bookings,
        awaiting_publication=awaiting_publication,
    )


# Student profile update.
# Allows student to update their name, contact phone number, and roll number.
@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("student")
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        roll_no = request.form.get("roll_no", "").strip()

        if not name:
            flash("Full name is required.", "danger")
            return redirect(url_for("student.profile"))

        current_user.name = name
        current_user.phone = phone or None
        current_user.roll_no = roll_no or None

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("student.profile"))

    total_bookings = Booking.query.filter_by(student_id=current_user.id).count()
    completed_exams = Booking.query.filter_by(student_id=current_user.id, status="Completed").count()
    upcoming_exams = Booking.query.filter_by(student_id=current_user.id, status="Booked").count()

    return render_template(
        "student/profile.html",
        total_bookings=total_bookings,
        completed_exams=completed_exams,
        upcoming_exams=upcoming_exams,
    )
