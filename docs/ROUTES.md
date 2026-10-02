# Routes Reference - EMP

All routes grouped by blueprint. Access levels: **A** = Admin only, **E** = Examiner only, **S** = Student only, **pub** = public.

---

## Auth Blueprint (`blueprints/auth.py`)

| Route | Methods | Access | Purpose |
|---|---|---|---|
| `/` | GET | pub | Landing page to redirect based on role |
| `/login` | GET, POST | pub | Login form + authenticate |
| `/logout` | GET | logged in | Clear session |
| `/register/student` | GET, POST | pub | Student signup to status=active |
| `/register/examiner` | GET, POST | pub | Examiner signup to status=pending |

---

## Admin Blueprint (`blueprints/admin.py`) - prefix `/admin`

| Route | Methods | Access | Purpose |
|---|---|---|---|
| `/admin/dashboard` | GET | A | Counts: courses, exams, examiners, students, pending approvals |
| `/admin/courses` | GET | A | List all courses |
| `/admin/courses/create` | POST | A | Create a course |
| `/admin/courses/<id>/edit` | POST | A | Edit a course |
| `/admin/courses/<id>/deactivate` | POST | A | Soft-deactivate a course |
| `/admin/exams` | GET | A | List all examinations |
| `/admin/exams/create` | POST | A | Create examination + timelines |
| `/admin/exams/<id>` | GET | A | Examination management hub |
| `/admin/exams/<id>/edit` | POST | A | Edit exam details before booking closes |
| `/admin/exams/<id>/open-slots` | POST | A | Draft to Slot Creation |
| `/admin/exams/<id>/open-booking` | POST | A | Slot Creation to Booking Open |
| `/admin/exams/<id>/close-booking` | POST | A | Booking Open to Booking Closed immediately |
| `/admin/exams/<id>/complete` | POST | A | Booking Closed to Completed after complete evaluations |
| `/admin/exams/<id>/publish-results` | POST | A | Publish completed results |
| `/admin/exams/<id>/rubrics/add` | POST | A | Add rubric criterion |
| `/admin/exams/<id>/rubrics/<rubric_id>/edit` | POST | A | Edit a rubric criterion |
| `/admin/exams/<id>/rubrics/<rubric_id>/delete` | POST | A | Delete rubric when no evaluations use it |
| `/admin/examiners` | GET | A | List all examiners + status |
| `/admin/examiners/add` | GET, POST | A | Add an active examiner directly |
| `/admin/examiners/<id>/approve` | POST | A | Set status=active |
| `/admin/examiners/<id>/deactivate` | POST | A | Set status=inactive |
| `/admin/examiners/<id>/reactivate` | POST | A | Set status=active again |
| `/admin/students` | GET | A | List/search students |
| `/admin/slots` | GET | A | All slots (filter by exam/examiner/date) |
| `/admin/slots/<id>/change-examiner` | POST | A | Reassign slot to different examiner |
| `/admin/bookings` | GET | A | All bookings including cancelled |
| `/admin/bookings/<id>/reschedule` | POST | A | Move booking to new slot (same exam) |
| `/admin/search` | GET | A | Search across students/examiners/exams/bookings |
| `/admin/results` | GET | A | Master results view |
| `/admin/profile` | GET, POST | A | Edit admin profile |

---

## Examiner Blueprint (`blueprints/examiner.py`) - prefix `/examiner`

| Route | Methods | Access | Purpose |
|---|---|---|---|
| `/examiner/dashboard` | GET | E | Assigned exams, slot counts, pending evaluations |
| `/examiner/exams` | GET | E | Active examinations |
| `/examiner/slots` | GET | E | Own slots list |
| `/examiner/slots/create` | GET, POST | E | Create slot (blocked outside creation window) |
| `/examiner/slots/<id>/edit` | GET, POST | E | Edit slot (blocked after booking starts or slots booked) |
| `/examiner/slots/<id>/delete` | POST | E | Delete/cancel slot (same conditions as edit) |
| `/examiner/slots/<id>/students` | GET | E | Booked students for a slot |
| `/examiner/evaluate/<booking_id>` | GET, POST | E | Enter marks + remarks per rubric |
| `/examiner/profile` | GET, POST | E | Edit name, department, contact |

---

## Student Blueprint (`blueprints/student.py`) - prefix `/student`

| Route | Methods | Access | Purpose |
|---|---|---|---|
| `/student/dashboard` | GET | S | Available exams, upcoming slots, recent results |
| `/student/exams` | GET | S | Browse + search + filter examinations |
| `/student/exams/<id>` | GET | S | Exam detail + available slots |
| `/student/book/<slot_id>` | POST | S | Book a slot (all checks run here) |
| `/student/cancel/<booking_id>` | POST | S | Cancel booking (before booking_end) |
| `/student/bookings` | GET | S | Full booking history (all statuses) |
| `/student/schedule` | GET | S | Upcoming booked slots sorted by date |
| `/student/results` | GET | S | Published evaluation results + remarks |
| `/student/profile` | GET, POST | S | Edit name, phone, roll_no |

---

## API Blueprint (`blueprints/api.py`) - prefix `/api` *(optional)*

| Route | Methods | Access | Returns |
|---|---|---|---|
| `/api/examinations` | GET | logged in | JSON list of examinations |
| `/api/examinations/<id>` | GET | logged in | Single exam detail |
| `/api/stats` | GET | logged in | JSON portal summary |
| `/api/students` | GET | A | JSON list of students |
| `/api/bookings` | GET | A / E (own) | Bookings list |

---

## HTTP Method Policy

- All state-changing actions (book, cancel, delete, approve, reschedule) to **POST**
- Read-only views to **GET**
- Never use GET for actions that change data (CSRF risk + browser prefetch issues)

---

## Error Pages

| Code | Trigger |
|---|---|
| 403 | Role/ownership check fails (e.g. examiner accessing admin route) |
| 404 | Record not found |
| EMP toast notifications | Validation failures and lifecycle success feedback |
