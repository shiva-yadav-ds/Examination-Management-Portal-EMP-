import os
import tempfile
import unittest
from datetime import date, datetime, time, timedelta


db_fd, db_path = tempfile.mkstemp(prefix="emp-test-", suffix=".db")
os.close(db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app
from extensions import db
from models import Booking, Course, Evaluation, Examination, ExamSlot, Rubric, User
from services import begin_immediate_write_transaction
from werkzeug.security import generate_password_hash


class EmpWorkflowTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(db_path)
        except OSError:
            pass

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.admin = self.user("Admin", "admin@test.local", "admin")
            self.examiner = self.user("Examiner", "examiner@test.local", "examiner")
            self.other_examiner = self.user("Other", "other@test.local", "examiner")
            self.student = self.user("Student", "student@test.local", "student")
            self.other_student = self.user("Other Student", "otherstudent@test.local", "student")
            course = Course(code="TST101", name="Testing")
            db.session.add(course)
            db.session.flush()
            now = datetime.now()
            self.exam = Examination(
                course_id=course.id,
                name="Workflow Viva",
                type="Viva",
                duration=30,
                max_marks=10,
                slot_creation_start=now - timedelta(hours=1),
                slot_creation_end=now + timedelta(days=2),
                booking_start=now - timedelta(hours=1),
                booking_end=now + timedelta(days=2),
                status="Booking Open",
            )
            self.other_exam = Examination(
                course_id=course.id,
                name="Parallel Practical",
                type="Practical",
                duration=30,
                max_marks=10,
                slot_creation_start=now - timedelta(hours=1),
                slot_creation_end=now + timedelta(days=2),
                booking_start=now - timedelta(hours=1),
                booking_end=now + timedelta(days=2),
                status="Booking Open",
            )
            db.session.add_all([self.exam, self.other_exam])
            db.session.flush()
            db.session.add(Rubric(exam_id=self.exam.id, criterion_name="Concept", max_marks=10))
            db.session.add(Rubric(exam_id=self.other_exam.id, criterion_name="Concept", max_marks=10))
            self.slot_a = self.slot(self.exam.id, self.examiner.id, date.today() + timedelta(days=1), time(10, 0))
            self.slot_b = self.slot(self.exam.id, self.examiner.id, date.today() + timedelta(days=1), time(11, 0))
            self.overlap_other_exam_slot = self.slot(
                self.other_exam.id,
                self.other_examiner.id,
                date.today() + timedelta(days=1),
                time(10, 15),
            )
            self.overlap_same_exam_slot = self.slot(
                self.exam.id,
                self.other_examiner.id,
                date.today() + timedelta(days=1),
                time(10, 15),
            )
            self.consecutive_other_exam_slot = self.slot(
                self.other_exam.id,
                self.other_examiner.id,
                date.today() + timedelta(days=1),
                time(10, 30),
            )
            self.admin_id = self.admin.id
            self.examiner_id = self.examiner.id
            self.student_id = self.student.id
            self.exam_id = self.exam.id
            self.other_exam_id = self.other_exam.id
            self.slot_a_id = self.slot_a.id
            self.slot_b_id = self.slot_b.id
            self.overlap_other_exam_slot_id = self.overlap_other_exam_slot.id
            self.overlap_same_exam_slot_id = self.overlap_same_exam_slot.id
            self.consecutive_other_exam_slot_id = self.consecutive_other_exam_slot.id
            db.session.commit()

    def user(self, name, email, role):
        user = User(
            name=name,
            email=email,
            password=generate_password_hash("Password@123"),
            role=role,
            status="active",
        )
        db.session.add(user)
        db.session.flush()
        return user

    def slot(self, exam_id, examiner_id, exam_date, start_time, capacity=2):
        exam = db.session.get(Examination, exam_id)
        start_dt = datetime.combine(exam_date, start_time)
        end_time = (start_dt + timedelta(minutes=exam.duration)).time()
        slot = ExamSlot(
            exam_id=exam_id,
            examiner_id=examiner_id,
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            available_seats=capacity,
            status="Available",
        )
        db.session.add(slot)
        db.session.flush()
        return slot

    def login(self, email, client=None):
        client = client or self.client
        return client.post(
            "/login",
            data={"email": email, "password": "Password@123"},
            follow_redirects=True,
        )

    def test_examiner_sees_booking_open_exam_while_slot_window_active(self):
        self.login("examiner@test.local")
        response = self.client.get("/examiner/exams")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Workflow Viva", response.data)
        self.assertIn(b"Booking Open", response.data)

    def test_lifecycle_controls_use_emp_confirmation_modal(self):
        self.login("admin@test.local")
        response = self.client.get(f"/admin/exams/{self.exam_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-lifecycle-confirm", response.data)
        self.assertIn(b'id="lifecycleConfirmModal"', response.data)
        self.assertIn(b"emp-toast-stack", response.data)
        self.assertNotIn(b"return confirm('Close booking now?", response.data)

    def test_student_booking_rules_duplicate_overlap_cancel_and_consecutive(self):
        self.login("student@test.local")
        response = self.client.post(f"/student/book/{self.slot_a_id}", follow_redirects=True)
        self.assertIn(b"Slot successfully booked", response.data)

        duplicate = self.client.post(f"/student/book/{self.slot_b_id}", follow_redirects=True)
        self.assertIn(b"already have an active booking", duplicate.data)

        overlap = self.client.post(
            f"/student/book/{self.overlap_other_exam_slot_id}",
            follow_redirects=True,
        )
        self.assertIn(b"overlapping this time", overlap.data)

        with self.app.app_context():
            booking = Booking.query.filter_by(student_id=self.student_id, exam_id=self.exam_id).first()
        cancelled = self.client.post(f"/student/cancel/{booking.id}", follow_redirects=True)
        self.assertIn(b"Booking cancelled successfully", cancelled.data)

        consecutive = self.client.post(
            f"/student/book/{self.consecutive_other_exam_slot_id}",
            follow_redirects=True,
        )
        self.assertIn(b"Slot successfully booked", consecutive.data)

    def test_admin_reschedule_rejects_overlap_and_preserves_original(self):
        with self.app.app_context():
            booking = Booking(
                student_id=self.student_id,
                exam_id=self.exam_id,
                slot_id=self.slot_a_id,
                status="Booked",
            )
            blocker = Booking(
                student_id=self.student_id,
                exam_id=self.other_exam_id,
                slot_id=self.overlap_other_exam_slot_id,
                status="Booked",
            )
            db.session.get(ExamSlot, self.slot_a_id).available_seats -= 1
            db.session.get(ExamSlot, self.overlap_other_exam_slot_id).available_seats -= 1
            db.session.add_all([booking, blocker])
            db.session.commit()
            booking_id = booking.id
            original_slot_id = booking.slot_id

        self.login("admin@test.local")
        response = self.client.post(
            f"/admin/bookings/{booking_id}/reschedule",
            data={"new_slot_id": self.overlap_same_exam_slot_id},
            follow_redirects=True,
        )
        self.assertIn(b"overlaps the target slot", response.data)

        with self.app.app_context():
            preserved = db.session.get(Booking, booking_id)
            self.assertEqual(preserved.slot_id, original_slot_id)

    def test_close_booking_immediately_blocks_a_stale_student_booking_form(self):
        student_client = self.app.test_client()
        admin_client = self.app.test_client()
        self.login("student@test.local", student_client)

        # The student loads the page while booking is open, then submits that
        # now-stale form after the administrator closes booking.
        page = student_client.get(f"/student/exams/{self.exam_id}")
        self.assertIn(b"Book Slot", page.data)

        self.login("admin@test.local", admin_client)
        closed = admin_client.post(
            f"/admin/exams/{self.exam_id}/close-booking",
            follow_redirects=True,
        )
        self.assertIn(b"Booking closed.", closed.data)

        stale_submit = student_client.post(
            f"/student/book/{self.slot_a_id}",
            follow_redirects=True,
        )
        self.assertIn(b"Student booking is not currently open", stale_submit.data)

        with self.app.app_context():
            exam = db.session.get(Examination, self.exam_id)
            self.assertEqual(exam.status, "Booking Closed")
            self.assertLessEqual(exam.booking_end, datetime.now())
            self.assertIsNone(
                Booking.query.filter_by(
                    student_id=self.student_id,
                    exam_id=self.exam_id,
                    status="Booked",
                ).first()
            )

    def test_sqlite_lifecycle_write_lock_replaces_auth_read_transaction(self):
        with self.app.app_context():
            # This mirrors Flask-Login loading current_user before a protected
            # view. The lifecycle helper must replace it with BEGIN IMMEDIATE.
            db.session.get(User, self.admin_id)
            self.assertTrue(db.session().in_transaction())
            begin_immediate_write_transaction()
            raw_connection = db.session.connection().connection.driver_connection
            self.assertTrue(raw_connection.in_transaction)
            db.session.rollback()

    def test_evaluate_close_complete_publish_flow(self):
        with self.app.app_context():
            booking = Booking(
                student_id=self.student_id,
                exam_id=self.exam_id,
                slot_id=self.slot_a_id,
                status="Booked",
            )
            slot = db.session.get(ExamSlot, self.slot_a_id)
            slot.available_seats -= 1
            db.session.add(booking)
            db.session.commit()
            booking_id = booking.id
            rubric_id = db.session.get(Examination, self.exam_id).rubrics[0].id

        examiner_client = self.app.test_client()
        admin_client = self.app.test_client()
        student_client = self.app.test_client()

        self.login("examiner@test.local", examiner_client)
        evaluated = examiner_client.post(
            f"/examiner/evaluate/{booking_id}",
            data={f"marks_{rubric_id}": "8", f"remarks_{rubric_id}": "Good work"},
            follow_redirects=True,
        )
        self.assertIn(b"Evaluation submitted successfully", evaluated.data)

        self.login("admin@test.local", admin_client)
        closed = admin_client.post(
            f"/admin/exams/{self.exam_id}/close-booking",
            follow_redirects=True,
        )
        self.assertIn(b"Booking closed.", closed.data)

        completed = admin_client.post(
            f"/admin/exams/{self.exam_id}/complete",
            follow_redirects=True,
        )
        self.assertIn(b"marked as Completed", completed.data)

        published = admin_client.post(
            f"/admin/exams/{self.exam_id}/publish-results",
            follow_redirects=True,
        )
        self.assertIn(b"Results published", published.data)

        self.login("student@test.local", student_client)
        result = student_client.get("/student/results")
        self.assertIn(b"Workflow Viva", result.data)
        self.assertIn(b"8", result.data)

    def test_publish_requires_completed_exam_and_complete_evaluations(self):
        with self.app.app_context():
            booking = Booking(
                student_id=self.student_id,
                exam_id=self.exam_id,
                slot_id=self.slot_a_id,
                status="Booked",
            )
            db.session.add(booking)
            exam = db.session.get(Examination, self.exam_id)
            exam.status = "Booking Closed"
            db.session.commit()
            exam_id = self.exam_id
            booking_id = booking.id
            rubric_id = exam.rubrics[0].id

        self.login("admin@test.local")
        incomplete = self.client.post(f"/admin/exams/{exam_id}/complete", follow_redirects=True)
        self.assertIn(b"still need complete evaluation", incomplete.data)

        with self.app.app_context():
            booking = db.session.get(Booking, booking_id)
            booking.status = "Completed"
            db.session.add(Evaluation(booking_id=booking_id, rubric_id=rubric_id, marks=8))
            db.session.commit()

        completed = self.client.post(f"/admin/exams/{exam_id}/complete", follow_redirects=True)
        self.assertIn(b"marked as Completed", completed.data)

        published = self.client.post(f"/admin/exams/{exam_id}/publish-results", follow_redirects=True)
        self.assertIn(b"Results published", published.data)


if __name__ == "__main__":
    unittest.main()
