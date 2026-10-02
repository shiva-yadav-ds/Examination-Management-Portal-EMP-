from sqlalchemy import select

from extensions import db
from models import Booking, Examination, ExamSlot


BOOKING_CLOSED_STATUS = "Booking Closed"
LEGACY_BOOKING_CLOSED_STATUSES = ("Closed", BOOKING_CLOSED_STATUS)
ACTIVE_BOOKING_STATUS = "Booked"


def begin_immediate_write_transaction():
    """Start a transaction that serializes booking lifecycle writes on SQLite.

    Flask-Login loads ``current_user`` before a protected view runs. That read
    starts SQLAlchemy's implicit transaction, so the previous early return
    meant authenticated booking requests never reached ``BEGIN IMMEDIATE``.
    These callers invoke this helper before making changes, making it safe to
    discard that read-only transaction and start the required write one.
    """
    session = db.session()
    bind = db.session.get_bind()
    if bind and bind.dialect.name == "sqlite":
        if session.in_transaction():
            session.rollback()
        session.execute(db.text("BEGIN IMMEDIATE"))


def lock_examination_for_lifecycle_change(exam_id):
    """Return the current exam row locked for a booking lifecycle transition.

    SQLite is serialized by ``BEGIN IMMEDIATE`` above. Other databases use a
    row lock so a close, booking, cancellation, completion, publication, or
    evaluation cannot act on stale exam status at the same time.
    """
    return db.session.execute(
        select(Examination)
        .where(Examination.id == exam_id)
        .with_for_update()
    ).scalar_one_or_none()


def find_student_time_conflict(student_id, new_slot, exclude_booking_id=None):
    query = (
        Booking.query.join(ExamSlot, Booking.slot_id == ExamSlot.id)
        .filter(
            Booking.student_id == student_id,
            Booking.status == ACTIVE_BOOKING_STATUS,
            ExamSlot.exam_date == new_slot.exam_date,
            ExamSlot.start_time < new_slot.end_time,
            ExamSlot.end_time > new_slot.start_time,
        )
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    return query.first()


def has_active_exam_booking(student_id, exam_id, exclude_booking_id=None):
    query = Booking.query.filter_by(
        student_id=student_id,
        exam_id=exam_id,
        status=ACTIVE_BOOKING_STATUS,
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    return query.first()


def reserve_slot_seat(slot):
    if slot.status != "Available" or slot.available_seats <= 0:
        return False
    slot.available_seats -= 1
    if slot.available_seats == 0:
        slot.status = "Full"
    return True


def release_slot_seat(slot):
    slot.available_seats = min(slot.available_seats + 1, slot.capacity)
    if slot.status == "Full" and slot.available_seats > 0:
        slot.status = "Available"


def get_incomplete_bookings_for_exam(exam):
    rubric_ids = {rubric.id for rubric in exam.rubrics}
    if not rubric_ids:
        return list(
            Booking.query.filter(
                Booking.exam_id == exam.id,
                Booking.status.in_(["Booked", "Completed"]),
            ).all()
        )

    candidates = Booking.query.filter(
        Booking.exam_id == exam.id,
        Booking.status.in_(["Booked", "Completed"]),
    ).all()
    incomplete = []
    for booking in candidates:
        scored_ids = {evaluation.rubric_id for evaluation in booking.evaluations}
        if booking.status != "Completed" or not rubric_ids.issubset(scored_ids):
            incomplete.append(booking)
    return incomplete


def get_rubric_total(exam):
    return sum(rubric.max_marks for rubric in exam.rubrics)


def get_evaluation_total(booking):
    return sum(evaluation.marks for evaluation in booking.evaluations)
