# Examination Management Portal (EMP)

EMP ek Flask-based portal hai jahan Admin exam setup karta hai, Examiner slots aur marks manage karta hai, aur Student slot book karke published result dekhta hai.

Is README ka goal sirf project run karna nahi hai. Isse aap sequence mein samajh sakte ho ki browser se request kahan jaati hai, kaunsa Python function chal raha hai, database mein kya change hota hai, aur user ko kaunsa page wapas milta hai.

## 1. Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

Browser mein `http://127.0.0.1:5000` kholo.

First run par `app.py -> create_app()` tables create karta hai aur default admin seed karta hai:

| Account | Email | Password | Status |
|---|---|---|---|
| Admin | `admin@emp.local` | `Admin@123` | active |

## 2. Pehle yeh mental model banao

```text
Browser form/link
    -> Flask route in blueprints/*.py
    -> login and role checks
    -> validation + services.py rules
    -> models.py / SQLite database
    -> commit or rollback
    -> flash message + redirect or rendered Jinja template
```

Example: Student ka `Book Slot` button `templates/student/exam_detail.html` mein form submit karta hai. Request `POST /student/book/<slot_id>` par jaati hai, `blueprints/student.py -> book_slot()` run hota hai, `services.py` seat and conflict checks deta hai, `Booking` row insert hoti hai, `ExamSlot.available_seats` kam hoti hai, aur browser `/student/bookings` par redirect hota hai.

## 3. Project ko kis order mein padhein

Is order mein read karoge to har next file pichhli file se naturally connect hogi:

1. `app.py` - application startup, extension setup, blueprint registration, error pages, session user loading.
2. `config.py` and `extensions.py` - database URL, session cookie configuration, `db` aur `login_manager` ke shared objects.
3. `models.py` - data tables and their relationships. Pehle `User`, phir `Examination`, `ExamSlot`, `Booking`, aur `Evaluation` dekho.
4. `blueprints/auth.py` - registration, login, logout; yahin se authenticated journey start hoti hai.
5. `decorators.py` - har protected route par role checking ka common rule.
6. `utils.py` and `services.py` - time-window decisions, duplicate/conflict guards, locks, seat updates.
7. `blueprints/admin.py` - exam lifecycle control.
8. `blueprints/examiner.py` - slot creation and rubric evaluation.
9. `blueprints/student.py` - discovery, booking, cancellation, result visibility.
10. `templates/base.html`, then matching role template - route jo variables pass karta hai, template unhe screen par render karta hai.
11. `blueprints/api.py` - optional logged-in JSON endpoints; normal UI flow APIs par depend nahi karta.

## 4. Application startup: request aane se pehle kya hota hai

`python app.py` ya production WSGI server `app.py` ko import karta hai.

1. `app = create_app()` Flask object banata hai.
2. `Config` `SECRET_KEY`, SQLite location, and 3-day login cookie settings deta hai.
3. `db.init_app(app)` SQLAlchemy ko Flask app se connect karta hai.
4. `login_manager.init_app(app)` Flask-Login ko connect karta hai.
5. Blueprints register hote hain: `auth_bp`, `admin_bp`, `examiner_bp`, `student_bp`, aur `api_bp`.
6. App context ke andar `db.create_all()` model classes se SQLite tables create karta hai and `seed_admin()` initial admin banata hai if one does not already exist.
7. Har protected request par `load_user()` session cookie se user id leta hai aur `User` database row ko `current_user` banata hai.

## 5. Data connection map

```text
User (admin / examiner / student)
  |-- ExaminerProfile (only examiner; one-to-one)
  |-- ExamSlot (examiner owns created slots)
  `-- Booking (student owns reservations)

Course -> Examination -> Rubric
                     `-> ExamSlot -> Booking -> Evaluation
```

| Model | Important connection | Why it exists |
|---|---|---|
| `User` | Base account for all roles | Login, role, account status, profile data |
| `ExaminerProfile` | `user_id -> User.id` | Examiner-only department/contact fields |
| `Course` | One course has many exams | Academic grouping |
| `Examination` | Belongs to course; has rubrics, slots, bookings | Lifecycle/status is controlled here |
| `Rubric` | Belongs to exam | Each evaluation criterion and maximum marks |
| `ExamSlot` | Belongs to exam and examiner | Date, time, capacity, available seats |
| `Booking` | Joins student, exam, slot | Student appointment and audit status |
| `Evaluation` | Joins booking and rubric | Marks and remarks for one criterion |

## 6. Student registration: exact request sequence

```text
GET /register/student
  -> auth.register_student()
  -> renders templates/auth/register_student.html

POST /register/student
  -> auth.register_student()
  -> validates name/email/password and email uniqueness
  -> generate_password_hash(password)
  -> INSERT User(role="student", status="active")
  -> db.session.commit()
  -> flash success and redirect to /login
```

Student registration ke baad account active hota hai, isliye admin approval required nahi hai. Password plaintext mein store nahi hota; only generated password hash `users.password` column mein save hota hai.

## 7. Examiner registration: Student se kya difference hai

```text
GET /register/examiner
  -> auth.register_examiner()
  -> renders templates/auth/register_examiner.html

POST /register/examiner
  -> validates common fields and unique email
  -> INSERT User(role="examiner", status="pending")
  -> db.session.flush() gets new user.id
  -> INSERT ExaminerProfile(user_id=new_user.id)
  -> commit and redirect to /login

Admin POST /admin/examiners/<id>/approve
  -> admin.approve_examiner()
  -> status becomes "active"
```

Pending examiner login nahi kar sakta because `auth.login()` checks `user.status == "active"` before calling `login_user()`.

## 8. Login se dashboard tak: exact sequence

```text
templates/auth/login.html form
  -> POST /login
  -> auth.login()
  -> User.query.filter_by(email=email).first()
  -> check_password_hash(user.password, entered_password)
  -> status must be active
  -> login_user(user, remember=True)
  -> redirect by role:
       admin     -> /admin/dashboard
       examiner  -> /examiner/dashboard
       student   -> /student/dashboard
```

Dashboard request par pehle `@login_required` session se current user load karta hai. Uske baad `@role_required("student")` ya relevant role decorator check karta hai. Galat role par `403.html` render hota hai; missing page par `404.html`; unhandled database error par `500.html` and transaction rollback.

## 9. Complete examination lifecycle

```text
Admin: Course create
  -> Exam create (Draft)
  -> Rubrics add
  -> Open Slot Creation

Examiner: create slots during allowed window

Admin: Open Booking

Student: browse -> view slots -> book/cancel

Examiner: evaluate every rubric -> Booking becomes Completed

Admin: Close Booking -> Complete Exam -> Publish Results

Student: Results page sees official scorecard
```

### 9.1 Admin setup

| User action | HTTP request | Main function | Database effect |
|---|---|---|---|
| Create course | `POST /admin/courses/create` | `admin.create_course()` | Inserts `Course` |
| Create exam | `POST /admin/exams/create` | `admin.create_exam()` | Inserts `Examination(status="Draft")` |
| Add rubric | `POST /admin/exams/<id>/rubrics/add` | `admin.add_rubric()` | Inserts `Rubric`; sum cannot exceed exam max marks |
| Start slots | `POST /admin/exams/<id>/open-slots` | `admin.open_slot_creation()` | Exam status `Draft -> Slot Creation` |
| Start booking | `POST /admin/exams/<id>/open-booking` | `admin.open_booking()` | Exam status `Slot Creation -> Booking Open` |

Admin starts student booking only if at least one non-cancelled slot exists and booking dates are valid. Status alone enough nahi hai: `utils.can_student_book()` additionally checks current server time is inside the configured booking window.

### 9.2 Examiner slot creation

```text
GET /examiner/slots/create
  -> examiner.create_slot() renders templates/examiner/create_slot.html

POST /examiner/slots/create
  -> decorator verifies active examiner
  -> utils.can_examiner_create_slots(exam) checks status + time window
  -> create_slot() calculates end time from exam.duration
  -> validates date, capacity, and examiner time clash
  -> INSERT ExamSlot(capacity=N, available_seats=N, status="Available")
  -> redirect /examiner/slots
```

### 9.3 Student booking: most important backend flow

```text
GET /student/exams
  -> student.exams() lists Booking Open exams that are inside time window

GET /student/exams/<exam_id>
  -> student.exam_detail() loads rubric + available slots
  -> renders templates/student/exam_detail.html

POST /student/book/<slot_id>
  -> student.book_slot()
  -> services.begin_immediate_write_transaction()
  -> services.lock_examination_for_lifecycle_change()
  -> checks exam status/window, seat count, duplicate exam booking, time overlap
  -> services.reserve_slot_seat(slot)
  -> INSERT Booking(status="Booked") + decrease available_seats
  -> one commit, then redirect /student/bookings
```

The transaction matters: booking row and seat decrement are saved together. If a validation/database problem happens, `rollback()` runs, so a seat is not accidentally lost. A database partial unique index on `Booking` is an extra final guard against two active bookings for the same student and exam.

Cancellation is `POST /student/cancel/<booking_id>` -> `student.cancel_booking()`. It does not delete the booking. It changes status to `Cancelled`, records timestamp, and `release_slot_seat()` restores capacity, preserving history.

### 9.4 Evaluation and result publishing

```text
GET /examiner/evaluate/<booking_id>
  -> examiner.evaluate() renders one field per rubric

POST /examiner/evaluate/<booking_id>
  -> checks examiner owns the slot and marks are within rubric bounds
  -> INSERT or UPDATE Evaluation rows (one per rubric)
  -> Booking.status = "Completed"

POST /admin/exams/<id>/complete
  -> admin.complete_exam() refuses if any active booking lacks full evaluation

POST /admin/exams/<id>/publish-results
  -> admin.publish_results() requires completed exam and rubric total == max marks
  -> Examination.results_published = True

GET /student/results
  -> student.results() returns only completed bookings whose exam is published
```

## 10. Important guards: kaun rule kahan enforce hota hai

| Rule | Main code | Extra protection |
|---|---|---|
| User must be logged in | `@login_required` | Flask-Login session loader |
| User must have correct role/status | `decorators.role_required()` | 403 handler in `app.py` |
| Examiner needs approval | `auth.login()` and `role_required()` | `users.status` field |
| Booking window must be live | `utils.can_student_book()` | Rechecked inside `student.book_slot()` |
| One active booking per exam | `services.has_active_exam_booking()` | Partial unique DB index in `Booking` |
| No overlapping student schedule | `services.find_student_time_conflict()` | Used by booking and admin reschedule |
| Seats never go negative | `services.reserve_slot_seat()` | Lock + transaction + rollback |
| Only slot owner can grade | `examiner.evaluate()` | `abort(403)` |
| Results cannot be partial | `services.get_incomplete_bookings_for_exam()` | Completion/publish checks |

## 11. File to responsibility map

| File | Read it when you want to understand |
|---|---|
| `app.py` | Backend boot and every request's shared setup |
| `blueprints/auth.py` | Register, login, logout, role redirect |
| `blueprints/admin.py` | Course/exam/rubric setup and lifecycle actions |
| `blueprints/examiner.py` | Slot ownership, scheduling, grading |
| `blueprints/student.py` | Booking, cancellation, schedule, scorecard |
| `services.py` | Transactions, locks, seats, booking integrity |
| `utils.py` | Time-window eligibility decisions |
| `models.py` | Every database table and foreign-key relationship |
| `decorators.py` | Role based access control |
| `templates/base.html` | Shared navigation, flash/toast/modal UI |
| `templates/<role>/...` | Screen markup for the matching route |
| `blueprints/api.py` | Logged-in JSON endpoints for integrations |

## 12. Useful documentation

| Document | Use it for |
|---|---|
| `RUN_GUIDE.md` | Fresh setup and troubleshooting |
| `docs/guide/00_OVERVIEW_AND_LIFECYCLE.md` | Browser-based full lifecycle walkthrough |
| `docs/guide/01_ADMIN_GUIDE.md` | Admin controls in detail |
| `docs/guide/02_EXAMINER_GUIDE.md` | Examiner workflow in detail |
| `docs/guide/03_STUDENT_GUIDE.md` | Student workflow in detail |
| `docs/guide/04_BACKEND_CODE_MAP.md` | Feature-to-function lookup |
| `docs/SCHEMA.md` | Table columns and database schema |
| `docs/ROUTES.md` | All HTTP endpoints |

## 13. Agar ek human developer is project ko scratch se banata

Koi experienced developer normally seedha `admin.py` ya HTML se start nahi karta. Pehle business flow aur data decide karta hai, phir foundation banata hai, then one working user journey, and finally advanced features. Ye exact project ko banane ka sensible human order hota:

| Step | Pehle kya create hota | Kyu zaroori hai | Is project mein file / output |
|---|---|---|---|
| 1 | Requirements and role flow | Pehle decide hota hai kaun kya kar sakta hai | Admin, Examiner, Student lifecycle |
| 2 | Python environment and packages | Framework and libraries ke bina app run/test nahi hoga | `requirements.txt` |
| 3 | Settings | Secret key, DB location, cookie lifetime ek jagah chahiye | `config.py` |
| 4 | Shared extension objects | Models aur routes dono ko same DB/session manager use karna hai | `extensions.py` |
| 5 | Database design | Screen banane se pehle decide karna hota hai kya data persist hoga | `models.py` |
| 6 | Application factory | Flask app, configuration, extensions, blueprints ko assemble karta hai | `app.py` |
| 7 | First-run data | System mein login-able admin hona chahiye | `seed.py` |
| 8 | Shared rules | Same security/time/transaction rules copy-paste nahi hone chahiye | `decorators.py`, `utils.py`, `services.py` |
| 9 | Authentication feature | Har role feature se pehle account, login and session kaam kare | `blueprints/auth.py` and `templates/auth/` |
| 10 | Common page shell | Navbar, messages, CSRF form setup aur layout shared rahe | `templates/base.html` |
| 11 | Admin setup features | Exam ecosystem tabhi ban sakta hai jab Course, Exam, Rubric exist kare | `blueprints/admin.py` and `templates/admin/` |
| 12 | Examiner workflow | Admin ke created exam par slots and evaluations bante hain | `blueprints/examiner.py` and `templates/examiner/` |
| 13 | Student workflow | Student sirf prepared, live exam par booking kar sakta hai | `blueprints/student.py` and `templates/student/` |
| 14 | API/integration endpoints | Main UI working hone ke baad JSON access add hota hai | `blueprints/api.py` |
| 15 | Tests and deployment | Important business rules regression se protected rehte hain | `tests/`, `wsgi.py`, `Procfile` |

### 13.1 `models.py` pehle kyu socha jata hai?

Database model app ka permanent data contract hota hai. Is app mein screen par jo bhi important cheez dikhti hai, usko save karne ke liye model chahiye: account ke liye `User`, subject ke liye `Course`, exam ke liye `Examination`, appointment ke liye `ExamSlot`/`Booking`, aur marks ke liye `Evaluation`.

Isliye developer pehle relationship draw karta hai:

```text
Student User + ExamSlot + Examination = Booking
Booking + Rubric = Evaluation
Examiner User + Examination = ExamSlot
Course = many Examinations
```

Uske baad routes likhna easy hota hai because har route ko clear pata hota hai ki kaunsa model read, insert, update, ya delete hoga.

### 13.2 `app.py` itna early kyu hota hai?

`app.py` database business logic nahi rakhta. Yeh conductor hai. Iska kaam Flask app ko run-able banana hai: config load karna, `db` and login manager connect karna, route groups register karna, tables create karna, and errors render karna.

Human developer practical development mein `app.py` ka small skeleton bahut jaldi bana deta hai so that `flask run`/`python app.py` work kare. Models finalize hote hi `app.py` unhe database context deta hai. Isliye `app.py` aur `models.py` initial foundation ke paired files hain, lekin unki responsibilities alag hain:

| File | Simple answer | Isme kya nahi likhna chahiye |
|---|---|---|
| `app.py` | App ko start aur connect karta hai | Course create/booking/evaluation feature logic |
| `models.py` | Data table and relationships define karta hai | Browser request/redirect logic |
| `blueprints/*.py` | Browser request handle karta hai | App-wide startup wiring |
| `services.py` | Reusable, sensitive business rules rakhta hai | HTML rendering |
| `templates/*.html` | User ko screen dikhata hai | Database security decision |

### 13.3 One feature ko human kaise build karta?

Example: **Student slot booking**.

1. Data need identify: Student, Exam, Slot, Booking. Isliye relevant models first.
2. Rule decide: one student cannot book same exam twice; seats cannot become negative; timings overlap nahi honi chahiye.
3. Shared helpers write: `has_active_exam_booking()`, `find_student_time_conflict()`, `reserve_slot_seat()` in `services.py`.
4. Route write: `student.book_slot(slot_id)` in `blueprints/student.py`.
5. Template form/button write: `templates/student/exam_detail.html` posts to that route.
6. Test write: two bookings, full slot, duplicate booking, and cancellation cases.

Yahi pattern har feature par apply hota hai: **data -> rules -> route -> template -> test**.

## 14. Blueprint files: actual structure aur connection

Blueprint ek module hai jo related routes ko group karta hai. Example:

```python
student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/book/<int:slot_id>", methods=["POST"])
@login_required
@role_required("student")
def book_slot(slot_id):
    # request data / current_user read
    # models and services validate
    # db.session.commit() or rollback()
    # flash() + redirect() or render_template()
```

Is code block ko is tarah padho:

1. `Blueprint(..., url_prefix=...)` URL ka common beginning define karta hai.
2. `@route` exact browser URL and HTTP method define karta hai.
3. `@login_required` session ke bina request ko login par bhejta hai.
4. `@role_required(...)` role/status verify karta hai.
5. Function form/query parameters read karta hai, models/services call karta hai.
6. Successful change par `db.session.commit()` permanent DB change karta hai.
7. Failure par `flash()` user message deta hai; route template render ya safe page par redirect karta hai.

### 14.1 Auth blueprint: account and session

File: `blueprints/auth.py`. Is blueprint ka prefix nahi hai, so paths root se directly start hoti hain.

| Browser feature | Request | Backend function | Kya check/change hota hai | Next screen |
|---|---|---|---|---|
| Open site root | `GET /` | `auth.index()` | `current_user` check, role-based route selection | Login or matching dashboard |
| Login page/open login | `GET /login` | `auth.login()` | Login template render | `auth/login.html` |
| Submit login | `POST /login` | `auth.login()` | Email lookup, password hash verify, active status, `login_user()` | Role dashboard |
| Logout | `GET /logout` | `auth.logout()` | `logout_user()` clears session | Login |
| Student registration | `GET/POST /register/student` | `auth.register_student()` | Unique email, password hash, insert active `User` | Login |
| Examiner registration | `GET/POST /register/examiner` | `auth.register_examiner()` | Insert pending `User` + connected `ExaminerProfile` | Login; waits for admin approval |

### 14.2 Admin blueprint: system setup and control center

File: `blueprints/admin.py`, prefix `/admin`. Har route par admin login + active admin role needed hai. Admin features depend on models in this order: Course -> Examination -> Rubric/ExamSlot -> Booking/Evaluation.

| Admin screen/action | Request | Function | Main backend work |
|---|---|---|---|
| Dashboard | `GET /admin/dashboard` | `dashboard()` | Courses, users, slots, bookings counts query karta hai |
| View courses | `GET /admin/courses` | `courses()` | All Course rows render karta hai |
| Create course | `POST /admin/courses/create` | `create_course()` | Required code/name and unique code check; inserts `Course` |
| Edit course | `POST /admin/courses/<id>/edit` | `edit_course()` | Existing course update; duplicate code reject |
| Deactivate course | `POST /admin/courses/<id>/deactivate` | `deactivate_course()` | Deletes history nahi; `Course.status = inactive` |
| View examiners | `GET /admin/examiners` | `examiners()` | Examiner User rows and statuses show karta hai |
| Add examiner directly | `GET/POST /admin/examiners/add` | `add_examiner()` | Active examiner `User` + `ExaminerProfile` create karta hai |
| Approve examiner | `POST /admin/examiners/<id>/approve` | `approve_examiner()` | Pending account ko `active` karta hai |
| Deactivate/reactivate examiner | `POST /admin/examiners/<id>/deactivate` or `/reactivate` | `deactivate_examiner()` / `reactivate_examiner()` | Login access status change karta hai |
| View exams | `GET /admin/exams` | `exams()` | All Examination rows show karta hai |
| Create exam | `POST /admin/exams/create` | `create_exam()` | Course, duration, marks, and timeline validate; inserts Draft `Examination` |
| Manage one exam | `GET /admin/exams/<id>` | `exam_detail()` | Exam, rubrics, slots, bookings and lifecycle controls render karta hai |
| Edit exam | `POST /admin/exams/<id>/edit` | `edit_exam()` | Name/type/duration/marks/windows update with date validation |
| Open slot creation | `POST /admin/exams/<id>/open-slots` | `open_slot_creation()` | Valid dates required; status `Draft -> Slot Creation` |
| Open student booking | `POST /admin/exams/<id>/open-booking` | `open_booking()` | At least one active slot + valid booking window; status -> `Booking Open` |
| Close booking | `POST /admin/exams/<id>/close-booking` | `close_booking()` | Exam lock, booking end set now, status -> `Booking Closed` |
| Complete exam | `POST /admin/exams/<id>/complete` | `complete_exam()` | All active bookings fully evaluated honi chahiye; status -> `Completed` |
| Publish results | `POST /admin/exams/<id>/publish-results` | `publish_results()` | Completed exam, full rubric total, complete scores required; flag true |
| Add rubric | `POST /admin/exams/<id>/rubrics/add` | `add_rubric()` | Inserts criterion only if rubric total max marks se exceed na kare |
| Edit rubric | `POST /admin/exams/<id>/rubrics/<rubric_id>/edit` | `edit_rubric()` | Existing scores ke baad edit blocked; marks total validated |
| Delete rubric | `POST /admin/exams/<id>/rubrics/<rubric_id>/delete` | `delete_rubric()` | Existing Evaluation rows ho to delete blocked; otherwise deletes `Rubric` |
| View/filter slots | `GET /admin/slots` | `slots()` | Exam, examiner, status filters ke saath all slots |
| Change slot examiner | `POST /admin/slots/<id>/change-examiner` | `change_examiner()` | Active examiner and no overlapping faculty slot check |
| View/filter bookings | `GET /admin/bookings` | `bookings()` | All booking records plus available reschedule target slots |
| Reschedule booking | `POST /admin/bookings/<id>/reschedule` | `reschedule_booking()` | Same exam, seat, time conflict checks; old seat release/new seat reserve atomically |
| View/search students | `GET /admin/students` | `students()` | Name/email/roll number filter |
| Global search | `GET /admin/search` | `search()` | Student, examiner, exam, course, booking across query |
| Master results | `GET /admin/results` | `results()` | Completed bookings and rubric score breakdown |
| Admin profile | `GET/POST /admin/profile` | `profile()` | Current admin name/phone update and metrics |

### 14.3 Examiner blueprint: slots and marks

File: `blueprints/examiner.py`, prefix `/examiner`. Examiner only apne assigned/created slots and students ko handle kar sakta hai; ownership mismatch `403` deta hai.

| Examiner screen/action | Request | Function | Main backend work |
|---|---|---|---|
| Dashboard | `GET /examiner/dashboard` | `dashboard()` | Active exams, own slots, pending grading metrics |
| Open exams | `GET /examiner/exams` | `exams()` | Slot-creation visible exams list |
| My slots | `GET /examiner/slots` | `slots()` | `current_user.id` ke own slots list |
| Create slot | `GET/POST /examiner/slots/create` | `create_slot()` | Exam phase/time-window, future date, capacity, examiner clash checks; inserts `ExamSlot` |
| Edit own slot | `POST /examiner/slots/<id>/edit` | `edit_slot()` | Ownership, window, active booking and time clash checks; updates times/capacity |
| Cancel own slot | `POST /examiner/slots/<id>/delete` | `delete_slot()` | Booked students hon to cancellation blocked; otherwise status `Cancelled` |
| Slot students | `GET /examiner/slots/<id>/students` | `slot_students()` | Owner ke slot ki bookings/evaluation state show karta hai |
| Evaluate student | `GET/POST /examiner/evaluate/<booking_id>` | `evaluate()` | Owner check, rubric-wise marks bounds, Evaluation upsert, Booking -> `Completed` |
| Examiner profile | `GET/POST /examiner/profile` | `profile()` | User name plus ExaminerProfile department/contact update |

### 14.4 Student blueprint: discover, reserve, cancel, result

File: `blueprints/student.py`, prefix `/student`. Student ke routes `current_user.id` use karte hain, so user kisi doosre student ki booking/cancel operation nahi kar sakta.

| Student screen/action | Request | Function | Main backend work |
|---|---|---|---|
| Dashboard | `GET /student/dashboard` | `dashboard()` | Upcoming bookings, open exams, published result counts |
| Browse exams | `GET /student/exams` | `exams()` | Booking Open exams, course/type/search filters, server time eligibility |
| Exam detail | `GET /student/exams/<id>` | `exam_detail()` | Exam/rubrics/available slots load; no-cache headers prevent stale booking page |
| Book slot | `POST /student/book/<slot_id>` | `book_slot()` | Exam lock; window, seat, duplicate, time-conflict checks; Booking insert + seat decrement atomically |
| Cancel booking | `POST /student/cancel/<booking_id>` | `cancel_booking()` | Student ownership and deadline check; soft-cancel + seat release |
| Booking history | `GET /student/bookings` | `bookings()` | Current student's Booked/Cancelled/Completed rows |
| Schedule | `GET /student/schedule` | `schedule()` | Current student's active slots sorted chronologically |
| Published results | `GET /student/results` | `results()` | Only Completed bookings whose exam `results_published=True` |
| Student profile | `GET/POST /student/profile` | `profile()` | Current student name, phone, roll number update |

### 14.5 API blueprint: optional JSON access

File: `blueprints/api.py`, prefix `/api`. Yeh normal HTML page flow ka replacement nahi hai; integrations or future frontend ke liye JSON response deta hai.

| Request | Function | Who can use it | Result |
|---|---|---|---|
| `GET /api/stats` | `stats()` | Any logged-in user | Portal count JSON |
| `GET /api/examinations` | `examinations()` | Any logged-in user | Exam list JSON |
| `GET /api/examinations/<id>` | `examination_detail()` | Any logged-in user | Exam and rubric JSON |
| `GET /api/students` | `students()` | Admin | Student directory JSON |
| `GET /api/bookings` | `bookings()` | Logged-in role | Admin all; examiner own slot; student own booking JSON |

## 15. Screen/button se exact code tak kaise jao

Kisi bhi UI button ko trace karne ke liye ye repeatable method use karo:

1. Relevant template kholo, for example `templates/admin/exam_detail.html`.
2. `<form action="...">`, `url_for("...")`, ya link `href` dekho.
3. `url_for("admin.open_booking", exam_id=...)` ka matlab `blueprints/admin.py` mein `def open_booking(...)` search karo.
4. Route decorators ke neeche function padho: form field reads `request.form.get(...)`, database class, service helper, `commit()`, and final redirect.
5. Function mein `render_template("admin/...")` ho to named template next open karo; jo variables render_template mein hain wahi Jinja `{{ variable }}` mein use honge.

Example trace:

```text
Admin clicks "Open Booking"
  templates/admin/exam_detail.html
  -> POST /admin/exams/<exam_id>/open-booking
  -> blueprints/admin.py: open_booking(exam_id)
  -> Examination + ExamSlot read
  -> validates status, active slot, booking dates
  -> exam.status = "Booking Open"; db.session.commit()
  -> redirect back to admin.exam_detail
  -> page re-renders with new lifecycle button/state
```

## 16. Short answers to common confusion

| Question | Answer |
|---|---|
| Login ka backend kahan hai? | `blueprints/auth.py -> login()`, session reload `app.py -> load_user()` |
| Role access check kahan hai? | `decorators.py -> role_required()` plus `@login_required` |
| User data kahan store hai? | `models.py -> User`, actual SQLite database `instance/emp.db` |
| Course/exam/rubric backend kahan hai? | `blueprints/admin.py`; database models `Course`, `Examination`, `Rubric` |
| Slot create kaun karta aur code kahan hai? | Examiner, `blueprints/examiner.py -> create_slot()` |
| Booking ka sensitive logic kahan hai? | `blueprints/student.py -> book_slot()` plus `services.py` |
| Delete actually kahan hota hai? | `admin.delete_rubric()` uses `db.session.delete()`; course and booking are intentionally soft-state changes, history preserve karne ke liye |
| Result student ko kab dikhta hai? | Admin `publish_results()` flag true karta hai, then `student.results()` only that data query karta hai |
| HTML aur Python ka connection? | Template `url_for()`/form request sends URL; matching blueprint function renders/redirects back to template |

## 17. Verification

```bash
python3 -m unittest -v tests.test_emp_workflows
```

The project uses Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Jinja2, Bootstrap 5, and SQLite.
