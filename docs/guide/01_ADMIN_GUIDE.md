# Admin Module — Detailed Technical & Operational Guide

Yeh document Admin ke sabhi features, rules, aur unke backend code mapping ko explain karta hai.

---

## 1. Admin Ke Key Features & Capabilities

Admin pure portal ka super-user hota hai. Admin ke paas nimnlikhit shaktiyan hoti hain:

### A. Dashboard (`/admin/dashboard`)
- **Kaam**: Portal ka real-time health overview dikhana.
- **Metrics**: 
  - Total Courses, Active Examinations, Approved Examiners, Registered Students, Total Slots, Total Bookings.
  - **Alert Badge**: Agar koi naya examiner register hota hai, toh pending approval card highlight hota hai.
- **Code File**: `blueprints/admin.py` -> `dashboard()` function.
- **Template**: `templates/admin/dashboard.html`.

### B. Course Management (`/admin/courses`)
- **Kaam**: Academic courses ko create, edit aur active/inactive karna.
- **Rules**:
  - Course Code unique hona chahiye (e.g. `CS101`, `DBMS`, `MAD1`).
  - Agar kisi course ko deactivate kiya jaye, toh uske existing exams safe rehte hain lekin naye exams mein wo select nahi hota.
- **In-place Editor**: Course edit karne ke liye kisi doosre page par jane ki zaroorat nahi hai, table row ke niche hi collapsible form khulta hai.
- **Code File**: `blueprints/admin.py` -> `courses()`, `create_course()`, `edit_course()`, `toggle_course_status()`.
- **Template**: `templates/admin/courses.html`.

### C. Examiner Approvals & Management (`/admin/examiners`)
- **Kaam**: 
  - Public registration (`/register/examiner`) se aaye faculty accounts ko **Approve** ya **Reject** karna.
  - Existing examiners ko **Deactivate** ya **Reactivate** karna.
  - **Add Examiner Directly (`/admin/examiners/add`)**: Admin khud bhi examiner profile (department + contact) ke saath instant active account bana sakta hai.
- **Security Rule**: Jab tak Admin kisi examiner ko approve nahi karta, uska account `status='pending'` rehta hai aur wo login nahi kar sakta (`Your account is pending approval`).
- **Code File**: `blueprints/admin.py` -> `examiners()`, `approve_examiner()`, `toggle_examiner_status()`, `add_examiner()`.
- **Templates**: `templates/admin/examiners.html`, `templates/admin/examiners_add.html`.

### D. Examination Lifecycle & Rubrics (`/admin/exams` & `/admin/exams/<id>`)
- **Kaam**: Exams create karna, status transitions manage karna, aur rubrics jodna.
- **Exam Status Machine**:
  - `Draft` -> Initial stage (Name, Type, Duration, Max Marks edit ho sakte hain).
  - `Slot Creation` -> Examiners slots create karna shuru karte hain.
  - `Booking Open` -> Students discovery aur slot booking kar sakte hain.
  - `Booking Closed` -> New student booking aur cancellation band; booked students ki evaluation continue ho sakti hai.
  - `Completed` -> Examination khatam.
  - `Publish Results` -> `results_published = True` ho jata hai aur student dashboard par results unlock ho jate hain.
- **Rubrics Management**:
  - Har exam ke andar grading criteria add kiye jaate hain (e.g., Code Quality, Viva Knowledge).
  - **Sum Guard**: Sabhi rubrics ke max marks ka sum exam ke total `max_marks` se zyada nahi ho sakta.
  - **Delete Guard**: Agar kisi student ka evaluation ho chuka hai, toh rubric delete hona block ho jata hai (data integrity).
- **Reliability**: Close Booking, Complete, aur Publish database lifecycle lock ke saath execute hote hain. Close successful hone ke baad backend kisi bhi new student booking ko allow nahi karta.
- **Feedback**: Lifecycle buttons shared EMP confirmation modal use karte hain; success/error feedback toast ke roop mein aata hai.
- **Code File**: `blueprints/admin.py` -> `exams()`, `create_exam()`, `exam_detail()`, `open_slot_creation()`, `open_booking()`, `close_booking()`, `complete_exam()`, `publish_results()`, `add_rubric()`, `delete_rubric()`.
- **Templates**: `templates/admin/exams.html`, `templates/admin/exam_detail.html`.

### E. Slot Management & Change Examiner (`/admin/slots`)
- **Kaam**: Portal ke sabhi scheduled slots ko filter karke dekhna (by Exam, Date, Status).
- **Change Slot Examiner (Special Feature)**:
  - Admin kisi slot ka faculty change kar sakta hai (e.g., agar original faculty unavailable ho).
  - **Clash Guard**: Naye examiner ka us date aur time par koi dusra slot nahi hona chahiye.
- **Code File**: `blueprints/admin.py` -> `slots()`, `change_slot_examiner()`.
- **Template**: `templates/admin/slots.html`.

### F. Reschedule Student Booking (`/admin/bookings`)
- **Kaam**: Agar kisi student ko genuine emergency ho, toh admin uska booking kisi dusre slot par shift kar sakta hai.
- **Transaction Safety**:
  - Purane slot mein seat increment hoti hai (`available_seats + 1`).
  - Naye slot mein seat decrement hoti hai (`available_seats - 1`).
  - Agar naya slot bhar jaye toh uska status `Full` ho jata hai.
  - Agar booking already evaluate ho chuki ho (`Completed`), toh reschedule block ho jata hai.
- **Code File**: `blueprints/admin.py` -> `bookings()`, `reschedule_booking()`.
- **Template**: `templates/admin/bookings.html`.

### G. Unified Global Search (`/admin/search`)
- **Kaam**: Ek single search box se 4 alag-alag entities search karna:
  - Examiners (by Name, Email, Department)
  - Students (by Name, Email, Roll Number)
  - Examinations (by Exam Name, Course Code)
  - Bookings (by Student Name, Exam Name)
- **Code File**: `blueprints/admin.py` -> `search()`.
- **Template**: `templates/admin/search.html`.

### H. Master Results View (`/admin/results`)
- **Kaam**: Completed examinations ke sabhi students ke total score aur per-rubric detailed marks breakdown ko tabular format mein dekhna.
- **Code File**: `blueprints/admin.py` -> `results()`.
- **Template**: `templates/admin/results.html`.

### I. Naye Admin Accounts Banana (CLI Tool)
- **Kaam**: Security reasons se portal par Admin ka public registration nahi hota. Naye admins banane ya existing admin ka password reset karne ke liye root directory mein `manage_admin.py` tool diya gaya hai.
- **Detailed Guide**: Dekhein [`docs/guide/05_ADMIN_MANAGEMENT_CLI.md`](05_ADMIN_MANAGEMENT_CLI.md).
