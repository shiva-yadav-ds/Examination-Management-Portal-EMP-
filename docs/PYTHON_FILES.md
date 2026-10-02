# EMP Python Files - Complete Documentation

> **Examination Management Portal (EMP)** ke saare Python files ka ek jagah documentation.
> Hinglish mein likha gaya hai - simple, practical, aur seedha point pe.

---

## Table of Contents

| # | File | Kya karta hai (short) |
|---|------|-----------------------|
| 1 | [`app.py`](#apppy) | Flask app factory - sab kuch yahan se shuru hota hai |
| 2 | [`config.py`](#configpy) | App settings - DB URL, secret key, session timeout |
| 3 | [`extensions.py`](#extensionspy) | Shared `db` aur `login_manager` objects |
| 4 | [`decorators.py`](#decoratorspy) | `role_required` - route pe role check karta hai |
| 5 | [`utils.py`](#utilspy) | Slot creation aur booking window open hai ya nahi check karta hai |
| 6 | [`services.py`](#servicespy) | Transactions, lifecycle locking, seats and evaluation helpers |
| 7 | [`models.py`](#modelspy) | Saare DB tables - User, Course, Exam, Slot, Booking, etc. |
| 8 | [`seed.py`](#seedpy) | Pehli baar default admin account banata hai |
| 9 | [`manage_admin.py`](#manage_adminpy) | CLI tool - terminal se admin add/reset/list |
| 10 | [`wsgi.py`](#wsgipy) | Production WSGI entry point |
| 11 | [`blueprints/__init__.py`](#blueprintsinitpy) | Blueprints package init file |
| 12 | [`blueprints/auth.py`](#blueprintsauthpy) | Login, logout, register student/examiner |
| 13 | [`blueprints/admin.py`](#blueprintsadminpy) | Admin ke saare routes |
| 14 | [`blueprints/examiner.py`](#blueprintsexaminerpy) | Examiner routes - slots, evaluate, profile |
| 15 | [`blueprints/student.py`](#blueprintsstudentpy) | Student routes - book, cancel, results |
| 16 | [`blueprints/api.py`](#blueprintsapipy) | JSON endpoints |

---

## `app.py`

**Kya karta hai**: Poori Flask app yahaan se banti hai. Blueprint register karta hai, DB tables banata hai, error pages set karta hai.

**Path**: `app.py`

**Main Features / Functions**:

- `create_app()` - Flask app factory function. Ye function:
  - `Config` se settings load karta hai
  - `db` aur `login_manager` ko app se attach karta hai (`init_app`)
  - Saare 5 blueprints register karta hai (`auth`, `admin`, `examiner`, `student`, `api`)
  - `db.create_all()` chalata hai - agar tables nahi hain toh banata hai
  - `seed_admin()` call karta hai - pehli baar default admin insert karne ke liye
  - 403, 404, 500 error handlers define karta hai custom HTML pages ke saath

- `load_user(user_id)` - Flask-Login ka user loader callback. Session cookie mein stored `user_id` se `User` object DB se fetch karta hai. Ye function `@login_manager.user_loader` decorator ke saath register hota hai.

- `forbidden_error(error)` - 403 pe `403.html` render karta hai
- `not_found_error(error)` - 404 pe `404.html` render karta hai
- `internal_error(error)` - 500 pe `db.session.rollback()` karta hai (broken transaction clear karne ke liye), phir `500.html` render karta hai

- `app = create_app()` - Module level pe app instance banata hai, Gunicorn/WSGI servers ke liye

**Kaun use karta hai / Kisse connect hai**:
- `config.py` se `Config` import karta hai
- `extensions.py` se `db`, `login_manager` import karta hai
- `seed.py` se `seed_admin()` call karta hai
- Saare blueprint files (`auth`, `admin`, `examiner`, `student`, `api`) yahan register hote hain
- `models.py` ke saare models yahan `db.create_all()` ke liye import hote hain
- `manage_admin.py` bhi `create_app()` ko import karta hai

**Code mein kahan dhundhu**: Lines 9-65 (`create_app`), Line 70-74 (`load_user`), Line 78 (module-level app instance)

---

## `config.py`

**Kya karta hai**: App ki saari settings ek jagah rakhta hai. `.env` file se environment variables load karta hai.

**Path**: `config.py`

**Main Features / Functions**:

- `load_dotenv()` - `.env` file se variables load karta hai (project root mein `.env` hona chahiye production ke liye)

- `Config` class - Ek plain Python class jisme saari app settings hain:
  - `SECRET_KEY` - Session cookies aur CSRF tokens sign karne ke liye. Default hai `"dev-secret-key-change-later"` - production mein `.env` se override karo
  - `SQLALCHEMY_DATABASE_URI` - DB connection string. Default: `sqlite:///emp.db` (project ke `instance/` folder mein). `DATABASE_URL` env variable se override hota hai
  - `SQLALCHEMY_TRACK_MODIFICATIONS = False` - SQLAlchemy ka unnecessary overhead band karta hai
  - `WTF_CSRF_ENABLED = True` - Forms pe CSRF protection on hai
  - `PERMANENT_SESSION_LIFETIME = timedelta(days=3)` - Login session 3 din tak rehta hai
  - `REMEMBER_COOKIE_DURATION = timedelta(days=3)` - "Remember me" cookie bhi 3 din
  - `SESSION_COOKIE_HTTPONLY = True` - JavaScript cookie access nahi kar sakta (XSS protection)
  - `SESSION_COOKIE_SAMESITE = "Lax"` - CSRF protection ke liye cross-site cookie restrict karta hai
  - `DEBUG = True` - Development mode on (production mein `False` karo)

**Kaun use karta hai / Kisse connect hai**:
- `app.py` mein `app.config.from_object(Config)` se use hota hai
- Koi bhi doosra file directly import nahi karta - sirf `app.py` ke through kaam karta hai

**Code mein kahan dhundhu**: Line 12-33 (`Config` class definition)

---

## `extensions.py`

**Kya karta hai**: `SQLAlchemy` aur `LoginManager` ke shared instances yahan define hote hain - circular import problem se bachne ke liye.

**Path**: `extensions.py`

**Main Features / Functions**:

- `db = SQLAlchemy()` - Database ORM instance. Poori app mein ek hi `db` object use hota hai. Models, blueprints, seed - sab yahan se import karte hain.
- `login_manager = LoginManager()` - Flask-Login ka instance. User sessions manage karta hai.

**Kyun alag file mein hai?**
Agar `db` directly `app.py` mein banate toh models `app.py` import karte, `app.py` models import karta - circular import error aata. Is alag file ki wajah se `models.py`, `blueprints/*.py`, `seed.py` - sab `extensions.py` se `db` import karte hain bina `app.py` ko touch kiye.

**Kaun use karta hai / Kisse connect hai**:
- `app.py` - `db.init_app(app)` aur `login_manager.init_app(app)` ke liye import karta hai
- `models.py` - `db` use karta hai table definitions ke liye
- `blueprints/auth.py`, `admin.py`, `examiner.py`, `student.py`, `api.py` - `db` se queries karte hain
- `seed.py` aur `manage_admin.py` - `db.session.add/commit` ke liye

**Code mein kahan dhundhu**: Lines 1-7 (poora file, sirf 7 lines hai)

---

## `decorators.py`

**Kya karta hai**: `role_required` decorator define karta hai jo route pe role-based access control (RBAC) enforce karta hai.

**Path**: `decorators.py`

**Main Features / Functions**:

- `role_required(*roles)` - Ye ek decorator factory hai. Isko use karte hain route ke upar:
  ```python
  @role_required("admin")          # sirf admin
  @role_required("admin", "examiner")  # admin ya examiner dono
  ```
  Andar kya hota hai:
  1. `current_user.is_authenticated` check karta hai - agar login nahi toh `abort(401)` (Unauthorized)
  2. `current_user.role` check karta hai allowed roles mein se - nahi mila toh `abort(403)` (Forbidden)
  3. Sab theek hai toh actual view function call hota hai

- `@wraps(view_function)` - Original function ka naam aur docstring preserve karta hai (Flask routing ke liye zaruri)

**Kaun use karta hai / Kisse connect hai**:
- `blueprints/admin.py` - har route pe `@role_required("admin")` laga hai
- `blueprints/examiner.py` - `@role_required("examiner")`
- `blueprints/student.py` - `@role_required("student")`
- `blueprints/api.py` - `@role_required("admin")` specific endpoints pe

**Code mein kahan dhundhu**: Lines 10-26 (`role_required` function)

---

## `utils.py`

**Kya karta hai**: Do utility functions - exam ka slot creation window aur booking window abhi open hai ya band, ye check karta hai.

**Path**: `utils.py`

**Main Features / Functions**:

- `is_slot_creation_open(exam)` - Diya hua `Examination` object ka `slot_creation_start` aur `slot_creation_end` check karta hai. Agar current server time us window ke andar hai toh `True` return karta hai, warna `False`. Agar dates set hi nahi hain toh bhi `False`.

- `is_booking_open(exam)` - Same logic, lekin `booking_start` aur `booking_end` ke liye. Students sirf tab slot book kar sakte hain jab ye `True` ho.

**Kaun use karta hai / Kisse connect hai**:
- `blueprints/examiner.py` - `create_slot()` mein `is_slot_creation_open()` call karta hai; `edit_slot()` mein `is_booking_open()` call karta hai
- `blueprints/student.py` - `exam_detail()` aur `book_slot()` mein `is_booking_open()` use hota hai

**Code mein kahan dhundhu**: Lines 6-12 (`is_slot_creation_open`), Lines 17-23 (`is_booking_open`)

---

## `services.py`

**Kya karta hai**: Booking aur examination lifecycle ke shared database helpers rakhta hai. Is file ka purpose UI se independent, server-side consistency maintain karna hai.

**Main helpers**:

- `begin_immediate_write_transaction()` - SQLite par authenticated request ke existing read transaction ko replace karke `BEGIN IMMEDIATE` start karta hai. Isse booking lifecycle writes serialized rehte hain.
- `lock_examination_for_lifecycle_change(exam_id)` - Supported databases par exam row ko `FOR UPDATE` se lock karta hai; SQLite par immediate transaction same protection deta hai.
- `reserve_slot_seat()` / `release_slot_seat()` - Seat count aur `Available` / `Full` slot status ko saath update karte hain.
- `get_incomplete_bookings_for_exam()` - Completion aur publication se pehle incomplete evaluations identify karta hai.

**Kaun use karta hai**: `admin.py`, `student.py`, aur `examiner.py`. Close booking, booking, cancellation, evaluation, completion, aur publication same lifecycle protection use karte hain.

---

## `models.py`

**Kya karta hai**: EMP ke saare database tables SQLAlchemy ORM models ke roop mein yahan define hain. Ek model = ek DB table.

**Path**: `models.py`

**Main Features / Functions**:

### `User` (Line 11)
Poori app ka single users table. Admin, examiner, student - teeno isi table mein hain. `role` column se distinguish hota hai.

- **Columns**: `id`, `name`, `email` (unique), `password` (hashed), `role` (`admin`/`examiner`/`student`), `status` (`active`/`pending`/`inactive`), `created_at`, `phone`, `roll_no`
- **Flask-Login integration**: `UserMixin` inherit karta hai - `is_authenticated`, `is_active`, etc. automatically milte hain
- `roll_no` aur `phone` sirf students ke liye relevant hain, nullable hain

### `ExaminerProfile` (Line 29)
Examiner ka extra data - department aur contact. `User` ke saath one-to-one relation.

- **Columns**: `id`, `user_id` (FK → users.id, unique), `department`, `contact`
- **Relationship**: `user` → `User` object milta hai. `User` pe `examiner_profile` backref se profile milta hai
- Admin-created examiners aur self-registered dono ke liye row banta hai

### `Course` (Line 49)
Subject/course represent karta hai (jaise MLT101, CS301).

- **Columns**: `id`, `code` (unique), `name`, `description`, `status` (`active`/`inactive`), `created_at`
- **Relationship**: `examinations` → ek course ke andar multiple exams ho sakte hain (`cascade="all, delete-orphan"`)

### `Examination` (Line 70)
Ek specific exam event (jaise "MLT Viva Sem 4"). Course ke under hota hai.

- **Columns**: `id`, `course_id` (FK), `name`, `type` (Viva/Practical/Project Demo/Assessment), `duration` (minutes mein), `max_marks`, `slot_creation_start`, `slot_creation_end`, `booking_start`, `booking_end`, `status` (Draft → Slot Creation → Booking Open → Booking Closed → Completed), `results_published` (boolean), `created_at`
- Status workflow: Admin manually ek state se doosre state mein move karta hai

### `Rubric` (Line 114)
Exam ke grading criteria (jaise "Communication Skills - 10 marks", "Technical Knowledge - 20 marks").

- **Columns**: `id`, `exam_id` (FK), `criterion_name`, `max_marks`, `weightage` (optional float), `description`
- **Relationship**: `examination` → parent exam. Evaluations yahan ke `rubric_id` ke through link hoti hain

### `ExamSlot` (Line 141)
Examiner ka ek time slot - kab, kitne students, kitni seats available.

- **Columns**: `id`, `exam_id` (FK), `examiner_id` (FK → users.id), `exam_date`, `start_time`, `end_time`, `capacity`, `available_seats`, `status` (`Available`/`Full`/`Cancelled`)
- **Relationships**: `examination` → exam object; `examiner` → User object
- `end_time` examiner create karte waqt manually nahi deta - `start_time + exam.duration` se auto-calculate hota hai

### `Booking` (Line 186)
Student ka slot reservation record. Kabhi delete nahi hota - cancellation = status "Cancelled".

- **Columns**: `id`, `student_id` (FK), `exam_id` (controlled redundancy - slot ke exam_id ke barabar hona chahiye), `slot_id` (FK), `booking_date`, `status` (`Booked`/`Cancelled`/`Completed`), `cancelled_at`, `rescheduled_from` (FK → exam_slots.id, nullable), `rescheduled_at`
- **Partial Unique Index** `uq_active_booking`: Ek student ek exam mein sirf ek active (`status='Booked'`) booking rakh sakta hai - DB level pe enforce hota hai
- **Relationships**: `student`, `examination`, `slot`, `original_slot` (reschedule history ke liye)

### `Evaluation` (Line 269)
Examiner ka per-rubric score - ek booking ke ek rubric ke liye ek row.

- **Columns**: `id`, `booking_id` (FK), `rubric_id` (FK), `marks` (float), `remarks` (optional text), `evaluated_at`
- **Unique Constraint** `uq_booking_rubric`: Ek booking ke ek rubric ka sirf ek evaluation row - duplicate prevent karta hai
- **Relationships**: `booking`, `rubric`

**Kaun use karta hai / Kisse connect hai**:
- `app.py` - `db.create_all()` ke liye import karta hai
- Saare blueprint files - queries aur data insert/update ke liye
- `seed.py` aur `manage_admin.py` - `User` model use karte hain
- `blueprints/api.py` - JSON responses ke liye models query karta hai

**Code mein kahan dhundhu**: User (L11), ExaminerProfile (L29), Course (L49), Examination (L70), Rubric (L114), ExamSlot (L141), Booking (L186), Evaluation (L269)

---

## `seed.py`

**Kya karta hai**: App pehli baar chalti hai toh default admin account create karta hai. Agar admin already hai toh kuch nahi karta.

**Path**: `seed.py`

**Main Features / Functions**:

- `seed_admin()` - Pehle check karta hai koi bhi `role="admin"` user DB mein hai ya nahi:
  - Agar hai → function return ho jaata hai (kuch nahi karta, safe hai)
  - Agar nahi hai → ek default admin create karta hai:
    - **Email**: `admin@emp.local`
    - **Password**: `Admin@123` (Werkzeug se hash hota hai)
    - **Name**: `System Admin`
    - **Status**: `active`

**Kaun use karta hai / Kisse connect hai**:
- `app.py` mein `create_app()` ke andar `with app.app_context()` block mein call hota hai - har app start pe
- `extensions.py` se `db` import karta hai
- `models.py` se `User` import karta hai

**Code mein kahan dhundhu**: Lines 9-24 (`seed_admin` function)

> **Note**: Production mein deploy karne ke baad pehla kaam `admin@emp.local` ka password change karna chahiye ya `manage_admin.py` se naaya admin add karna chahiye.

---

## `manage_admin.py`

**Kya karta hai**: Terminal se admin accounts manage karne ka CLI tool. Web UI ke bina directly DB mein admin add, list, ya password reset kar sakte ho.

**Path**: `manage_admin.py`

**Main Features / Functions**:

- `list_admins()` - Saare admin users ki formatted list print karta hai (ID, Name, Email, Status)
  ```bash
  python manage_admin.py list
  ```

- `add_admin(name, email, password)` - Naaya admin account banata hai:
  - Email uniqueness check karta hai pehle
  - Password hash karke store karta hai
  - Status directly `active` set hota hai (pending nahi)
  ```bash
  python manage_admin.py add "Ravi Sharma" ravi@college.edu "MyPass@123"
  ```

- `reset_password(email, new_password)` - Existing user ka password reset karta hai (koi bhi role, admin restrict nahi)
  ```bash
  python manage_admin.py reset-password ravi@college.edu "NewPass@456"
  ```

- `__main__` block - `sys.argv` parse karta hai aur sahi function call karta hai. Wrong command pe docstring print karta hai.

**Kaun use karta hai / Kisse connect hai**:
- Ye file standalone script hai - seedha terminal se chalate hain
- `app.py` ka `create_app()` use karta hai app context ke liye
- `extensions.py` se `db` aur `models.py` se `User` import karta hai
- Koi bhi doosra Python file isko import nahi karta

**Code mein kahan dhundhu**: `list_admins` (L19), `add_admin` (L32), `reset_password` (L54), CLI parser (L69-91)

---

## `wsgi.py`

**Kya karta hai**: Production server entry point. Gunicorn, Render, Railway, aur Vercel configuration isi module se Flask application ko load kar sakte hain.

**Path**: `wsgi.py`

**Main implementation**:

- `create_app` ko `app.py` se import karta hai.
- `app = create_app()` bana kar WSGI servers ke liye export karta hai.
- Local fallback ke liye direct execution par `app.run()` bhi available hai.

**Kaun use karta hai**:
- `Procfile`: `gunicorn wsgi:app`
- `vercel.json`: `wsgi.py` ko Python build aur route destination ke roop mein reference karta hai.

---

## `blueprints/__init__.py`

**Kya karta hai**: `blueprints/` folder ko Python package banata hai. Practically khaali file hai - sirf ek comment line hai.

**Path**: `blueprints/__init__.py`

**Main Features / Functions**:
- Koi functions/classes nahi hain
- `# blueprints package` comment sirf documentation ke liye hai
- Iska hona Python ko batata hai ki `blueprints/` ek package hai, isse `from blueprints.auth import auth_bp` jaise imports kaam karte hain

**Kaun use karta hai / Kisse connect hai**:
- `app.py` mein `from blueprints.auth import auth_bp` waale imports tab kaam karte hain jab ye file exist karti hai

**Code mein kahan dhundhu**: Line 1-2 (poora file)

---

## `blueprints/auth.py`

**Kya karta hai**: Login, logout, student registration, aur examiner registration handle karta hai. Ye publicly accessible routes hain (bina login ke bhi accessible).

**Path**: `blueprints/auth.py`

**Main Features / Functions**:

- `auth_bp = Blueprint("auth", __name__)` - Blueprint object, koi `url_prefix` nahi (root level routes)

- `index()` - Route: `GET /`
  Logged-in user ko uske role ke dashboard pe redirect karta hai. Naya visitor → `/login` pe jaata hai.

- `login()` - Route: `GET /login`, `POST /login`
  - Email aur password validate karta hai (`check_password_hash`)
  - `status != "active"` wale users block hote hain (pending examiners login nahi kar sakte)
  - Successful login pe `session.permanent = True` aur `login_user(user, remember=True)` - 3-day session set hota hai
  - Role ke hisaab se dashboard pe redirect: admin → `/admin/dashboard`, examiner → `/examiner/dashboard`, student → `/student/dashboard`

- `logout()` - Route: `GET /logout`
  `logout_user()` call karta hai (session clear), phir `/login` pe redirect

- `register_student()` - Route: `GET /register/student`, `POST /register/student`
  - Name, email, password, phone, roll_no leta hai
  - Email uniqueness check karta hai
  - `status="active"` ke saath seedha `User` create karta hai - admin approval nahi chahiye
  - Success pe `/login` redirect

- `register_examiner()` - Route: `GET /register/examiner`, `POST /register/examiner`
  - Name, email, password, department, contact leta hai
  - `status="pending"` ke saath `User` create karta hai - **admin approval zaroori hai login ke liye**
  - `db.session.flush()` karta hai user ID pane ke liye, phir `ExaminerProfile` row banata hai
  - Success pe info flash karta hai ki "pending approval"

**Kaun use karta hai / Kisse connect hai**:
- `app.py` mein `auth_bp` register hota hai
- `extensions.py` se `db` import karta hai
- `models.py` se `User`, `ExaminerProfile` import karta hai
- `blueprints/admin.py` - `approve_examiner` route is file mein set hue `pending` status ko `active` banata hai
- Templates: `auth/login.html`, `auth/register_student.html`, `auth/register_examiner.html`

**Code mein kahan dhundhu**: `index` (L22), `login` (L36), `logout` (L70), `register_student` (L78), `register_examiner` (L117)

---

## `blueprints/admin.py`

**Kya karta hai**: Admin portal ke saare routes - courses, examiners, exams, rubrics, slots, bookings, students, search, aur results manage karta hai. Sabse bada blueprint file hai (915 lines, 20+ routes).

**Path**: `blueprints/admin.py`

**Main Features / Functions**:

`admin_bp = Blueprint("admin", __name__, url_prefix="/admin")` - Saare routes `/admin/` se shuru hote hain.

Har route pe `@login_required` aur `@role_required("admin")` laga hota hai.

### Dashboard
- `dashboard()` - `GET /admin/dashboard` - System metrics fetch karta hai: course count, exam count, examiner count, student count, pending examiners, slot count, booking count. `admin/dashboard.html` render karta hai.

### Course Management
- `courses()` - `GET /admin/courses` - Saare courses list karta hai
- `create_course()` - `POST /admin/courses/create` - Naaya course banata hai, code uniqueness check karta hai
- `edit_course(course_id)` - `POST /admin/courses/<id>/edit` - Course name/code/description update karta hai, duplicate code check karta hai
- `deactivate_course(course_id)` - `POST /admin/courses/<id>/deactivate` - Course ko `inactive` karta hai (soft delete, historical data safe rehta hai)

### Examiner Management
- `examiners()` - `GET /admin/examiners` - Saare examiners, unka status aur department
- `add_examiner()` - `GET/POST /admin/examiners/add` - Admin directly active examiner add karta hai (self-register wala pending hota hai, ye seedha active)
- `approve_examiner(examiner_id)` - `POST /admin/examiners/<id>/approve` - Pending examiner ko `active` karta hai
- `deactivate_examiner(examiner_id)` - `POST /admin/examiners/<id>/deactivate` - Active examiner band karta hai
- `reactivate_examiner(examiner_id)` - `POST /admin/examiners/<id>/reactivate` - Inactive examiner wapas active karta hai

### Examination Management
- `EXAM_TYPES = ["Viva", "Practical", "Project Demo", "Assessment"]` - Allowed exam types constant
- `exams()` - `GET /admin/exams` - Saare exams list, active courses bhi deta hai create form ke liye
- `create_exam()` - `POST /admin/exams/create` - Naaya exam banata hai `Draft` status mein. Duration, max_marks validate karta hai. Datetime strings parse karta hai aur timeline order check karta hai (start before end).
- `exam_detail(exam_id)` - `GET /admin/exams/<id>` - Ek exam ka detail page - timeline, rubrics, status buttons
- `edit_exam(exam_id)` - `POST /admin/exams/<id>/edit` - Sirf `Draft` status mein edit ho sakta hai
- `open_slot_creation(exam_id)` - `POST /admin/exams/<id>/open-slots` - Draft → Slot Creation (examiner slots add kar sakte hain)
- `open_booking(exam_id)` - `POST /admin/exams/<id>/open-booking` - Slot Creation → Booking Open (students book kar sakte hain). Slots exist karna zaroori hai.
- `close_booking(exam_id)` - `POST /admin/exams/<id>/close-booking` - Booking Open → Booking Closed; booking end immediately current server time par set hota hai
- `complete_exam(exam_id)` - `POST /admin/exams/<id>/complete` - Booking Closed → Completed
- `publish_results(exam_id)` - `POST /admin/exams/<id>/publish-results` - `results_published = True` set karta hai - students apne scores dekh sakte hain

### Rubric Management
- `add_rubric(exam_id)` - `POST /admin/exams/<id>/rubrics/add` - Grading criterion add karta hai. Rubric max_marks ka sum exam max_marks se zyada nahi hona chahiye.
- `delete_rubric(exam_id, rubric_id)` - `POST /admin/exams/<id>/rubrics/<rubric_id>/delete` - Rubric delete karta hai. Block karta hai agar evaluations already ho chuki hain.

### Slot Management
- `slots()` - `GET /admin/slots` - Saare slots with filters (exam_id, examiner_id, status)
- `change_examiner(slot_id)` - `POST /admin/slots/<id>/change-examiner` - Slot ka examiner badalta hai. Time clash detection karta hai new examiner ke liye.

### Booking Management
- `bookings()` - `GET /admin/bookings` - Saari bookings, exam/status filter ke saath. Rescheduling ke liye available slots bhi deta hai.
- `reschedule_booking(booking_id)` - `POST /admin/bookings/<id>/reschedule` - Student ki booking ek slot se doosre slot pe move karta hai. Atomically old seat free, new seat book, `rescheduled_from` record karta hai.

### Student / Search / Results
- `students()` - `GET /admin/students` - Student directory with live search (name/email/roll_no)
- `search()` - `GET /admin/search` - Global search across students, examiners, exams, courses, bookings ek saath
- `results()` - `GET /admin/results` - Master gradebook - kisi bhi exam ke completed evaluations dikhaata hai

**Kaun use karta hai / Kisse connect hai**:
- `app.py` mein register hota hai
- `decorators.py` se `role_required` import karta hai
- `extensions.py` se `db`
- `models.py` se saare models (Booking, Course, Evaluation, Examination, ExaminerProfile, ExamSlot, Rubric, User)
- Templates: `admin/` folder ke saare HTML files

**Code mein kahan dhundhu**: Dashboard (L38), Courses (L69-147), Examiners (L150-255), Exams (L262-530), Rubrics (L533-610), Slots (L613-693), Bookings (L696-793), Students (L796-815), Search (L820-880), Results (L883-915)

---

## `blueprints/examiner.py`

**Kya karta hai**: Examiner portal ke saare routes - dashboard, slot create/edit/cancel, students list, evaluate, aur profile.

**Path**: `blueprints/examiner.py`

**Main Features / Functions**:

`examiner_bp = Blueprint("examiner", __name__, url_prefix="/examiner")` - Saare routes `/examiner/` se shuru hote hain.

Har route pe `@login_required` aur `@role_required("examiner")` laga hota hai.

- `dashboard()` - `GET /examiner/dashboard`
  Examiner ka overview:
  - Kitne exams Slot Creation phase mein hain
  - Examiner ke khud ke active slots count
  - Un slots mein booked candidates count
  - **Pending evaluations** - woh students jinki exam date aa gayi hai (ya kal thi) lekin abhi tak grade nahi diya. Ye list dashboard pe seedha dikhti hai.

- `exams()` - `GET /examiner/exams`
  Sirf woh exams dikhata hai jo `status="Slot Creation"` mein hain - examiner yahan se slot create karne ka option dekh sakta hai.

- `slots()` - `GET /examiner/slots`
  Examiner ke khud ke saare non-cancelled slots, date/time ke order mein.

- `create_slot()` - `GET/POST /examiner/slots/create`
  Slot creation form aur handler:
  - `is_slot_creation_open(exam)` check karta hai - window band hai toh error
  - Past date nahi ho sakti
  - Capacity kam se kam 1 honi chahiye
  - `end_time = start_time + exam.duration` auto-calculate hota hai
  - **Clash detection**: Agar examiner ka same date pe koi overlapping slot hai toh block karta hai

- `edit_slot(slot_id)` - `POST /examiner/slots/<id>/edit`
  - Sirf apna slot edit kar sakta hai (ownership check, warna 403)
  - Block karta hai agar active bookings hain ya booking window open hai
  - Clash detection phir se karta hai (current slot ko exclude karke)

- `delete_slot(slot_id)` - `POST /examiner/slots/<id>/delete`
  - Ownership check
  - Active bookings hain toh block (students hai toh cancel nahi kar sakte)
  - Soft delete - `slot.status = "Cancelled"`

- `slot_students(slot_id)` - `GET /examiner/slots/<id>/students`
  - Ownership check (doosre examiner ki student list nahi dekh sakta)
  - Booked + Completed bookings list
  - `can_evaluate = slot.exam_date <= date.today()` - exam date aane ke baad hi evaluate button enable hota hai

- `evaluate(booking_id)` - `GET/POST /examiner/evaluate/<id>`
  Sabse complex function. Student ko grade karta hai:
  - Ownership check (slot owner hi evaluate kar sakta hai)
  - Har rubric ke liye marks validate karta hai (0 ≤ marks ≤ max_marks)
  - **Upsert logic**: Agar evaluation already hai toh update, nahi hai toh insert
  - Success pe `booking.status = "Completed"` set karta hai

- `profile()` - `GET/POST /examiner/profile`
  Examiner apna naam, department, contact update kar sakta hai. Agar `ExaminerProfile` row nahi hai (purane users ke liye edge case) toh naaya create karta hai.

**Kaun use karta hai / Kisse connect hai**:
- `app.py` mein register hota hai
- `decorators.py` se `role_required`
- `extensions.py` se `db`
- `models.py` se Booking, Evaluation, Examination, ExaminerProfile, ExamSlot, Rubric, User
- `utils.py` se `is_booking_open`, `is_slot_creation_open`
- Templates: `examiner/` folder

**Code mein kahan dhundhu**: `dashboard` (L29), `exams` (L74), `slots` (L88), `create_slot` (L106), `edit_slot` (L190), `delete_slot` (L259), `slot_students` (L288), `evaluate` (L319), `profile` (L394)

---

## `blueprints/student.py`

**Kya karta hai**: Student portal ke saare routes - dashboard, exams browse, book slot, cancel booking, schedule, results, aur profile.

**Path**: `blueprints/student.py`

**Main Features / Functions**:

`student_bp = Blueprint("student", __name__, url_prefix="/student")` - Saare routes `/student/` se shuru hote hain.

Har route pe `@login_required` aur `@role_required("student")` laga hota hai.

- `dashboard()` - `GET /student/dashboard`
  Student ka home page:
  - Upcoming confirmed bookings (aaj se aage, status="Booked") chronologically
  - Open exams count (Booking Open status mein)
  - Total bookings count (kisi bhi status)
  - Published results count (completed + results_published=True)

- `exams()` - `GET /student/exams`
  Exam discovery page - sirf `status="Booking Open"` exams dikhata hai. Filters: course, type, search keyword (name/type mein ILIKE search). `active_booked_exam_ids` set banata hai - jo exams already booked hain unpe "Already Booked" badge dikhta hai UI mein.

- `exam_detail(exam_id)` - `GET /student/exams/<id>`
  Ek exam ka detail - metadata, rubric criteria (marks breakdown), available slots (seats > 0). `is_booking_open(exam)` check karta hai - window band hai toh booking button disabled hoga.

- `book_slot(slot_id)` - `POST /student/book/<slot_id>`
  Slot reservation - sabse important student function. Multiple safety checks:
  1. Slot exist karta hai?
  2. Exam lifecycle lock ke under `Booking Open` status mein hai + `is_booking_open()` True hai?
  3. Slot `Available` hai aur seats > 0?
  4. Student ne is exam ke liye already booking ki hai?
  5. Same date pe koi overlapping slot already booked hai? (time clash)
  
  Sab theek toh `Booking` row create karta hai, `slot.available_seats -= 1` aur agar seats = 0 toh `slot.status = "Full"`.

- `cancel_booking(booking_id)` - `POST /student/cancel/<id>`
  Booking cancel karta hai:
  - Ownership check (apni booking hi cancel kar sakta hai, warna 403)
  - Sirf `status="Booked"` cancel ho sakti hai
  - `exam.status == "Booking Open"` aur `exam.booking_end` deadline check - close hone ke baad cancel nahi ho sakta
  - Soft cancel: `status="Cancelled"`, `cancelled_at` timestamp, `slot.available_seats += 1` (aur agar slot Full tha toh wapas Available)

- `bookings()` - `GET /student/bookings`
  Student ki poori booking history (Booked, Cancelled, Completed sab). `now` bhi template ko deta hai deadline calculations ke liye.

- `schedule()` - `GET /student/schedule`
  Sirf active upcoming bookings (`status="Booked"`) chronologically - exam schedule calendar jaisa.

- `results()` - `GET /student/results`
  Official results - sirf woh bookings dikhata hai jahan `status="Completed"` aur `examination.results_published=True` ho. Evaluation scores yahan template mein `booking.evaluations` ke through access hote hain.

- `profile()` - `GET/POST /student/profile`
  Student apna naam, phone, roll_no update kar sakta hai.

**Kaun use karta hai / Kisse connect hai**:
- `app.py` mein register hota hai
- `decorators.py` se `role_required`
- `extensions.py` se `db`
- `models.py` se Booking, Course, Examination, ExamSlot, User
- `utils.py` se `is_booking_open`
- Templates: `student/` folder

**Code mein kahan dhundhu**: `dashboard` (L30), `exams` (L74), `exam_detail` (L120), `book_slot` (L159), `cancel_booking` (L234), `bookings` (L276), `schedule` (L290), `results` (L308), `profile` (L327)

---

## `blueprints/api.py`

**Kya karta hai**: REST API endpoints - JSON format mein data return karte hain. External dashboards, scripts, ya testing ke liye use hota hai.

**Path**: `blueprints/api.py`

**Main Features / Functions**:

`api_bp = Blueprint("api", __name__, url_prefix="/api")` - Saare routes `/api/` se shuru hote hain.

Sab routes `@login_required` hain - bina session ke 401 milega.

- `stats()` - `GET /api/stats`
  High-level portal metrics ek JSON mein:
  ```json
  {
    "success": true,
    "stats": {
      "courses_count": 5,
      "examinations_count": 12,
      "examiners_count": 8,
      "students_count": 150,
      "bookings_count": 320
    }
  }
  ```
  Koi role restriction nahi - koi bhi logged-in user dekh sakta hai.

- `examinations()` - `GET /api/examinations`
  Saare exams ki list - id, name, course_code, course_name, type, duration, max_marks, status, results_published. Created date descending order.

- `examination_detail(exam_id)` - `GET /api/examinations/<id>`
  Ek specific exam ka detail + uske saare rubric criteria (weightage aur description ke saath). Exam nahi mila toh 404 JSON.

- `students()` - `GET /api/students`
  Registered students ki list - id, name, email, roll_no, phone, status.
  **Sirf admin access kar sakta hai** (`@role_required("admin")`).

- `bookings()` - `GET /api/bookings`
  Booking records - role ke hisaab se filter hota hai:
  - **Admin**: Saari bookings
  - **Examiner**: Sirf apne slots ki bookings
  - **Student**: Sirf apni bookings
  
  Response mein: id, student_name, exam_name, exam_date (YYYY-MM-DD), slot_time (HH:MM - HH:MM), status.

**Kaun use karta hai / Kisse connect hai**:
- `app.py` mein register hota hai
- `decorators.py` se `role_required`
- `extensions.py` se `db`
- `models.py` se Booking, Course, Examination, ExamSlot, User
- Koi template use nahi hota - sirf `jsonify()` se JSON response

**Code mein kahan dhundhu**: `stats` (L17), `examinations` (L31), `examination_detail` (L53), `students` (L88), `bookings` (L110)

---

## Overall Architecture - Quick Map

```
app.py  ←──────────────────────────────────────────────┐
  │                                                     │
  ├── config.py          (settings)                     │
  ├── extensions.py      (db, login_manager)            │
  ├── models.py          (DB tables)                    │
  ├── seed.py            (default admin)                │
  ├── services.py        (transactions + lifecycle lock) │
  │                                                     │
  ├── blueprints/                                       │
  │   ├── auth.py        (/login, /register/*)          │
  │   ├── admin.py       (/admin/*)                     │
  │   ├── examiner.py    (/examiner/*)                  │
  │   ├── student.py     (/student/*)                   │
  │   └── api.py         (/api/*)                       │
  │                                                     │
  ├── decorators.py      (role_required)  ←─ blueprints use karte hain
  ├── utils.py           (window checks)  ←─ examiner + student use karte hain
  └── wsgi.py            (production entry point)

manage_admin.py  ←── standalone CLI (create_app() use karta hai)
```

**Data Flow (ek booking ka example)**:
1. Student `POST /student/book/<slot_id>` bhejta hai
2. `blueprints/student.py` ka `book_slot()` chalता hai
3. `@role_required("student")` via `decorators.py` check hota hai
4. `services.py` lifecycle transaction aur examination lock start karta hai
5. Current `Booking Open` state aur booking window `utils.py` se verify hote hain
6. `models.py` ke `Booking`, `ExamSlot` objects se DB operations hote hain
7. `extensions.py` ka `db.session.commit()` DB save karta hai

---

*Last updated: October 2026 | EMP v1.0*
