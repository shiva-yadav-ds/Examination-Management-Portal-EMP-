# Database Schema - EMP

All tables live in `instance/emp.db` (SQLite). Created via `db.create_all()` in `app.py`. Never edited manually.

---

## ER Diagram

```
USERS ──1:1──► EXAMINER_PROFILES
USERS ──1:N──► EXAM_SLOTS          (examiner creates)
USERS ──1:N──► BOOKINGS            (student makes)
COURSES ──1:N──► EXAMINATIONS
EXAMINATIONS ──1:N──► RUBRICS
EXAMINATIONS ──1:N──► EXAM_SLOTS
EXAM_SLOTS ──1:N──► BOOKINGS
BOOKINGS ──1:N──► EVALUATIONS
RUBRICS ──1:N──► EVALUATIONS
```

---

## Table Definitions

### users

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT NOT NULL | display name |
| email | TEXT UNIQUE NOT NULL | login credential |
| password | TEXT NOT NULL | Werkzeug password hash; never plain text |
| role | TEXT NOT NULL | `admin` / `examiner` / `student` |
| status | TEXT NOT NULL | `active` / `pending` / `inactive` |
| created_at | DATETIME | auto |
| phone | TEXT | optional |
| roll_no | TEXT | student-specific, used in search |

**Status rules:**
- Student registers to `status=active`
- Examiner registers to `status=pending` (blocked from login until admin approves)
- Admin approves to `status=active`; deactivate to `status=inactive`

---

### examiner_profiles

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | FK to users.id, UNIQUE | 1:1 with users |
| department | TEXT | |
| contact | TEXT | |

---

### courses

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| code | TEXT UNIQUE NOT NULL | e.g. `MLT101` |
| name | TEXT NOT NULL | |
| description | TEXT | |
| status | TEXT | `active` / `inactive` |
| created_at | DATETIME | |

---

### examinations

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| course_id | FK to courses.id | |
| name | TEXT | e.g. `MLT Viva` |
| type | TEXT | `Viva` / `Practical` / `Project Demo` / `Assessment` |
| duration | INTEGER | minutes |
| max_marks | INTEGER | |
| slot_creation_start | DATETIME | slot creation window opens |
| slot_creation_end | DATETIME | slot creation window closes |
| booking_start | DATETIME | booking opens |
| booking_end | DATETIME | booking closes (cancellation deadline too) |
| status | TEXT | `Draft` to `Slot Creation` to `Booking Open` to `Booking Closed` to `Completed` |
| results_published | BOOLEAN | default False; student sees results only when True |
| created_at | DATETIME | |

---

### rubrics

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| exam_id | FK to examinations.id | |
| criterion_name | TEXT | e.g. `Communication` |
| max_marks | INTEGER | |
| weightage | FLOAT | optional display metadata |
| description | TEXT | |

**Validation:** rubric `max_marks` total cannot exceed the exam's `max_marks`; result publication requires the total to equal it.

---

### exam_slots

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| exam_id | FK to examinations.id | |
| examiner_id | FK to users.id | admin can reassign |
| exam_date | DATE | |
| start_time | TIME | |
| end_time | TIME | start_time + exam.duration |
| capacity | INTEGER | max students per slot |
| available_seats | INTEGER | updated on every booking/cancel |
| status | TEXT | `Available` / `Full` / `Cancelled` / `Completed` |

> `available_seats` is stored (not derived) for simplicity. Must be kept consistent in every booking/cancel transaction.

---

### bookings

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| student_id | FK to users.id | |
| slot_id | FK to exam_slots.id | |
| exam_id | FK to examinations.id | denormalized for duplicate check |
| booking_date | DATETIME | |
| status | TEXT | `Booked` / `Cancelled` / `Completed` |
| cancelled_at | DATETIME | null unless cancelled |
| rescheduled_from | FK to exam_slots.id | null unless rescheduled |
| rescheduled_at | DATETIME | null unless rescheduled |

**Rows are never deleted** - `status=Cancelled` preserves history.

**Duplicate booking prevention (two layers):**
1. App-level check: `Booking.query.filter_by(student_id=..., exam_id=..., status='Booked').first()`
2. DB-level partial unique index (created in `models.py`):
   ```sql
   CREATE UNIQUE INDEX uq_active_booking
   ON bookings(student_id, exam_id)
   WHERE status = 'Booked';
   ```

---

### evaluations

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| booking_id | FK to bookings.id | |
| rubric_id | FK to rubrics.id | |
| marks | FLOAT | 0 ≤ marks ≤ rubric.max_marks |
| remarks | TEXT | per-criterion feedback |
| evaluated_at | DATETIME | |

**Constraint:** `UNIQUE(booking_id, rubric_id)` - one score per criterion per booking.

---

## Notes for Viva

- Single `users` table to role column separates behavior; no duplication
- `bookings` many-to-many resolved through junction table
- Partial unique index allows re-booking after cancel
- `available_seats` stored vs derived - explain both approaches
