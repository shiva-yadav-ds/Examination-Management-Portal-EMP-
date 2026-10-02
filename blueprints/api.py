from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from decorators import role_required
from extensions import db
from models import Booking, Course, Examination, User

api_bp = Blueprint(
    "api",
    __name__,
    url_prefix="/api"
)


# Returns high-level summary counts for courses, exams, examiners, students, and bookings.
# Useful for external dashboards or integration scripts.
@api_bp.route("/stats")
@login_required
def stats():
    data = {
        "courses_count": Course.query.count(),
        "examinations_count": Examination.query.count(),
        "examiners_count": User.query.filter_by(role="examiner").count(),
        "students_count": User.query.filter_by(role="student").count(),
        "bookings_count": Booking.query.count(),
    }
    return jsonify({"success": True, "stats": data})


# Returns a JSON list of all examinations and their statuses.
@api_bp.route("/examinations")
@login_required
def examinations():
    exams = Examination.query.order_by(Examination.created_at.desc()).all()
    results = [
        {
            "id": e.id,
            "name": e.name,
            "course_code": e.course.code,
            "course_name": e.course.name,
            "type": e.type,
            "duration": e.duration,
            "max_marks": e.max_marks,
            "status": e.status,
            "results_published": e.results_published,
        }
        for e in exams
    ]
    return jsonify({"success": True, "examinations": results})


# Returns detailed examination information including its rubric criteria and weightages.
@api_bp.route("/examinations/<int:exam_id>")
@login_required
def examination_detail(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam:
        return jsonify({"success": False, "error": "Examination not found"}), 404

    rubrics_data = [
        {
            "id": r.id,
            "criterion_name": r.criterion_name,
            "max_marks": r.max_marks,
            "weightage": r.weightage,
            "description": r.description,
        }
        for r in exam.rubrics
    ]

    return jsonify({
        "success": True,
        "examination": {
            "id": exam.id,
            "name": exam.name,
            "course_code": exam.course.code,
            "course_name": exam.course.name,
            "type": exam.type,
            "duration": exam.duration,
            "max_marks": exam.max_marks,
            "status": exam.status,
            "results_published": exam.results_published,
            "rubrics": rubrics_data,
        }
    })


# Returns registered student directory. Restricted to admin role only.
@api_bp.route("/students")
@login_required
@role_required("admin")
def students():
    students_list = User.query.filter_by(role="student").order_by(User.name).all()
    results = [
        {
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "roll_no": s.roll_no,
            "phone": s.phone,
            "status": s.status,
        }
        for s in students_list
    ]
    return jsonify({"success": True, "students": results})


# Returns booking records filtered dynamically by the requester's role.
# Admin sees all portal bookings; examiner sees bookings for their own slots; student sees their own bookings.
@api_bp.route("/bookings")
@login_required
def bookings():
    if current_user.role == "admin":
        booking_records = Booking.query.order_by(Booking.booking_date.desc()).all()
    elif current_user.role == "examiner":
        my_slot_ids = [s.id for s in current_user.exam_slots]
        booking_records = Booking.query.filter(Booking.slot_id.in_(my_slot_ids)).all() if my_slot_ids else []
    else:
        booking_records = Booking.query.filter_by(student_id=current_user.id).all()

    results = [
        {
            "id": b.id,
            "student_name": b.student.name,
            "exam_name": b.examination.name,
            "exam_date": b.slot.exam_date.strftime("%Y-%m-%d"),
            "slot_time": f"{b.slot.start_time.strftime('%H:%M')} - {b.slot.end_time.strftime('%H:%M')}",
            "status": b.status,
        }
        for b in booking_records
    ]
    return jsonify({"success": True, "bookings": results})
