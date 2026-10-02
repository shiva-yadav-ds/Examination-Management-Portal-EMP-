# Student Module — Detailed Technical & Operational Guide

Yeh document Student (Candidate) ke sabhi features, rules, safety guards, aur unke backend code mapping ko explain karta hai.

---

## 1. Student Onboarding

- **Signup Page (`/register/student`)**:
  - Student apna Name, Email, Password, Roll Number, aur Phone Number enter karta hai.
  - Examiner ke ulat, **Student account instant `active` hota hai** (Admin approval ki zaroorat nahi hoti).
- **Persistent Session**:
  - Login hone par browser cookie 3 din tak session maintain karti hai.

---

## 2. Student Ke Key Features & Workflows

### A. Student Dashboard (`/student/dashboard`)
- **Kaam**: Student ko uske active aur aane wale exams ka quick summary dena.
- **Metrics**:
  - **Open Exams**: Currently kitne exams booking ke liye khule hain.
  - **My Bookings**: Student ne ab tak total kitni reservations ki hain.
  - **Published Results**: Kitne exams ke results release ho chuke hain.
- **Upcoming Booked Exams Table**:
  - Aane wale dino ke confirmed slots direct table mein dikhte hain (Exam, Date, Time, Examiner Name).
- **Code File**: `blueprints/student.py` -> `dashboard()`.
- **Template**: `templates/student/dashboard.html`.

### B. Browse Available Examinations (`/student/exams`)
- **Kaam**: Portal ke sabhi `Booking Open` exams ko search aur filter karna.
- **Filters**:
  - Filter by Course dropdown (e.g. DBMS, CS101)
  - Filter by Exam Type (Viva, Practical, Project Demo, Assessment)
  - Free-text search by Exam Name
- **Smart Status Badges**:
  - Agar student ne kisi exam ka slot already book kar rakha hai, toh button **"View Slots & Book"** ke badle **"Already Booked"** chip dikhata hai.
- **Code File**: `blueprints/student.py` -> `exams()`.
- **Template**: `templates/student/exams.html`.

### C. Exam Detail & Slot Booking (`/student/exams/<id>` & `POST /student/book/<slot_id>`)
- **Kaam**: Exam ke evaluation rubrics dekhna aur available time slots mein se pasandida slot chun kar book karna.
- **Rubrics Preview**:
  - Student exam dene se pehle dekh sakta hai ki examiner kin-kin criteria par marks dega aur unka weightage kya hai.
- **Booking Rules & Safety Guards (Backend Protected)**:
  1. **Window Guard**: Booking tabhi ho sakti hai jab locked, current exam record ka status `Booking Open` ho aur current server time booking window ke andar ho.
  2. **Seat Availability Guard**: Slot ka `available_seats > 0` aur status `Available` hona chahiye.
  3. **Duplicate Booking Guard**: Ek student ek exam ke liye sirf **ek hi active booking** rakh sakta hai. Agar wo usi exam ka dusra slot lene ki koshish karega toh reject ho jayega:
     `"You already have an active booking for this examination."`
  4. **Student Time Clash Guard**: Agar student ka usi date par koi doosra exam slot book hai jiska time naye slot se clash kar raha ho, toh booking block ho jayegi:
    `"You already have a booked slot on this date overlapping this time."`
- **Close Booking Guarantee**: Student page pe purana button dikh raha ho tab bhi POST route exam lifecycle lock ke baad current database status dobara check karta hai. Admin ke successful Close Booking ke baad new booking create nahi hoti.
- **Atomic Database Transaction**:
  - New `Booking` row insert hoti hai (`status='Booked'`).
  - Slot ki `available_seats` 1 se kam hoti hai (`slot.available_seats -= 1`).
  - Agar available seats 0 ho jayein, toh slot ka status turant **`Full`** mark ho jata hai.
- **Code File**: `blueprints/student.py` -> `exam_detail()`, `book_slot()`.
- **Template**: `templates/student/exam_detail.html`.

### D. Booking Cancellation (`POST /student/cancel/<booking_id>`)
- **Kaam**: Kisi scheduled appointment ko cancel karke seat release karna.
- **Guards**:
  1. **Ownership**: Sirf wahi student cancel kar sakta hai jiska booking hai (`403 Forbidden` if mismatched).
  2. **Deadline Protection**: Agar booking close ho chuki hai ya booking/cancellation deadline nikal chuki hai, toh cancellation block ho jata hai:
     `"Cancellation deadline has passed for this examination."`
  3. **Status Check**: Sirf `Booked` status wale records cancel ho sakte hain (Already evaluated `Completed` records cancel nahi ho sakte).
- **Seat Release & Reversion**:
  - Booking status `Cancelled` ho jata hai aur `cancelled_at` timestamp save hota hai (Audit history kabhi delete nahi hoti).
  - Slot ki `available_seats` 1 se badh jati hai.
  - Agar slot pehle `Full` tha, toh wo wapas **`Available`** ho jata hai taaki koi dusra student book kar sake.
- **Code File**: `blueprints/student.py` -> `cancel_booking()`.
- **Template**: `templates/student/bookings.html`.

### E. Reservation History (`/student/bookings`)
- **Kaam**: Student ke sabhi past aur active bookings ka comprehensive record (Booked, Cancelled, Completed).
- **Code File**: `blueprints/student.py` -> `bookings()`.
- **Template**: `templates/student/bookings.html`.

### F. Chronological Schedule (`/student/schedule`)
- **Kaam**: Student ke aane wale confirmed viva/exam appointments ko neat calendar/card format mein dekhna (Date, Time duration, Examiner, Faculty Department).
- **Code File**: `blueprints/student.py` -> `schedule()`.
- **Template**: `templates/student/schedule.html`.

### G. Official Examination Results (`/student/results`)
- **Kaam**: Published scorecards aur examiner feedback dekhna.
- **Results Visibility Rule**:
  - Student ko result tabhi dikhta hai jab:
    1. Booking status **`Completed`** ho (Examiner ne evaluate kar diya ho).
    2. Admin ne exam ka **`results_published = True`** mark kar diya ho.
- **Scorecard Breakdown**:
  - Total Marks Scored / Exam Max Marks (e.g. `93 / 100`).
  - Har Rubric Criterion ke alag marks aur percentage weightage.
  - Examiner ke remarks aur feedback (e.g., *"Good understanding of SQL indexing"*).
- **Code File**: `blueprints/student.py` -> `results()`.
- **Template**: `templates/student/results.html`.

### H. Student Profile (`/student/profile`)
- **Kaam**: Student apna Full Name, Roll Number, aur Phone Number edit kar sakta hai (Email address locked rehta hai).
- **Code File**: `blueprints/student.py` -> `profile()`.
- **Template**: `templates/student/profile.html`.
