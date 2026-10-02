from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Index

from extensions import db


# Stores all users - admin, examiner, and student - in a single table.
# Role and status columns drive access control throughout the app.
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    phone = db.Column(db.String(20), nullable=True)
    roll_no = db.Column(db.String(50), nullable=True)
    
    
    
    
# Extra info specific to examiners (department, contact).
# Kept separate so the users table stays clean. One-to-one with User.
class ExaminerProfile(db.Model):
    __tablename__ = "examiner_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )
    department = db.Column(db.String(100))
    contact = db.Column(db.String(20))

    user = db.relationship("User", backref=db.backref("examiner_profile", uselist=False))    
    
    
    
    
# Represents a subject/course (e.g. MLT101).
# One course can have many examinations under it.
class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    examinations = db.relationship(
        "Examination",
        backref="course",
        lazy=True,
        cascade="all, delete-orphan"
    )    
    
    
 
# An exam event under a course (e.g. "MLT Viva").
# Holds timelines for slot creation and student booking, plus the current status.
class Examination(db.Model):
    __tablename__ = "examinations"

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(30), nullable=False)

    duration = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)

    slot_creation_start = db.Column(db.DateTime)
    slot_creation_end = db.Column(db.DateTime)

    booking_start = db.Column(db.DateTime)
    booking_end = db.Column(db.DateTime)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Draft"
    )

    results_published = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )    
    
    
    
# Defines evaluation criteria for an exam (e.g. "Communication - 10 marks").
# Each criterion is scored separately in the Evaluation table.
class Rubric(db.Model):
    __tablename__ = "rubrics"

    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    criterion_name = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    weightage = db.Column(db.Float)
    description = db.Column(db.Text)

    examination = db.relationship(
        "Examination",
        backref="rubrics"
    )
    
    
    
    
    
# A time slot created by an examiner for a specific exam.
# Tracks capacity and available seats; status flips to Full when seats hit 0.
class ExamSlot(db.Model):
    __tablename__ = "exam_slots"

    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    examiner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Available"
    )

    examination = db.relationship(
        "Examination",
        backref="slots"
    )

    examiner = db.relationship(
        "User",
        backref="exam_slots"
    )
    
    
    
    
# Records a student's booking for a slot. Rows are never deleted - cancellation
# sets status to Cancelled. Partial unique index prevents double-booking per exam.
class Booking(db.Model):
    __tablename__ = "bookings"

    __table_args__ = (
        Index(
            "uq_active_booking",
            "student_id",
            "exam_id",
            unique=True,
            sqlite_where=db.text("status = 'Booked'")
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # exam_id is intentional controlled redundancy.
    # It must always equal slot.exam_id (enforced in booking flow, never from user input).
    # Required so the DB-level partial unique index can enforce:
    #   one active booking per student per examination.
    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    slot_id = db.Column(
        db.Integer,
        db.ForeignKey("exam_slots.id"),
        nullable=False
    )

    booking_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Booked"
    )

    cancelled_at = db.Column(db.DateTime, nullable=True)

    rescheduled_from = db.Column(
        db.Integer,
        db.ForeignKey("exam_slots.id"),
        nullable=True
    )

    rescheduled_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship(
        "User",
        backref="bookings"
    )

    examination = db.relationship(
        "Examination",
        backref="bookings"
    )

    slot = db.relationship(
        "ExamSlot",
        foreign_keys=[slot_id],
        backref="bookings"
    )

    original_slot = db.relationship(
        "ExamSlot",
        foreign_keys=[rescheduled_from]
    )
    
    
    
# Stores per-rubric marks and remarks given by an examiner for a booking.
# One row per rubric per booking; unique constraint prevents duplicate scoring.
class Evaluation(db.Model):
    __tablename__ = "evaluations"

    __table_args__ = (
        db.UniqueConstraint(
            "booking_id",
            "rubric_id",
            name="uq_booking_rubric"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id"),
        nullable=False
    )

    rubric_id = db.Column(
        db.Integer,
        db.ForeignKey("rubrics.id"),
        nullable=False
    )

    marks = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text)

    evaluated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    booking = db.relationship(
        "Booking",
        backref="evaluations"
    )

    rubric = db.relationship(
        "Rubric",
        backref="evaluations"
    )
    
    
    
    
            
    
    
    

            
