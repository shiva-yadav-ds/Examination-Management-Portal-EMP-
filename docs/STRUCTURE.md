# Project Structure - EMP

Complete file tree with purpose of every file. Updated after cleanup.

---

```
emp_project/
│
├── app.py                        # Entry point. App factory, blueprint registration,
│                                 # db.create_all(), seed trigger. Run: python app.py
│
├── config.py                     # Config class: SECRET_KEY, SQLALCHEMY_DATABASE_URI,
│                                 # session settings and DEBUG flag
│
├── extensions.py                 # Initializes shared objects: db (SQLAlchemy),
│                                 # login_manager (Flask-Login). Imported by app.py + models.py
│
├── models.py                     # All 8 SQLAlchemy table models:
│                                 #   User, ExaminerProfile, Course, Examination,
│                                 #   Rubric, ExamSlot, Booking, Evaluation
│                                 # Also creates partial unique index uq_active_booking
│
├── seed.py                       # Seeds admin user on first run (only if not exists).
│                                 # Called from app.py after db.create_all()
│
├── decorators.py                 # role_required(*roles) decorator for route protection.
│                                 # Returns 403 on role mismatch
│
├── utils.py                      # Stateless helper functions:
│                                 #   is_slot_creation_open(exam) to bool
│                                 #   is_booking_open(exam), can_student_book(exam),
│                                 #   lifecycle window messaging
│
├── services.py                   # Transaction helpers, lifecycle row lock,
│                                 # seat helpers and evaluation/rubric helpers
│
├── manage_admin.py               # CLI: list/add/reset administrator accounts
├── wsgi.py                       # Production WSGI entry point
├── Procfile                      # Gunicorn process declaration
├── vercel.json                   # Vercel Python routing configuration
│
├── requirements.txt              # pip dependencies (Flask, Flask-SQLAlchemy,
│                                 # Flask-Login, Flask-WTF, werkzeug, etc.)
│
├── README.md                     # Quick start guide, run instructions, role table,
│                                 # tech stack, links to docs/
│
│
├── blueprints/                   # Route handlers split by role
│   ├── __init__.py               # Package marker (empty)
│   ├── auth.py                   # /login  /logout  /register/student  /register/examiner
│   ├── admin.py                  # /admin/* - courses, exams, rubrics, examiners,
│   │                             #            slots, bookings, search, reschedule,
│   │                             #            change-examiner, results publish
│   ├── examiner.py               # /examiner/* - slot CRUD, evaluate students,
│   │                             #               view own slots/bookings, profile
│   ├── student.py                # /student/* - browse exams, book, cancel,
│   │                             #              booking history, results, profile
│   └── api.py                    # /api/* - optional JSON endpoints for examinations,
│                                 #          examiners, students, bookings
│
│
├── templates/
│   ├── base.html                 # Master layout: Bootstrap 5 CDN, navbar (role-aware),
│   │                             # toast notifications, lifecycle and sign-out modals,
│   │                             # content block, footer and shared JS
│   │
│   ├── auth/
│   │   ├── login.html            # Login form (email + password)
│   │   ├── register_student.html # Student signup form (name, email, password, phone, roll_no)
│   │   └── register_examiner.html# Examiner signup form (name, email, password, department)
│   │
│   ├── admin/
│   │   ├── dashboard.html        # Counts: courses, exams, examiners, students,
│   │   │                         # pending approvals alert, recent activity
│   │   ├── courses.html          # Course list table + add/edit/deactivate actions
│   │   ├── exams.html            # Exam list + status badges + CRUD + status controls
│   │   ├── exam_detail.html      # Exam detail + integrated Rubrics management (add/delete criteria)
│   │   ├── examiners.html        # Examiner list + pending badge + approve/deactivate buttons
│   │   ├── students.html         # Student list with search by name or roll_no
│   │   ├── slots.html            # All slots across all exams; filter controls;
│   │   │                         # change-examiner action per slot
│   │   ├── bookings.html         # All bookings (Booked/Cancelled/Completed);
│   │   │                         # reschedule action for Booked rows
│   │   └── search.html           # Global search results across students/examiners/
│   │                             # exams/bookings, query param ?q=&type=
│   │
│   ├── examiner/
│   │   ├── dashboard.html        # Assigned exams count, slots created, booked students,
│   │   │                         # pending evaluations (slots where exam date passed)
│   │   ├── exams.html            # Active examinations that have this examiner's slots
│   │   ├── slots.html            # Own slot list: date, time, capacity, seats, status
│   │   ├── create_slot.html      # Slot creation form (blocked if outside window)
│   │   ├── students.html         # Booked students for a specific slot; evaluate button
│   │   ├── evaluate.html         # One form row per rubric: marks input + remarks textarea
│   │   │                         # 403 if examiner is not slot owner
│   │   └── profile.html          # Edit name, department, contact
│   │
│   └── student/
│       ├── dashboard.html        # Summary: available exams, upcoming booked slots,
│       │                         # published results count
│       ├── exams.html            # Browse + search exams (?q=&type=&course=)
│       ├── exam_detail.html      # Exam info + rubrics preview + available slot list
│       │                         # with Book button (POST form per slot)
│       ├── bookings.html         # Full booking history: all statuses, dates, slot info
│       ├── schedule.html         # Upcoming booked slots sorted by exam_date
│       ├── results.html          # Published results: total marks + per-criterion
│       │                         # marks and remarks (visible only after results_published)
│       └── profile.html          # Edit name, phone, roll_no
│
│
├── static/
│   └── css/
│       └── custom.css            # EMP tokens, components, toasts and responsive styles
│
│
├── docs/
│   ├── SCHEMA.md                 # All 8 table definitions, column types, constraints,
│   │                             # duplicate booking prevention, ER diagram
│   ├── ROUTES.md                 # Every route across all blueprints: method, access, purpose
│   ├── FEATURES.md               # Business logic rules, status lifecycles, all edge cases
│   ├── PROGRESS.md               # Milestone checklist (0 - 11) - tick off as you build
│   └── STRUCTURE.md              # ← this file
│
│
└── instance/
    └── emp.db                    # SQLite DB - auto-created by db.create_all() on first run.
                                  # Never edit manually. Listed in .gitignore
```

---

## Files That Were Removed (Cleanup)

| File | Why removed |
|---|---|
| `templates/login.html` | Empty duplicate - `templates/auth/login.html` is the correct one |
| `templates/register.html` | Empty - replaced by role-specific `register_student.html` / `register_examiner.html` |
| `templates/form.html` | Old scratch file, no Bootstrap, not in spec |
| `templates/home.html` | Old test page, no base.html, not in spec |
| `templates/auth/profile.html` | Profile is role-specific - `student/profile.html` and `examiner/profile.html` handle this |
| `database.py` | Empty file, not in spec |
| `init_db.py` | Used raw sqlite3 (conflicts with SQLAlchemy approach in `models.py`) |

---

## Quick Count

| Category | Count |
|---|---|
| Root Python source files | 10 (`app`, `config`, `extensions`, `models`, `seed`, `decorators`, `utils`, `services`, `manage_admin`, `wsgi`) |
| Blueprint files | 5 (`auth`, `admin`, `examiner`, `student`, `api`) |
| Templates | 33 (1 base + 3 error + 3 auth + 12 admin + 7 examiner + 7 student) |
| Static files | 1 (`custom.css`) |
| Documentation | 10 root guides plus 6 detailed guide files |
| Config/misc | `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `RUN_GUIDE.md`, `Procfile`, `vercel.json` |
| DB | 1 (`instance/emp.db`) |
