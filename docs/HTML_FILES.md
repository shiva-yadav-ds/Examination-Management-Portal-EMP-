# EMP HTML Templates - Complete Documentation

> **Examination Management Portal (EMP)** ke saare 33 HTML template files ka complete, detailed reference.
> Hinglish mein likha gaya hai - simple, practical, aur point-to-point. Har file ka purpose, backend route, context variables, aur key UI logic explain kiya gaya hai.

---

## Table of Contents

### 1. Root Layout & Error Pages (4 Files)
- [`templates/base.html`](#templatesbasehtml) - Master layout, navbar, sign-out modal, password toggle
- [`templates/403.html`](#templates403html) - Access Denied (role permission error)
- [`templates/404.html`](#templates404html) - Page Not Found
- [`templates/500.html`](#templates500html) - Internal Server Error (with rollback)

### 2. Authentication Module (3 Files)
- [`templates/auth/login.html`](#templatesauthloginhtml) - Common sign in page for all roles
- [`templates/auth/register_student.html`](#templatesauthregister_studenthtml) - Public student self-registration
- [`templates/auth/register_examiner.html`](#templatesauthregister_examinerhtml) - Public examiner registration (pending approval)

### 3. Admin Module (11 Files)
- [`templates/admin/dashboard.html`](#templatesadmindashboardhtml) - Portal metrics & pending approval alerts
- [`templates/admin/courses.html`](#templatesadmincourseshtml) - Course list, creation & inline editing
- [`templates/admin/exams.html`](#templatesadminexamshtml) - Examination list & creation form
- [`templates/admin/exam_detail.html`](#templatesadminexam_detailhtml) - Lifecycle status controls, timelines & rubrics
- [`templates/admin/examiners.html`](#templatesadminexaminershtml) - Examiner directory with approval/deactivation controls
- [`templates/admin/examiners_add.html`](#templatesadminexaminers_addhtml) - Direct examiner creation by admin
- [`templates/admin/slots.html`](#templatesadminslotshtml) - Central slot monitor & examiner reassignment
- [`templates/admin/bookings.html`](#templatesadminbookingshtml) - Booking audit log & in-place rescheduling
- [`templates/admin/students.html`](#templatesadminstudentshtml) - Student directory with instant search
- [`templates/admin/search.html`](#templatesadminsearchhtml) - Unified 4-in-1 global search results
- [`templates/admin/results.html`](#templatesadminresultshtml) - Master gradebook with rubric breakdowns

### 4. Examiner Module (7 Files)
- [`templates/examiner/dashboard.html`](#templatesexaminerdashboardhtml) - Faculty overview, metric cards & pending evaluations
- [`templates/examiner/exams.html`](#templatesexaminerexamshtml) - Open exams accepting slot creation
- [`templates/examiner/slots.html`](#templatesexaminerslotshtml) - Faculty's scheduled slots with edit & cancellation
- [`templates/examiner/create_slot.html`](#templatesexaminercreate_slothtml) - New exam slot creation form
- [`templates/examiner/students.html`](#templatesexaminerstudentshtml) - Booked candidates list for a slot
- [`templates/examiner/evaluate.html`](#templatesexaminerevaluatehtml) - Rubric-wise marks & feedback scoring form
- [`templates/examiner/profile.html`](#templatesexaminerprofilehtml) - Examiner profile settings

### 5. Student Module (7 Files)
- [`templates/student/dashboard.html`](#templatesstudentdashboardhtml) - Student home with upcoming bookings & quick actions
- [`templates/student/exams.html`](#templatesstudentexamshtml) - Browse open exams with filters & search
- [`templates/student/exam_detail.html`](#templatesstudentexam_detailhtml) - Exam rules, rubric preview & slot reservation
- [`templates/student/bookings.html`](#templatesstudentbookingshtml) - Booking history with cancellation action
- [`templates/student/schedule.html`](#templatesstudentschedulehtml) - Upcoming confirmed sessions calendar cards
- [`templates/student/results.html`](#templatesstudentresultshtml) - Official scorecards with rubric breakdown
- [`templates/student/profile.html`](#templatesstudentprofilehtml) - Candidate profile settings

---

## 1. Root Layout & Error Templates

### `templates/base.html`

**Kya page render karta hai**: Pure portal ka master skeleton/parent layout. Role-specific templates isko `{% extends "base.html" %}` karke inherit karte hain.

**Backend Route**: Direct koi route render nahi karta; har template iske blocks (`{% block content %}`, `{% block title %}`) ko populate karta hai.

**Context Variables**:
- `current_user` (Flask-Login): Authenticated user object (`role`, `name`, `email`, `is_authenticated`).
- `request.endpoint`: Current active route ka naam (navbar links ko `active` class dene ke liye).
- `get_flashed_messages(with_categories=true)`: Session flash notifications (success, danger, info).

**Key UI Sections & Features**:
- **EMP Top Navigation Bar**: Role-based links show karta hai:
  - Admin: Dashboard, Courses, Examinations, Examiners, Slots, Bookings, Students, Results, Global Search Icon.
  - Examiner: Dashboard, Open Exams, My Slots, Profile.
  - Student: Dashboard, Browse Exams, My Bookings, Schedule, Results, Profile.
  - Guest: Login, Student Signup, Examiner Signup.
- **User Chip & Sign Out Button**: Current user ka naam aur role badge dikhata hai.
- **Sign Out Confirmation Modal (`#logoutModal`)**: Accidental click rokne ke liye popup modal dikhata hai jisme "Stay signed in" aur "Sign out" ke options hote hain.
- **Toast Notifications Container**: Server flash messages EMP-styled top-right toasts mein render hote hain; close button aur auto-dismiss dono available hain.
- **Lifecycle Confirmation Modal (`#lifecycleConfirmModal`)**: Close Booking, Mark as Completed, aur Publish Results ke liye shared in-app confirmation. Browser-native `confirm()` use nahi hota.
- **Global Password Eye Toggle JS**: Event delegation ke through `.btn-toggle-password` buttons par click karne se password field `type="password"` se `type="text"` mein toggle ho jati hai aur icon badal jata hai.
- **Footer**: Copyright aur IITM BS Degree MAD-1 project branding.

---

### `templates/403.html`

**Kya page render karta hai**: Access Denied / Forbidden error page. Jab koi user kisi aisi URL par jata hai jiska role allow nahi hai (jaise Student agar `/admin/dashboard` khole).

**Backend Route**: `app.py -> forbidden_error(error)` (HTTP 403 status ke saath).

**Context Variables**: None.

**Key UI Sections & Features**:
- Yellow shield lock icon (`bi-shield-lock`).
- Clear message explaining permission rejection.
- "Return to Dashboard" button (`auth.index` par bhejta hai jo role ke hisaab se dashboard par redirect karta hai).
- "Sign In with Different Account" button (`auth.logout` par bhejta hai).

---

### `templates/404.html`

**Kya page render karta hai**: Not Found error page. Jab koi aisi URL request ki jaye jo portal mein exist nahi karti ya koi deleted resource khoja jaye.

**Backend Route**: `app.py -> not_found_error(error)` (HTTP 404 status ke saath).

**Context Variables**: None.

**Key UI Sections & Features**:
- Question circle icon (`bi-question-circle`).
- User-friendly error message.
- "Back to Home" button.

---

### `templates/500.html`

**Kya page render karta hai**: Internal Server Error page. Agar backend execution ke dauran koi unexpected crash ya unhandled exception aata hai.

**Backend Route**: `app.py -> internal_error(error)` (HTTP 500 status ke saath, backend automatically `db.session.rollback()` call karta hai).

**Context Variables**: None.

**Key UI Sections & Features**:
- Red warning triangle icon (`bi-exclamation-triangle`).
- Informative message: "Any incomplete transaction has been safely rolled back".
- "Return to Dashboard" button.

---

## 2. Authentication Module

### `templates/auth/login.html`

**Kya page render karta hai**: Common sign in portal jahan se teeno roles (Admin, Examiner, Student) login karte hain.

**Backend Route**: `GET /login` -> `blueprints/auth.py -> login()`

**Context Variables**: None (pure HTML form with Flask-Login backend handler).

**Key UI Sections & Features**:
- Clean card with mortarboard icon and title.
- Email address input field.
- Password input field with integrated eye toggle icon (`.btn-toggle-password`).
- "Sign in" full-width button.
- Bottom links: "Student Registration" aur "Examiner Signup".

**Forms / Actions**:
- `POST /login`: Form submits `email` aur `password`. Backend authenticate karta hai aur 3-day persistent remember cookie set karta hai.

---

### `templates/auth/register_student.html`

**Kya page render karta hai**: Students ke liye public self-registration form.

**Backend Route**: `GET /register/student` -> `blueprints/auth.py -> register_student()`

**Context Variables**: None.

**Key UI Sections & Features**:
- Full Name, Email, Password (with eye toggle).
- Roll Number (`roll_no`) field (unique student ID).
- Phone Number field (contact info).
- Instant Activation: Submit karte hi account `status='active'` banta hai aur turant login redirect hota hai.

**Forms / Actions**:
- `POST /register/student`: Validates unique email, unique roll_no, hashes password, creates `User` + `StudentProfile`, and redirects to login.

---

### `templates/auth/register_examiner.html`

**Kya page render karta hai**: Faculty/examiners ke liye registration form.

**Backend Route**: `GET /register/examiner` -> `blueprints/auth.py -> register_examiner()`

**Context Variables**: None.

**Key UI Sections & Features**:
- Full Name, Email, Password (with eye toggle).
- Academic Department field (e.g., Computer Science, Data Science).
- Phone Number field.
- Pending Notice Banner: User ko clearly batata hai ki submission ke baad account `pending` rahega jab tak Portal Admin use approve na kar de.

**Forms / Actions**:
- `POST /register/examiner`: Creates `User` with `status='pending'` and attached `ExaminerProfile`. Flashes approval warning message.

---

## 3. Admin Module

### `templates/admin/dashboard.html`

**Kya page render karta hai**: Admin ka main landing dashboard portal-wide high-level metrics aur quick actions ke saath.

**Backend Route**: `GET /admin/dashboard` -> `blueprints/admin.py -> dashboard()`

**Context Variables**:
- `course_count`: Total active courses.
- `examination_count`: Total created examinations.
- `examiner_count`: Total registered examiners.
- `student_count`: Total registered students.
- `pending_examiner_count`: Awaiting approval examiners count.
- `slot_count`: Total scheduled exam slots.
- `booking_count`: Total student reservations.

**Key UI Sections & Features**:
- **Pending Examiner Banner**: Agar `pending_examiner_count > 0` hai toh top par warning banner aata hai direct "Review Applications" button ke saath.
- **Top 4 Stat Cards**: Courses, Examinations, Active Examiners, Total Students.
- **Secondary Stat Cards**: Total Scheduled Slots, Student Bookings.
- **Quick Action Grid**: Quick navigation shortcuts to Courses, Examinations, Examiners, Slots, Bookings, Students.

---

### `templates/admin/courses.html`

**Kya page render karta hai**: Course curriculum directory. Courses add karna, unki list dekhna, inline edit karna, aur deactivate karna.

**Backend Route**: `GET /admin/courses` -> `blueprints/admin.py -> courses()`

**Context Variables**:
- `courses`: List of all `Course` objects sorted by code.

**Key UI Sections & Features**:
- **Add New Course Card**: Code (`code`), Name (`name`), Description (`description`).
- **All Courses Table**: Shows Course Code (bold blue), Name, Description, Status chip (Active/Inactive), and Actions.
- **Collapsible Inline Edit Row**: Har course row ke neeche ek collapse row hoti hai jisme edit form khulta hai bina doosre page par navigate kiye.
- **Deactivate Button**: Active courses ko deactivate karne ka button with confirmation popup.

**Forms / Actions**:
- `POST /admin/courses/create`: Creates new course with uppercase code.
- `POST /admin/courses/<id>/edit`: Updates course code, name, description, and status.
- `POST /admin/courses/<id>/deactivate`: Sets course status to `inactive`.

---

### `templates/admin/exams.html`

**Kya page render karta hai**: Sabhi examinations ki directory aur naya examination event create karne ka form.

**Backend Route**: `GET /admin/exams` -> `blueprints/admin.py -> exams()`

**Context Variables**:
- `exams`: List of all `Examination` objects with attached courses.
- `courses`: List of active courses for dropdown selection.
- `exam_types`: Supported types `["Viva", "Practical", "Project Presentation", "Interview", "Oral Exam"]`.

**Key UI Sections & Features**:
- **Create Examination Form**:
  - Course selection dropdown.
  - Exam Name, Exam Type dropdown, Duration (minutes), Max Marks.
  - Optional timeline inputs: Slot Creation window & Booking window dates.
  - Submit button: "Create as Draft".
- **Examinations List Table**:
  - Name, Course, Type, Duration, Max Marks, Status Chip (Draft, Slot Creation, Booking Open, Booking Closed, Completed).
  - Results Published chip badge.
  - "Manage" button linking to `admin.exam_detail`.

**Forms / Actions**:
- `POST /admin/exams/create`: Creates examination in `Draft` state with optional timeline dates.

---

### `templates/admin/exam_detail.html`

**Kya page render karta hai**: Single examination control hub. Timeline configuration, lifecycle transitions, aur evaluation rubrics management.

**Backend Route**: `GET /admin/exams/<id>` -> `blueprints/admin.py -> exam_detail()`

**Context Variables**:
- `exam`: Current `Examination` model object.
- `exam_types`: Supported exam types list.
- `rubric_total`: Sum of max marks across all attached rubrics.

**Key UI Sections & Features**:
- **Header & Status Badges**: Exam name, course, type, current lifecycle state.
- **Lifecycle Controls Section**:
  - When `Draft`: "Open Slot Creation" button (requires timeline dates to be set).
  - When `Slot Creation`: "Open Bookings" button (checks if at least 1 active slot exists).
  - When `Booking Open`: "Close Bookings" button.
  - When `Booking Closed`: "Mark Completed" button.
  - When `Completed` and not published: "Publish Results" button (checks if rubrics exist and students are evaluated).
- **Examination Details & Inline Edit**: Collapsible form to edit duration, max marks, and all 4 timeline timestamps while in `Draft` status.
- **Evaluation Rubrics Section**:
  - Rubric marks counter (`rubric_total / exam.max_marks`).
  - Chip showing "unallocated marks" or "Fully allocated".
  - Rubric criteria table (Criterion Name, Max Marks, Weightage %, Description, Delete action).
  - Delete guard: Agar kisi student ka evaluation exist karta hai toh delete button disable ho jata hai.
- **Add Rubric Criterion Form**: Name, Max Marks, Weightage, Description.

**Forms / Actions**:
- `POST /admin/exams/<id>/edit`: Updates exam metadata & timelines.
- `POST /admin/exams/<id>/open-slot-creation`: Status -> `Slot Creation`.
- `POST /admin/exams/<id>/open-booking`: Status -> `Booking Open`.
- `POST /admin/exams/<id>/close-booking`: Status -> `Booking Closed` and booking end set to the close timestamp.
- `POST /admin/exams/<id>/complete`: Status -> `Completed`.
- `POST /admin/exams/<id>/publish-results`: Sets `results_published=True`.
- `POST /admin/exams/<id>/rubrics/add`: Inserts new `Rubric` row.
- `POST /admin/rubrics/<id>/delete`: Deletes rubric criterion (if no evaluations exist).

---

### `templates/admin/examiners.html`

**Kya page render karta hai**: Faculty directory with account approval and activation management.

**Backend Route**: `GET /admin/examiners` -> `blueprints/admin.py -> examiners()`

**Context Variables**:
- `examiners`: List of faculty `User` objects with joined `ExaminerProfile`.

**Key UI Sections & Features**:
- Top header with "Add Examiner Directly" button (`admin.add_examiner`).
- Table listing: Name, Email, Department, Phone, Status badge (Active, Pending, Inactive), and Action controls.
- **Conditional Action Buttons**:
  - Agar `pending`: "Approve" button aur "Reject" button dikhte hain.
  - Agar `active`: "Deactivate" button dikhta hai.
  - Agar `inactive`: "Activate" button dikhta hai.

**Forms / Actions**:
- `POST /admin/examiners/<id>/approve`: Status -> `active`.
- `POST /admin/examiners/<id>/reject`: Status -> `inactive`.
- `POST /admin/examiners/<id>/toggle-status`: Flips status between active and inactive.

---

### `templates/admin/examiners_add.html`

**Kya page render karta hai**: Direct examiner creation form for administrators.

**Backend Route**: `GET /admin/examiners/add` -> `blueprints/admin.py -> add_examiner()`

**Context Variables**: None.

**Key UI Sections & Features**:
- Full Name, Email, Temporary Password, Academic Department, Phone Number.
- Direct Active Status Notice: Admin dwara banaya gaya account instantly `active` hota hai bina approval queue ke.

**Forms / Actions**:
- `POST /admin/examiners/add`: Creates faculty account in `active` state and redirects to examiner list.

---

### `templates/admin/slots.html`

**Kya page render karta hai**: Central slot monitoring table across all exams with evaluator reassignment tool.

**Backend Route**: `GET /admin/slots` -> `blueprints/admin.py -> slots()`

**Context Variables**:
- `slots`: Filtered list of `ExamSlot` objects.
- `exams`: List of examinations for filter dropdown.
- `examiners`: List of active faculty for filter and reassignment dropdowns.
- `selected_exam_id`, `selected_examiner_id`, `selected_status`: Active filter state.

**Key UI Sections & Features**:
- **Filters Bar**: Filter by Examination, Examiner, and Status (Available, Full, Cancelled, Completed).
- **Slots Table**:
  - Exam Name & Course code.
  - Date & Time window.
  - Assigned Examiner name and department.
  - Seat utilization (`booked_count / capacity` + Available count).
  - Status chip.
- **Change Examiner Modal / Collapse Row**:
  - Har slot ke aage "Change Examiner" button hota hai.
  - Dropdown me doosre active faculty dikhte hain.
  - Backend time-overlap check karta hai taaki naye examiner ka koi clash na ho.

**Forms / Actions**:
- `POST /admin/slots/<id>/change-examiner`: Reassigns slot to new faculty member.

---

### `templates/admin/bookings.html`

**Kya page render karta hai**: Complete audit log of all student reservations with rescheduling tool.

**Backend Route**: `GET /admin/bookings` -> `blueprints/admin.py -> bookings()`

**Context Variables**:
- `bookings`: List of `Booking` objects.
- `exams`: Examinations list for filtering.
- `available_slots`: List of slots having free seats.
- `selected_exam_id`, `selected_status`: Filter state.

**Key UI Sections & Features**:
- **Filters Bar**: Exam dropdown, Status dropdown (Booked, Cancelled, Completed).
- **Bookings Table**:
  - Booking ID, Student Name, Roll Number, Exam Name, Slot Date & Time, Assigned Examiner, Status Chip.
- **Reschedule Collapse Row**:
  - Active bookings ke liye "Reschedule" button khulta hai.
  - Target slot dropdown shows only available slots of the *same* examination.
  - Atomically puraane slot ki seat increment aur naye slot ki seat decrement hoti hai.

**Forms / Actions**:
- `POST /admin/bookings/<id>/reschedule`: Transfers student to another available slot.

---

### `templates/admin/students.html`

**Kya page render karta hai**: Candidate directory with live search.

**Backend Route**: `GET /admin/students` -> `blueprints/admin.py -> students()`

**Context Variables**:
- `students`: List of student `User` objects with joined `StudentProfile`.
- `search_query`: Active search string.

**Key UI Sections & Features**:
- Search input box (filters instantly across Name, Email, and Roll Number).
- Students Table: Name, Email, Roll Number, Phone Number, Registered Date, and Status Chip.

---

### `templates/admin/search.html`

**Kya page render karta hai**: Unified 4-in-1 global search result page.

**Backend Route**: `GET /admin/search` -> `blueprints/admin.py -> search()`

**Context Variables**:
- `query`: Search keyword entered by user.
- `courses`: Matching courses list.
- `exams`: Matching examinations list.
- `examiners`: Matching faculty list.
- `students`: Matching candidates list.
- `total_results`: Total count of all matching records.

**Key UI Sections & Features**:
- Global search input bar with search button.
- 4 Tabbed / Grouped result cards: Courses Results, Examinations Results, Examiners Results, Students Results.
- Direct navigation links into the respective entity detail/edit pages.

---

### `templates/admin/results.html`

**Kya page render karta hai**: Master gradebook view showing completed evaluations for each examination.

**Backend Route**: `GET /admin/results` -> `blueprints/admin.py -> results()`

**Context Variables**:
- `exams`: All examinations list for selection tabs.
- `selected_exam`: Currently selected `Examination` object.
- `results_data`: List of completed candidate records with total score and rubric-by-rubric score breakdown.

**Key UI Sections & Features**:
- Exam Selection Pills/Dropdown.
- Results Table: Student Name, Roll No, Slot Date, Evaluator Name, Rubric Columns (Marks obtained per criterion), Total Score, and Percentage.
- Status indicator showing whether results have been published to students.

---

## 4. Examiner Module

### `templates/examiner/dashboard.html`

**Kya page render karta hai**: Faculty home dashboard showing personal activity stats and pending grading alerts.

**Backend Route**: `GET /examiner/dashboard` -> `blueprints/examiner.py -> dashboard()`

**Context Variables**:
- `open_exams_count`: Examinations currently accepting slots.
- `my_slots_count`: Total slots created by this examiner.
- `my_candidates_count`: Total students booked under this examiner.
- `pending_evaluations_count`: Candidates whose slot has passed or booked but not yet evaluated.
- `pending_bookings`: List of bookings waiting for evaluation.

**Key UI Sections & Features**:
- Top 4 Metric Cards: Open Exams, My Slots, Total Candidates, Pending Evaluations.
- **Pending Evaluations Table**: Student name, Roll number, Exam name, Slot time, and direct **"Evaluate"** action button.
- Quick navigation buttons to "Open Exams" and "Create New Slot".

---

### `templates/examiner/exams.html`

**Kya page render karta hai**: Examinations directory currently in `Slot Creation` status.

**Backend Route**: `GET /examiner/exams` -> `blueprints/examiner.py -> exams()`

**Context Variables**:
- `exams`: List of `Examination` objects open for slot creation.
- `my_slot_counts`: Dictionary mapping `exam_id -> count of slots` created by current examiner.

**Key UI Sections & Features**:
- Exam card with Course Code, Exam Name, Duration, Max Marks.
- Slot window validity dates.
- Examiner's existing slot count for this exam.
- **"Create Slot"** button linking directly to slot creator with `exam_id` preselected.

---

### `templates/examiner/slots.html`

**Kya page render karta hai**: Examiner ke dwara banaye gaye sabhi slots ki list with inline edit controls.

**Backend Route**: `GET /examiner/slots` -> `blueprints/examiner.py -> slots()`

**Context Variables**:
- `slots`: All `ExamSlot` objects owned by `current_user`.
- `now`: Current server datetime for edit eligibility checks.

**Key UI Sections & Features**:
- Slots Table: Exam Name, Date, Time Window, Booked/Capacity Seats, Status Chip.
- Actions:
  - **"Students"** button: View candidates booked in this slot.
  - **"Edit"** button: Opens collapsible inline row to change date, time, capacity (only allowed before student booking starts).
  - **"Cancel"** button: Cancels slot (if no active bookings exist).

**Forms / Actions**:
- `POST /examiner/slots/<id>/edit`: Updates date, time, capacity.
- `POST /examiner/slots/<id>/delete`: Cancels slot.

---

### `templates/examiner/create_slot.html`

**Kya page render karta hai**: Naya exam slot define karne ka form.

**Backend Route**: `GET /examiner/slots/create` -> `blueprints/examiner.py -> create_slot()`

**Context Variables**:
- `exams`: List of exams in `Slot Creation` or `Booking Open` status.
- `selected_exam_id`: Pre-filled exam if accessed from exams page.

**Key UI Sections & Features**:
- Examination selection dropdown.
- Exam Date (`exam_date`) picker.
- Start Time (`start_time`) picker (End time auto-calculated by exam duration).
- Seating Capacity (`capacity`) field (default 1).
- Time clash validation notice.

**Forms / Actions**:
- `POST /examiner/slots/create`: Validates timeline bounds and examiner time clashes, then creates `ExamSlot`.

---

### `templates/examiner/students.html`

**Kya page render karta hai**: Kisi specific slot ke andar booked candidates ki list.

**Backend Route**: `GET /examiner/slots/<slot_id>/students` -> `blueprints/examiner.py -> slot_students()`

**Context Variables**:
- `slot`: The `ExamSlot` object.
- `bookings`: List of `Booking` objects for this slot.

**Key UI Sections & Features**:
- Slot summary banner (Date, Time, Exam Name, Course).
- Candidates Table: Roll Number, Student Name, Email, Booking Status, Evaluation Status.
- **"Evaluate"** button: Links to `examiner.evaluate`. Agar already evaluate ho chuka hai toh "Update Marks" button dikhta hai.

---

### `templates/examiner/evaluate.html`

**Kya page render karta hai**: Candidate performance evaluation form based on official rubrics.

**Backend Route**: `GET /examiner/evaluate/<booking_id>` -> `blueprints/examiner.py -> evaluate()`

**Context Variables**:
- `booking`: The candidate's `Booking` object.
- `exam`: Attached `Examination` object.
- `rubrics`: List of evaluation rubric criteria.
- `existing_scores`: Dictionary of previously saved scores for this booking (if editing).

**Key UI Sections & Features**:
- Candidate info card (Name, Roll No, Email, Exam Type, Max Marks).
- **Dynamic Rubric Scoring Cards**:
  - Criterion Name, Weightage percentage, Max Marks, Description.
  - Number input for marks (0 to criterion max_marks, step 0.5).
  - Text input for faculty feedback/remarks.
- "Submit Evaluation" / "Update Evaluation" button.

**Forms / Actions**:
- `POST /examiner/evaluate/<booking_id>`: Saves individual `Evaluation` rows per rubric criterion and sets `booking.status='Completed'`.

---

### `templates/examiner/profile.html`

**Kya page render karta hai**: Examiner profile settings and contact details.

**Backend Route**: `GET /examiner/profile` -> `blueprints/examiner.py -> profile()`

**Context Variables**:
- `profile`: Current examiner's `ExaminerProfile` object.

**Key UI Sections & Features**:
- Full Name, Email (read-only), Academic Department, Phone Number.
- Save Changes button.

**Forms / Actions**:
- `POST /examiner/profile`: Updates name, department, phone number.

---

## 5. Student Module

### `templates/student/dashboard.html`

**Kya page render karta hai**: Student personal home dashboard showing upcoming exams and quick action links.

**Backend Route**: `GET /student/dashboard` -> `blueprints/student.py -> dashboard()`

**Context Variables**:
- `open_exams_count`: Exams currently open for booking.
- `my_bookings_count`: Total bookings made by this student.
- `published_results_count`: Count of evaluated exams with published results.
- `upcoming_bookings`: List of active upcoming confirmed reservations.

**Key UI Sections & Features**:
- Welcome banner with student name and roll number.
- 3 Stat Cards: Open Exams, My Bookings, Published Results.
- 3 Quick Action Cards: Browse Exams, My Schedule, View Results.
- **Upcoming Booked Exams Table**: Exam name, Date, Time, Examiner name, and "Manage" link.

---

### `templates/student/exams.html`

**Kya page render karta hai**: Candidate exam catalog to browse and search available examinations.

**Backend Route**: `GET /student/exams` -> `blueprints/student.py -> exams()`

**Context Variables**:
- `exams`: List of open examinations matching search/filters.
- `courses`: Courses list for filter dropdown.
- `booked_exam_ids`: Set of exam IDs where student already has an active reservation.
- `selected_course_id`, `search_query`: Active filter values.

**Key UI Sections & Features**:
- Search bar and Course filter dropdown.
- Exam Cards Grid:
  - Course code, Exam Name, Exam Type badge.
  - Duration and Max marks chips.
  - Booking status: "Already Booked" badge ya "Booking Open" badge.
  - "View Details & Book" button.

---

### `templates/student/exam_detail.html`

**Kya page render karta hai**: Exam summary, rubric criteria preview, and live slot booking table.

**Backend Route**: `GET /student/exam_detail/<exam_id>` -> `blueprints/student.py -> exam_detail()`

**Context Variables**:
- `exam`: Current `Examination` object with rubrics.
- `slots`: Available `ExamSlot` objects.
- `active_booking`: Student's current active booking for this exam (if any).
- `booking_open`: Boolean indicating if booking window is currently open.

**Key UI Sections & Features**:
- **Active Booking Alert**: Agar student already booked hai toh green alert banner dikhta hai with slot details and "View in My Bookings" link.
- **Exam Summary Card**: Duration, Max Marks, Booking deadline date.
- **Evaluation Criteria Table**: Preview of criteria, max marks, and weightage so students know how they will be graded.
- **Available Time Slots Table**:
  - Date, Time Window, Examiner Name & Department, Seats Left.
  - **"Book Slot"** button with confirmation popup.
  - Guard: If already booked or window closed, button is disabled with explanatory tooltip.

**Forms / Actions**:
- `POST /student/book/<slot_id>`: Atomically reserves a seat, decrements `available_seats`, creates `Booking`, and updates slot status if full.

---

### `templates/student/bookings.html`

**Kya page render karta hai**: Student complete booking history with cancellation feature.

**Backend Route**: `GET /student/bookings` -> `blueprints/student.py -> bookings()`

**Context Variables**:
- `bookings`: List of all `Booking` objects for current student.
- `now`: Current server datetime for cancellation deadline comparison.

**Key UI Sections & Features**:
- Bookings Table: Booking ID, Exam Name, Date, Time, Examiner, Status Chip (Booked, Cancelled, Completed).
- **"Cancel Booking"** button:
  - Allowed only if `booking.status == 'Booked'`.
  - Allowed only before `exam.booking_end` (cancellation deadline).
  - Automatically restores seat in `ExamSlot`.

**Forms / Actions**:
- `POST /student/cancel/<booking_id>`: Cancels reservation and increments slot's `available_seats`.

---

### `templates/student/schedule.html`

**Kya page render karta hai**: Chronological calendar-style view of upcoming confirmed exam appointments.

**Backend Route**: `GET /student/schedule` -> `blueprints/student.py -> schedule()`

**Context Variables**:
- `confirmed_bookings`: List of active `Booked` reservations sorted by exam date and start time.

**Key UI Sections & Features**:
- Clean card layout for each upcoming appointment.
- Big date badge (Day, Month, Year).
- Exam title, Course code, Duration, Examiner name & department.
- Status chip ("Confirmed Appointment").

---

### `templates/student/results.html`

**Kya page render karta hai**: Official examination scorecards with per-criterion rubric breakdown.

**Backend Route**: `GET /student/results` -> `blueprints/student.py -> results()`

**Context Variables**:
- `results_data`: List of completed exams with `evaluations` where `exam.results_published == True`.

**Key UI Sections & Features**:
- Scorecard per exam:
  - Exam Name, Course, Total Marks obtained out of Max Marks, Percentage badge.
  - Detailed Rubric Breakdown Table: Criterion Name, Max Marks, Marks Awarded, Examiner Feedback Remarks.
- Empty state with illustration if no results are published yet.

---

### `templates/student/profile.html`

**Kya page render karta hai**: Student profile settings and personal details.

**Backend Route**: `GET /student/profile` -> `blueprints/student.py -> profile()`

**Context Variables**:
- `profile`: Current student's `StudentProfile` object.

**Key UI Sections & Features**:
- Full Name, Email (read-only), Roll Number, Phone Number.
- Save Changes button.

**Forms / Actions**:
- `POST /student/profile`: Updates name, roll number, and phone number.

---

## Architecture Summary - Template Inheritance & Data Flow

```
                      base.html (Master Layout)
                         ▲
     ┌───────────────────┼───────────────────┬───────────────────┐
     │                   │                   │                   │
Error Pages         Auth Pages          Admin Pages        Examiner/Student
- 403.html          - login.html        - dashboard.html   - dashboard.html
- 404.html          - register_*.html   - courses.html     - exams.html
- 500.html                              - exams.html       - slots.html
                                        - exam_detail.html - bookings.html
                                        - examiners.html   - evaluate.html
                                        - slots.html       - results.html
                                        - bookings.html    - schedule.html
                                        - search.html      - profile.html
                                        - results.html
```

---

*Last updated: October 2026 | EMP v1.0*
