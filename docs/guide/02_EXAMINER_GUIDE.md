# Examiner Module — Detailed Technical & Operational Guide

Yeh document Examiner (Faculty) ke sabhi features, rules, aur unke backend code mapping ko explain karta hai.

---

## 1. Examiner Account Kaise Banta Hai?

Examiner account do tareeqon se ban sakta hai:
1. **Self Signup (`/register/examiner`)**:
   - Faculty apna Name, Email, Password, Department, aur Contact daal kar register karta hai.
   - Status automatically **`pending`** set hota hai.
   - Examiner login tabhi kar payega jab Admin `/admin/examiners` se usko **Approve** karega.
2. **Admin Direct Creation (`/admin/examiners/add`)**:
   - Admin sidha faculty banata hai. Ye account instant **`active`** hota hai.

---

## 2. Examiner Ke Key Features & Workflows

### A. Examiner Dashboard (`/examiner/dashboard`)
- **Kaam**: Faculty ko uski responsibility ka overview dena.
- **Metrics**:
  - **Slot Creation Open**: Kitne exams abhi slots accept kar rahe hain.
  - **My Slots**: Examiner ke banaye huye active slots.
  - **Booked Candidates**: Examiner ke slots mein kul kitne students book ho chuke hain.
  - **Pending Evaluations (Action Required)**: Agar exam ki date nikal gayi hai ya aaj ki hai aur student ke marks submit nahi huye, toh card red alert ban kar highlight hota hai.
- **Code File**: `blueprints/examiner.py` -> `dashboard()`.
- **Template**: `templates/examiner/dashboard.html`.

### B. Open Exams Discovery (`/examiner/exams`)
- **Kaam**: Un sabhi exams ki list dekhna jinka status `Slot Creation` hai.
- **Details**: Course Code, Exam Type, Duration (mins), Max Marks, Slot Creation Window Deadline.
- **Direct Action**: Har exam ke aage **"Add Slot"** button hota hai jo directly exam pre-select karke slot creation form par le jata hai.
- **Code File**: `blueprints/examiner.py` -> `exams()`.
- **Template**: `templates/examiner/exams.html`.

### C. Slot Creation (`/examiner/slots/create`)
- **Kaam**: Examination ke liye date aur time schedule karna.
- **Form Fields**:
  - Exam selection dropdown
  - Date picker
  - Start Time picker
  - Capacity (Max kitne students ek slot mein baith sakte hain)
- **Automatic End-Time Calculation**:
  - Examiner ko end-time manually nahi daalna padta.
  - Backend exam duration (e.g. 30 mins) ko start time mein jod kar `end_time` automatically calculate karta hai:
    `end_dt = start_dt + timedelta(minutes=exam.duration)`
- **Clash Detection Guard (Backend)**:
  - Ek examiner same date par overlapping time par do slots nahi bana sakta.
  - Backend query check karti hai:
    `slot.start_time < new_end_time AND slot.end_time > new_start_time`
  - Agar overlap ho, toh submission reject ho jata hai: `"You already have a slot scheduled that overlaps with this time."`
- **Code File**: `blueprints/examiner.py` -> `create_slot()`.
- **Template**: `templates/examiner/create_slot.html`.

### D. Slot Management, Edit & Delete (`/examiner/slots`)
- **Kaam**: Apne sabhi slots ka status dekhna (Available / Full / Completed) aur modify karna.
- **Edit Rules**:
  - Examiner slot ki Date, Time ya Capacity change kar sakta hai.
  - **Guard**: Edit tabhi allowed hai jab tak booking window shuru na hui ho aur kisi student ne book na kiya ho.
- **Delete (Cancel) Rules**:
  - Examiner slot delete kar sakta hai.
  - **Guard**: Agar slot mein active bookings (`status = 'Booked'`) hain, toh deletion block ho jata hai taaki student ki booking na toote.
- **Code File**: `blueprints/examiner.py` -> `slots()`, `edit_slot()`, `delete_slot()`.
- **Template**: `templates/examiner/slots.html`.

### E. Booked Candidates List (`/examiner/slots/<id>/students`)
- **Kaam**: Kisi particular slot mein kis-kis student ne book kiya hai wo dekhna.
- **Ownership Security Guard**:
  - Agar Examiner A kisi aise slot ko kholne ki koshish kare jo Examiner B ka hai, toh backend turant **403 Forbidden** fek deta hai:
    `if slot.examiner_id != current_user.id: abort(403)`
- **Evaluation Availability**:
  - Slot owner booked candidate ko evaluate kar sakta hai. Publication ke baad evaluations lock ho jaati hain.
- **Code File**: `blueprints/examiner.py` -> `slot_students()`.
- **Template**: `templates/examiner/students.html`.

### F. Rubric Evaluation Submission (`/examiner/evaluate/<booking_id>`)
- **Kaam**: Student ke viva/practical ke marks aur remarks submit karna.
- **Dynamic Rubric Scoring**:
  - Exam ke admin dwara banaye gaye sabhi rubric criteria dynamic form ke roop mein aate hain.
  - Har criterion ke aage uska Max Marks aur Weightage show hota hai.
- **Validation Rules**:
  - `0 <= marks <= rubric.max_marks` (agar max 50 hai toh 51 daalne par backend error dega).
- **Database Upsert**:
  - Agar pehle marks submit kiye the aur faculty update kar raha hai, toh row update hoti hai; naya evaluation hai toh insert hoti hai (`UniqueConstraint('booking_id', 'rubric_id')`).
- **Status Progression**:
  - Marks submit hote hi booking ka status `Booked` se badal kar **`Completed`** ho jata hai.
- **Lifecycle Safety**:
  - POST evaluation exam lifecycle lock ke under save hota hai, isliye completion/publication ke saath stale write race nahi hoti.
- **Code File**: `blueprints/examiner.py` -> `evaluate()`.
- **Template**: `templates/examiner/evaluate.html`.

### G. Examiner Profile (`/examiner/profile`)
- **Kaam**: Apna Name, Department aur Contact number update karna.
- **Code File**: `blueprints/examiner.py` -> `profile()`.
- **Template**: `templates/examiner/profile.html`.
