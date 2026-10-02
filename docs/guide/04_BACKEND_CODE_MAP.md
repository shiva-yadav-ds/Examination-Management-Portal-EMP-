# Backend Code Map & Developer Reference Guide

Yeh document ek developer cheat sheet hai jo batata hai ki **kaunsa feature kis file mein hai**, **kaunse functions use ho rahe hain**, aur agar aapko code mein koi specific cheez dekhni ya modify karni ho toh direct kahan jana hai.

---

## 1. Project Directory Structure

```
examination-management-portal/
├── app.py                  # App Factory (create_app), Error Handlers (403/404/500), user_loader
├── config.py               # Secret key, SQLite URI, 3-day persistent cookie lifetimes
├── extensions.py           # SQLAlchemy (db) aur Flask-Login (login_manager) instances
├── models.py               # Database ke 8 models, relationships aur constraints
├── decorators.py           # @role_required custom security decorator
├── utils.py                # Timeline helper functions (is_booking_open, is_slot_creation_open)
├── seed.py                 # Initial Admin account seed (admin@emp.local)
├── requirements.txt        # Python pip dependencies
│
├── blueprints/             # Route controllers (MVC Pattern)
│   ├── auth.py             # Login, Logout, Student/Examiner Registrations
│   ├── admin.py            # Courses, Examiners, Exams, Rubrics, Slots, Bookings, Search, Results
│   ├── examiner.py         # Slot creation, Edit/Delete, Booked students, Rubric evaluation
│   ├── student.py          # Browse exams, Slot booking, Cancellation, Schedule, Results
│   └── api.py              # REST API JSON endpoints (/api/stats, /api/examinations, etc.)
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Master layout: Navbar, toast stack, lifecycle/signout modals, Global JS
│   ├── 403.html            # Access Denied page
│   ├── 404.html            # Page Not Found page
│   ├── 500.html            # Internal Server Error page
│   ├── auth/               # Login, Student Signup, Examiner Signup
│   ├── admin/              # Admin dashboard, courses, exams, exam_detail, slots, bookings, search
│   ├── examiner/           # Examiner dashboard, exams, slots, create_slot, students, evaluate
│   └── student/            # Student dashboard, exams, exam_detail, bookings, schedule, results
│
├── static/
│   └── css/
│       └── custom.css      # Design System: Colors, emp-card, emp-btn, emp-table, tokens
│
└── docs/
    └── guide/              # Hinglish detailed documentation
        ├── 00_OVERVIEW_AND_LIFECYCLE.md
        ├── 01_ADMIN_GUIDE.md
        ├── 02_EXAMINER_GUIDE.md
        ├── 03_STUDENT_GUIDE.md
        └── 04_BACKEND_CODE_MAP.md
```

---

## 2. "Main Code Mein Kahan Dhundhu?" (Feature to Code Mapping)

Agar aapko code inspect karna hai, toh is table se direct file aur function mil jayega:

| Feature / Sawal | File Path | Function / Class |
|---|---|---|
| **Role-based Access Control (403/401)** | `decorators.py` | `@role_required(*roles)` |
| **Login Verification & 3-day Cookie** | `blueprints/auth.py` | `login()` |
| **Session Lifetime Configuration** | `config.py` | `PERMANENT_SESSION_LIFETIME`, `REMEMBER_COOKIE_DURATION` |
| **Sign out Confirmation Pop-up** | `templates/base.html` | `#logoutModal` |
| **Lifecycle confirmation + toast feedback** | `templates/base.html`, `static/css/custom.css` | `#lifecycleConfirmModal`, `[data-emp-toast]` |
| **Password Show/Hide Eye Toggle** | `templates/base.html` | Vanilla JS `.btn-toggle-password` listener |
| **Course CRUD & Deactivation** | `blueprints/admin.py` | `courses()`, `create_course()`, `toggle_course_status()` |
| **Examiner Approval / Deactivation** | `blueprints/admin.py` | `approve_examiner()`, `toggle_examiner_status()` |
| **Exam Status Lifecycle Transitions** | `blueprints/admin.py` | `open_slot_creation()`, `open_booking()`, `close_booking()`, `complete_exam()`, `publish_results()` |
| **Immediate Close Booking / lifecycle lock** | `services.py`, `blueprints/admin.py`, `blueprints/student.py` | `begin_immediate_write_transaction()`, `lock_examination_for_lifecycle_change()` |
| **Rubric Sum <= Max Marks Guard** | `blueprints/admin.py` | `add_rubric()` |
| **Admin Reschedule Booking** | `blueprints/admin.py` | `reschedule_booking()` |
| **Global 4-in-1 Unified Search** | `blueprints/admin.py` | `search()` |
| **Slot Auto End-time Calculation** | `blueprints/examiner.py` | `create_slot()` (line ~125) |
| **Examiner Slot Clash Detection** | `blueprints/examiner.py` | `create_slot()` (line ~130) |
| **Examiner Ownership Guard (403)** | `blueprints/examiner.py` | `slot_students()`, `evaluate()` |
| **Rubric Marks Range Validation** | `blueprints/examiner.py` | `evaluate()` (line ~280) |
| **Evaluation Upsert & Complete Status**| `blueprints/examiner.py` | `evaluate()` (line ~300) |
| **Student Double Booking Guard** | `blueprints/student.py` | `book_slot()` (line ~155) |
| **Student Time Clash Guard** | `blueprints/student.py` | `book_slot()` (line ~165) |
| **Atomic Seat Decrement & Status Full**| `blueprints/student.py` | `book_slot()` (line ~185) |
| **Booking Cancel & Seat Restore** | `blueprints/student.py` | `cancel_booking()` (line ~205) |
| **Student Scorecard Visibility** | `blueprints/student.py` | `results()` (line ~270) |
| **Custom 403/404/500 Error Handlers** | `app.py` | `@app.errorhandler(403/404/500)` |
| **REST API Endpoints** | `blueprints/api.py` | `stats()`, `examinations()`, `students()`, `bookings()` |

---

## 3. Important Design Decisions & Interview Notes

1. **Server-Side Rendering (SSR) Priority**:
   - Project specifications ke mutabik core functionality (booking, evaluation, cancellation) pure server-side Python (Flask) se render aur execute hoti hai.
   - Client-side JS sirf UX enhancements ke liye hai (password eye toggle, EMP modals, aur toasts). Core booking ya validation kabhi browser JS par depend nahi karti.

2. **Atomic State Synchronization**:
   - `ExamSlot.available_seats` aur `ExamSlot.status` har booking aur cancellation par ek hi database transaction mein commit hote hain. Agar transaction fail ho toh seats aur status kabhi desync nahi hote.
   - Exam lifecycle actions aur booking mutations same examination-level lock use karte hain. Isse Close Booking commit hone ke baad stale booking request succeed nahi kar sakti.

3. **Data Integrity & Soft-Deletions**:
   - Jab koi student booking cancel karta hai, toh row delete nahi hoti (`DELETE FROM bookings`), balki `status = 'Cancelled'` mark hoti hai aur `cancelled_at` save hota hai. Isse complete audit history bani rehti hai.
   - Similarly, agar kisi rubric par evaluation ho chuki ho, toh wo rubric delete nahi kiya ja sakta.

4. **Independent FKs on Booking Model**:
   - `Booking` model ke paas do foreign keys hain `ExamSlot` par: ek current slot ke liye (`slot_id`) aur ek reschedule history ke liye (`rescheduled_from`). SQLAlchemy mein inhe explicit `foreign_keys=[...]` ke saath bind kiya gaya hai taaki query resolution ambiguous na ho.
