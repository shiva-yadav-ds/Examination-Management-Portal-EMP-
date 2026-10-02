# Progress Tracker - EMP

Track build progress here. Check off tasks as each milestone is done. Commit to Git after each milestone.

---

## Milestone 0 - Git Setup
- [ ] Git tracker registration (compulsory - project won't be evaluated without this)
- [ ] Initial commit with folder structure

---

## Milestone 1 - Models + DB + Seed
- [x] `models.py` - all 8 tables written
- [x] Partial unique index `uq_active_booking` created
- [x] `extensions.py` - db, login_manager initialized
- [x] `app.py` - `db.create_all()` called, seed triggered
- [x] `seed.py` - admin seeded only if not exists
- [x] `instance/emp.db` created when app runs
- [x] Verified: all tables exist via SQLite browser or test script

---

## Milestone 2 - Auth
- [x] `blueprints/auth.py` - login, logout, register student, register examiner
- [x] Password hashed on save, checked on login
- [x] Pending/inactive examiner blocked at login
- [x] Role-based redirect after login (admin/examiner/student dashboard)
- [x] Email uniqueness validated
- [x] `decorators.py` - `role_required` decorator working
- [x] Auth templates: login, register_student, register_examiner

---

## Milestone 3 - Admin: Courses, Exams, Rubrics, Examiner Approval
- [x] Course CRUD (add, edit, deactivate)
- [x] Examination CRUD + timeline fields
- [x] Rubric CRUD per exam + validation (sum ≤ max_marks)
- [x] Examiner list - approve, deactivate, reactivate
- [x] Templates: courses, examinations, rubrics, examiners

---

## Milestone 4 - Admin: Timeline Controls
- [x] Status transitions: Draft to Slot Creation to Booking Open to Booking Closed to Completed
- [x] `utils.py` - `is_slot_creation_open`, `is_booking_open` helpers
- [x] Status change route working
- [x] Lifecycle feedback shown with EMP confirmation modals and toast notifications

---

## Milestone 5 - Examiner: Slot CRUD
- [x] Create slot (with all creation rules enforced)
- [x] Examiner time clash check
- [x] Edit + delete slot (before booking or 0 bookings)
- [x] Slot status auto-updates (Full/Available)
- [x] Templates: slots list, create_slot, edit slot

---

## Milestone 6 - Student: Browse, Book, Cancel, History
- [x] Exam browse + search + filter
- [x] Exam detail page with slot list
- [x] Book slot (transaction, duplicate check, seat decrement)
- [x] Cancel booking (deadline + seat restore)
- [x] Booking history page
- [x] Templates: exams, exam_detail, bookings, schedule

---

## Milestone 7 - Evaluation + Results
- [x] Examiner sees booked students per slot
- [x] Evaluate form per rubric
- [x] Marks validation (0 <= marks <= max)
- [x] 403 if not slot owner (backend check)
- [x] Booking marked Completed after evaluation
- [x] Admin publishes results (`results_published = True`)
- [x] Student sees results only when published
- [x] Templates: evaluate, results

---

## Milestone 8 - Admin: Advanced Features
- [x] Reschedule booking (with all transaction logic)
- [x] Change slot examiner (with clash check)
- [x] All bookings view (Booked + Cancelled + Completed)
- [x] Search across students/examiners/exams/bookings
- [x] Templates: bookings, search, slots (change examiner form)

---

## Milestone 9 - Dashboards + UI Polish
- [x] Admin dashboard - counts + pending approval alert
- [x] Examiner dashboard - pending evaluations count
- [x] Student dashboard - upcoming slots + published results
- [x] Bootstrap layout consistent across all pages
- [x] Flash messages styled
- [x] 403 / 404 pages

---

## Milestone 10 - Optional / Bonus
- [x] REST API endpoints (`/api/*`) with JSON responses
- [x] Frontend HTML5 validation attributes
- [x] Audit log for reschedule/examiner change

---

## Milestone 11 - Testing + Submission Prep
- [x] Workflow regression suite passes: `python -m unittest -v tests.test_emp_workflows`
- [x] `requirements.txt` up to date
- [x] `README.md` has clear run instructions
- [ ] Video recorded (screen + voice, drive link anyone-with-link)
- [ ] Project report written (≤ 5 pages, AI declaration included)
- [ ] Zip created: single root folder `emp_project/`
- [ ] Zip validated: runs fresh on another machine within 10 minutes

---

## Milestone 12 - Lifecycle Reliability and Cleanup
- [x] Close Booking uses a real SQLite immediate write transaction even after authenticated session loading.
- [x] Examination-level row locking protects booking, cancellation, evaluation, completion, and publication on supported databases.
- [x] Stale student booking forms are rejected after booking closes.
- [x] Lifecycle confirmation modal and toast feedback use the shared EMP design tokens.
- [x] Unused imports and generated Python cache directories cleaned without removing operational files.

## Notes / Known Issues

*(Add notes here as you build - decisions made, bugs fixed, things to revisit)*

- No known core workflow issue. The empty `.aws` path is environment-mounted and intentionally not removed by project cleanup.
