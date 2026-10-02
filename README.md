# Examination Management Portal (EMP)

MAD-1 Project | Flask + Jinja2 + Bootstrap 5 + SQLite

---

## Quick Start

```bash
# 1. Clone / unzip project
cd emp_project

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run (DB auto-created, admin seeded on first run)
python app.py
```

App opens at **http://127.0.0.1:5000**

Default admin credentials:
- Email: `admin@emp.local`
- Password: `Admin@123`

---

## Roles

| Role | How to get in | Default status |
|---|---|---|
| Admin | Pre-seeded, no registration | active |
| Examiner | `/register/examiner` | pending to admin approves |
| Student | `/register/student` | active immediately |

---

## Current Project Status

The portal is functionally complete for its core examination workflow:

1. Admin creates an exam, configures timelines and rubrics, then opens slot creation and student booking.
2. Examiners create slots and submit rubric-based evaluations.
3. Students can book only while the server-side booking state and booking window are both open.
4. Admin closes booking, marks the exam completed after all evaluations are complete, then publishes results.

Lifecycle actions are protected by database transactions and an examination-level lock. Closing booking takes effect immediately in the backend; a stale student page cannot create a new booking after the close transaction commits. The shared EMP interface uses in-app confirmation modals for lifecycle actions and top-right toasts for success, warning, and error feedback.

Run the regression suite with:

```bash
python -m unittest -v tests.test_emp_workflows
```

---

## Project Structure

```
emp_project/
├── app.py              # App factory, blueprint registration, DB init
├── config.py           # Config class (SECRET_KEY, DB URI, etc.)
├── extensions.py       # db, login_manager instances
├── models.py           # All SQLAlchemy models (8 tables)
├── seed.py             # Admin user seed (runs once)
├── decorators.py       # role_required decorator + helpers
├── utils.py            # is_booking_open, is_slot_creation_open
├── blueprints/
│   ├── auth.py         # /login, /logout, /register/*
│   ├── admin.py        # /admin/* all admin routes
│   ├── examiner.py     # /examiner/* slot CRUD + evaluation
│   ├── student.py      # /student/* browse, book, cancel, results
│   └── api.py          # /api/* optional JSON endpoints
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── admin/
│   ├── examiner/
│   └── student/
├── static/
│   ├── css/custom.css
│   └── js/
├── instance/emp.db     # auto-created
├── requirements.txt
└── README.md
```

---

## Docs

| File | What's inside |
|---|---|
| `RUN_GUIDE.md` | **Quick Run & Fresh Setup Guide (Commands & Troubleshooting)** |
| `docs/DEPLOYMENT_GUIDE.md` | **Cloud Deployment Guide (GitHub, Render, Vercel, Railway)** |
| `docs/guide/` | **Complete Step-by-Step Hinglish Guide & Code Map** |
| `docs/PYTHON_FILES.md` | **All 14 Python Files Explained (Functions, Classes, Connections)** |
| `docs/HTML_FILES.md` | **All 33 HTML Templates Explained (Context, Sections, Logic)** |
| `docs/SCHEMA.md` | All table definitions, column types, constraints |
| `docs/ROUTES.md` | Every route, HTTP method, access level |
| `docs/FEATURES.md` | Business logic rules, status lifecycles, edge cases |
| `docs/PROGRESS.md` | Milestone tracker - tick off as you build |

---

## Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Frontend:** Jinja2, Bootstrap 5
- **DB:** SQLite (`instance/emp.db`)
- **Auth:** werkzeug `generate_password_hash` / `check_password_hash`
# Examination-Management-Portal-EMP-
