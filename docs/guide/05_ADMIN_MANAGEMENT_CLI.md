# Admin Management & Onboarding Guide — EMP

Yeh document explain karta hai ki **Examination Management Portal mein naye Admin kaise banaye jaate hain**, unka password kaise reset hota hai, aur CLI tool ka use kaise kiya jata hai.

---

## 1. Security Architecture: Admin Public Signup Kyun Nahi Hota?

Portal ke landing aur login page par do tarah ke public registration available hain:
- **Student Registration (`/register/student`)**: Koi bhi student apna account bana kar exams browse kar sakta hai.
- **Examiner Registration (`/register/examiner`)**: Faculty register karti hai, lekin account `pending` rehta hai jab tak Admin use approve na kare.

Lekin **Admin ke liye koi public registration URL nahi hota**. 
- **Reason**: Agar koi bhi bahar ka user website par sign-up karke Admin ban sake, toh wo poore portal ke courses, exam rubrics, scheduled slots, aur student ke marks ko alter kar sakta hai.
- Isliye standard production architecture mein naye Admins sirf **Backend CLI Tool** ya **Existing Authorized Admin** ke through hi add kiye jaate hain.

---

## 2. Admin Management CLI Tool (`manage_admin.py`)

Humne root directory mein ek dedicated CLI management script provide ki hai: [`manage_admin.py`](file:///home/sy-ds/examination-management-portal/manage_admin.py).

Yeh tool direct terminal se safe database operations perform karta hai aur password ko secure salt hash (`generate_password_hash`) ke saath store karta hai.

### A. Sabhi Admins Ki List Dekhna

Terminal mein run karein:
```bash
python manage_admin.py list
```

**Output example:**
```text
Total Admins: 2
------------------------------------------------------------
ID: 1   | Name: System Admin           | Email: admin@emp.local                | Status: active
ID: 8   | Name: Shubham Yadav          | Email: shubhamyadavji678@gmail.com    | Status: active
------------------------------------------------------------
```

---

### B. Naya Admin Add Karna

Terminal mein run karein:
```bash
python manage_admin.py add "<Full Name>" <email_address> "<Password>"
```

**Example:**
```bash
python manage_admin.py add "Shubham Yadav" shubhamyadavji678@gmail.com "ShivA@123"
```

**Output:**
```text
Success: Admin 'Shubham Yadav' (shubhamyadavji678@gmail.com) created successfully!
```

Naya account banne ke saath hi:
- Role automatically `admin` set hota hai.
- Status directly `active` hota hai.
- Password sha256 encrypted format mein database table `users` mein store hota hai.
- User turant `http://127.0.0.1:5000/login` par ja kar login kar sakta hai.

---

### C. Kisi Admin Ka Password Reset Karna

Agar koi admin apna password bhool jaye:
```bash
python manage_admin.py reset-password <email_address> "<NewPassword>"
```

**Example:**
```bash
python manage_admin.py reset-password shubhamyadavji678@gmail.com "NewPassword@123"
```

**Output:**
```text
Success: Password for 'shubhamyadavji678@gmail.com' has been updated.
```

---

## 3. Currently Active Admins

Abhi database mein nimnlikhit do active admin accounts configured hain:

| ID | Name | Email | Default Password | Role | Status |
|---|---|---|---|---|---|
| 1 | System Admin | `admin@emp.local` | `Admin@123` | admin | active |
| 8 | Shubham Yadav | `shubhamyadavji678@gmail.com` | `ShivA@123` | admin | active |

---

## 4. Code Implementation Detail

Agar aapko dekhna hai ki yeh CLI tool backend mein kaise kaam karta hai:
- **File**: [`manage_admin.py`](file:///home/sy-ds/examination-management-portal/manage_admin.py)
- **Logic**:
  1. `from app import create_app` aur `from extensions import db` se Flask application context start karta hai.
  2. `from models import User` se User table query karta hai.
  3. Werkzeug ki `generate_password_hash()` library use karke plain text password ko cryptographic hash mein convert karke commit karta hai.
  4. Duplicate email validation check karta hai taaki existing student ya examiner ka email clash na ho.
