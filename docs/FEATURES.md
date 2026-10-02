# Features & Business Logic - EMP

Detailed rules for every major feature. This is the source of truth before writing route code.

---

## 1. Exam Status Lifecycle

```
Draft to Slot Creation to Booking Open to Booking Closed to Completed
```

Admin controls transitions with dedicated POST routes on the examination detail page.

Date windows are **also** checked - button alone is not enough:

| Status | Condition to enter |
|---|---|
| Slot Creation | Admin opens after a valid slot-creation timeline is configured |
| Booking Open | Admin opens after at least one active slot and a valid booking window exist |
| Booking Closed | Admin closes booking; booking end is set to the close timestamp |
| Completed | Admin marks complete (after all evaluations done) |

Helper functions in `utils.py`:
- `is_slot_creation_open(exam)` to bool
- `is_booking_open(exam)` to bool

The current status is persisted server-side. UI controls are not authorization: booking, cancellation, evaluation, completion, and publication each re-check the database state inside their transaction.

---

## 2. Examiner: Slot Rules

**Create allowed when:**
1. Examiner `status == active`
2. `is_slot_creation_open(exam)` is True
3. `exam_date` is in the future
4. `end_time > start_time` (end should equal start + exam.duration)
5. `capacity >= 1`
6. No overlapping slots for this examiner on the same day/time

**Edit/Delete allowed when:**
- Slot belongs to this examiner
- Booking window has NOT started yet OR slot has 0 active bookings

Slot `status` transitions:
- Created to `Available`
- `available_seats == 0` to `Full`
- Cancel on Full slot to `Available`
- Exam completed to all slots to `Completed`

---

## 3. Student: Booking Flow

**Checks (in order) before creating booking:**
1. Lock the examination lifecycle row and verify `status == 'Booking Open'` plus `is_booking_open(exam)`
2. `slot.status == 'Available'` and `slot.available_seats > 0`
3. No existing active booking: `Booking.query.filter_by(student_id=..., exam_id=..., status='Booked').first()`
4. *(Optional)* No time clash with another booked slot

**Transaction (atomic):**
```python
booking = Booking(status='Booked', ...)
slot.available_seats -= 1
if slot.available_seats == 0:
    slot.status = 'Full'
db.session.commit()
```

On SQLite, booking lifecycle writes begin with `BEGIN IMMEDIATE`; on databases that support row locking, the examination row is locked with `FOR UPDATE`. This serializes Close Booking with an in-flight booking request. A student request that acquires the lock after Close Booking sees `Booking Closed` and is rejected.

---

## 4. Student: Cancel Flow

**Allowed when:**
- `booking.status == 'Booked'`
- exam remains `Booking Open` and `datetime.now() <= exam.booking_end`

**Actions:**
```python
booking.status = 'Cancelled'
booking.cancelled_at = datetime.now()
slot.available_seats += 1
if slot.status == 'Full':
    slot.status = 'Available'
db.session.commit()
```

Row is **never deleted** - cancel = status change only.

---

## 5. Admin: Reschedule Booking

**Allowed when:**
- Booking is `Booked`
- No evaluations exist for this booking yet
- New slot has `available_seats > 0` and belongs to same exam

**Transaction:**
```python
old_slot.available_seats += 1
if old_slot.status == 'Full': old_slot.status = 'Available'
new_slot.available_seats -= 1
if new_slot.available_seats == 0: new_slot.status = 'Full'
booking.rescheduled_from = old_slot.id
booking.rescheduled_at = datetime.now()
booking.slot_id = new_slot.id
db.session.commit()
```

Also check: student doesn't already have an active booking on the new slot's exam (duplicate guard).

---

## 6. Admin: Change Slot Examiner

- Pick active examiner to update `slot.examiner_id`
- Check: new examiner has no overlapping slots at that time

---

## 7. Evaluation Flow

**Who can evaluate:** Examiner whose `id == slot.examiner_id` for that booking's slot.

**Backend check (must - UI hiding alone is not enough):**
```python
if booking.slot.examiner_id != current_user.id:
    abort(403)
```

**Process:**
1. Show form: one input per rubric (marks + remarks)
2. Validate: `0 <= marks <= rubric.max_marks`
3. Save one `Evaluation` row per rubric
4. Set `booking.status = 'Completed'`
5. Calculate total marks from saved rubric scores

Evaluation submission participates in the same lifecycle lock as completion and publication. Once results are published, later evaluation changes are rejected.

---

## 8. Results Visibility

- `exam.results_published` must be `True` for students to see their results
- Student sees only their own evaluations
- Admin and Examiner can see all results regardless of publish status

---

## 9. Access Control Summary

Every blueprint has `@login_required` + `@role_required('role')` on every route.

Ownership checks on resource-level operations:
- Examiner can only edit/delete/evaluate on their own slots
- Student can only cancel/view their own bookings

`decorators.py` provides `role_required(*roles)` which aborts with 403 on mismatch.

---

## 10. Lifecycle Feedback UI

- Close Booking, Mark as Completed, and Publish Results use an in-app EMP confirmation modal, not `window.confirm()`.
- Server flash messages render as top-right EMP toasts with success, warning, info, or danger styling.
- Toasts can be dismissed manually and automatically close after a short delay.

The UI improves feedback only; the POST routes remain the source of truth for lifecycle validation.

---

## 11. Edge Cases (test these before submission)

| Case | Expected behavior |
|---|---|
| Pending examiner tries to log in | Blocked with "Awaiting approval" message |
| Slot creation outside window | Form rejects with flash message |
| Booking outside window | Rejected |
| Student submits a stale booking form after admin closes booking | Rejected by the backend; no booking row is created |
| Two students race for last seat | Only one succeeds (transaction + seat check) |
| Same exam double-booking | App check + partial unique index both catch it |
| Cancel after deadline | Rejected |
| Examiner evaluates another examiner's student via URL | 403 |
| Marks > rubric.max_marks | Validation error |
| Reschedule to Full slot | Rejected |
| Edit slot with active bookings | Rejected |
| Student/Examiner opens /admin/* URL | 403 redirect |
