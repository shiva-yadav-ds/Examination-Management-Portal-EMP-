# Examination Management Portal (EMP) — Overview & Complete Lifecycle Guide

Yeh document explain karta hai ki **EMP application actually kaise kaam karti hai**, iska end-to-end flow kya hai, aur browser mein ek-ek step test karke kaise verify karna hai.

---

## 1. EMP Portal Kya Hai aur Kyun Hai?

Traditional examination system mein exam conduct karna, slot schedule karna, faculty assign karna aur viva/practical ke marks dena alag-alag sheets ya emails mein hota tha. 

EMP (Examination Management Portal) ek centralized system hai jisme **3 distinct roles** hain:
1. **Admin**: Pure system ka controller (Course, Exam, Rubric, Examiner Approval, Reschedule aur Results Publish karta hai).
2. **Examiner**: Faculty member (Open exams ke liye dates & time slots schedule karta hai aur booked students ko rubric ke basis par marks/remarks deta hai).
3. **Student**: Candidate (Available exams dekhta hai, apni pasand ka date & time slot book karta hai, reschedule/cancel manage karta hai aur published scorecard dekhta hai).

---

## 2. Complete Lifecycle: Step-by-Step Flow

Pure portal ka lifecycle 8 main stages mein chalta hai. Agar kisi ko pura system samajhna hai toh isi order mein dekhna hota hai:

```
[Stage 1: Admin] Course & Examination Create karta hai (Status: Draft)
       ↓
[Stage 2: Admin] Exam mein Rubrics add karta hai aur status "Slot Creation" karta hai
       ↓
[Stage 3: Examiner] Slot Creation window mein apne Date & Time Slots create karta hai
       ↓
[Stage 4: Admin] Exam status ko "Booking Open" karta hai
       ↓
[Stage 5: Student] Slots browse karke apna slot "Book" karta hai (Seat decrement hoti hai)
       ↓
[Stage 6: Examiner] Student ko evaluate karta hai (Marks + Remarks per rubric)
       ↓
[Stage 7: Admin] Booking close karke complete evaluation ke baad exam ko Completed karta hai
       ↓
[Stage 8: Admin] "Publish Results" button dabata hai (Student scorecard unlock)
```

---

## 3. Hands-on Browser Walkthrough (Kaise Test Karein)

Agar aapko shuru se aakhir tak khud chala kar dekhna hai, toh ye sequence follow karein:

### Step 1: Admin Login & Course Creation
- URL par jao: `http://127.0.0.1:5000/login`
- Login Credentials:
  - **Email**: `admin@emp.local`
  - **Password**: `Admin@123`
- Top navbar mein **Courses** par click karein (`/admin/courses`).
- Ek naya course create karein (e.g., Code: `CS301`, Name: `Operating Systems Lab`).

### Step 2: Examination Create Karein & Rubrics Set Karein
- Navbar mein **Examinations** par click karein (`/admin/exams`).
- Form fill karein:
  - Course: `CS301`
  - Name: `OS Lab Viva Exam`
  - Type: `Viva`
  - Duration: `30` mins
  - Max Marks: `100`
- Exam create hone ke baad **Manage Exam** (`/admin/exams/<id>`) par jayein.
- **Rubrics (Evaluation Criteria) add karein**:
  - Criterion 1: `System Calls & Architecture` (Max: 50 marks)
  - Criterion 2: `Concurrency & Locking` (Max: 50 marks)
  *(Notice: Dono ka sum 100 max marks se zyada nahi ho sakta)*.
- **Exam Status change karein**:
  - `Draft` status se **"Open for Slot Creation"** button dabayein.

### Step 3: Examiner Login & Slot Creation
- Top right se **Sign out** karein.
- Examiner credentials se login karein:
  - **Email**: `priya@examiner.local`
  - **Password**: `Password@123`
- Dashboard par dikhega: `Slot Creation Open: 1`.
- Navbar mein **Open Exams** ya **My Slots -> New Slot** (`/examiner/slots/create`) par click karein.
- Exam select karein (`OS Lab Viva Exam`).
- Date pick karein (e.g., Kal ki date).
- Start time pick karein (e.g., `10:00`).
- Capacity daalein (e.g., `2` students).
- Click **Create Slot**.
- *(Notice: End time duration ke hisaab se auto 10:30 calculate ho jata hai. Agar same time par dubara slot banayenge toh system clash error dega).*

### Step 4: Admin Opens Booking
- Sign out karke wapas Admin se login karein (`admin@emp.local`).
- `/admin/exams/<id>` page par jayein.
- Status transition button dabayein: **"Open for Booking"**.
- Ab yeh exam students ko discovery page par live dikhega.

### Step 5: Student Login & Slot Booking
- Sign out karke Student login karein:
  - **Email**: `rahul@student.local`
  - **Password**: `Password@123`
  - *(Ya naya account register kar sakte hain `/register/student` se)*
- Navbar mein **Browse Exams** (`/student/exams`) par jayein.
- `OS Lab Viva Exam` ke aage **View Slots & Book** par click karein.
- Available slots ki list dikhegi. **Book Slot** button dabayein aur in-app booking modal mein confirm karein.
- Notice:
  - Slot ki available seats `2` se ghat kar `1` ho jayegi.
  - Agar available seat `0` ho jaye toh slot status automatically `Full` ho jata hai.
  - Student same exam ka dusra slot book nahi kar sakta (Duplicate protection).
  - Student ke **Schedule** (`/student/schedule`) aur **My Bookings** (`/student/bookings`) mein entry dikhne lagegi.

### Step 6: Examiner Evaluation
- Sign out karke Examiner (`priya@examiner.local`) login karein.
- **My Slots** (`/examiner/slots`) par jayein aur us slot ke aage **Students** button dabayein.
- Booked student (`Rahul Sharma`) list mein dikhega.
- **Evaluate** button dabayein:
  - System rubric criteria dikhayega (System Calls & Concurrency).
  - Har criterion ke marks daalein (e.g. `45` and `48`) aur remarks daalein.
  - Submit Evaluation karein.
- Booking status `Booked` se badal kar **`Completed`** ho jata hai.

### Step 7: Admin Publishes Results & Student Scorecard
- Admin login karein (`admin@emp.local`).
- Exam detail page (`/admin/exams/<id>`) par jayein.
- Pehle **Close Booking** confirm karein -> fir **Mark as Completed** -> fir **Publish Results** confirm karein.
- Har lifecycle action ka confirmation EMP in-app modal mein hota hai aur result top-right toast mein dikhta hai. Booking close hone ke baad stale student booking form bhi backend se reject hota hai.
- Sign out karke Student (`rahul@student.local`) login karein.
- Navbar mein **Results** (`/student/results`) par click karein:
  - Student ko uska official scorecard dikhega: Total marks (93/100) aur per-rubric break-up + faculty remarks!

---

## 4. Database Tables & Architecture Mapping

Backend SQLite database (`instance/emp.db`) mein yeh 8 core tables hain:

| Table | Model Class | Kaam |
|---|---|---|
| `users` | `User` | Sabhi users (Admin, Examiner, Student) ka base table, password hash, role, status |
| `examiner_profiles` | `ExaminerProfile` | Examiner ka department aur contact information |
| `courses` | `Course` | Academic courses (code, name, description, active status) |
| `examinations` | `Examination` | Exams (course_id, type, duration, max_marks, status, timeline dates, results_published flag) |
| `rubrics` | `Rubric` | Per-exam evaluation criteria (criterion_name, max_marks, weightage, description) |
| `exam_slots` | `ExamSlot` | Scheduled time windows (exam_id, examiner_id, date, start_time, end_time, capacity, available_seats, status) |
| `bookings` | `Booking` | Student slot reservations (student_id, exam_id, slot_id, status: Booked/Cancelled/Completed) |
| `evaluations` | `Evaluation` | Per-rubric marks obtained (booking_id, rubric_id, marks, remarks) |
