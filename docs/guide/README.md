# Examination Management Portal (EMP) — Comprehensive Hinglish Guide

Yeh documentation folder pure EMP portal ko deeply understand karne, browser mein live test karne, aur backend codebase ko navigate karne ke liye banaya gaya hai.

---

## 📚 Guide Index

Har document ek specific aspect ko cover karta hai:

0. **[⚡ Quick Run & Setup Guide](../../RUN_GUIDE.md)**
   - Terminal commands se project ko start kaise karein (`source .venv/bin/activate && python app.py`).
   - Fresh system par complete installation (virtualenv, pip install, .env).
   - Common troubleshooting (port busy, db reset, module errors).

0.1 **[🚀 Cloud Deployment Guide](../DEPLOYMENT_GUIDE.md)**
   - GitHub par push karne ka tareeqa.
   - Render, Railway, Vercel, PythonAnywhere par live deploy karna.
   - Production settings aur environment variables.

1. **[00. System Overview & Complete Lifecycle Guide](00_OVERVIEW_AND_LIFECYCLE.md)**
   - EMP kya hai aur kyun banaya gaya hai.
   - Teen roles (Admin, Examiner, Student) ka aapsi rishta.
   - **Step-by-step 7 Stages of Examination Lifecycle**.
   - **Hands-on Browser Walkthrough**: Kaise shuru se aakhir tak ek viva exam conduct karke result nikalna hai.
   - Database tables aur architecture.

2. **[01. Admin Module Complete Guide](01_ADMIN_GUIDE.md)**
   - Admin Dashboard metrics aur pending alert.
   - Course CRUD aur in-place collapsible editing.
   - Examiner approval, rejection, aur direct admin-add.
   - Examination creation, status lifecycle transitions, aur rubrics guards.
   - Slot management aur "Change Examiner" with clash check.
   - Student Booking Reschedule with atomic seat updates.
   - Unified Global Search (4-in-1 search).
   - Master Results view.

3. **[02. Examiner Module Complete Guide](02_EXAMINER_GUIDE.md)**
   - Examiner onboarding aur approval workflow.
   - Examiner Dashboard aur pending evaluation alerts.
   - Open exams discovery page.
   - Slot creation: automatic duration-based end-time aur time clash detection logic.
   - Slot editing aur cancellation rules.
   - Booked candidates list aur ownership guard (403).
   - Rubric-based evaluation scoring, range validation, aur upsert logic.
   - Examiner profile update.

4. **[03. Student Module Complete Guide](03_STUDENT_GUIDE.md)**
   - Student signup aur instant activation.
   - Student Dashboard aur upcoming confirmed exams.
   - Browse examinations with course/type filters and search.
   - Slot booking: double-booking guard, time clash guard, aur atomic seat decrements.
   - Booking cancellation: deadline protection, seat restoration, aur audit history.
   - My Bookings vs Chronological Schedule views.
   - Official published scorecard with rubric breakdown and faculty feedback.
   - Student profile update.

5. **[04. Backend Code Map & Developer Reference](04_BACKEND_CODE_MAP.md)**
   - Pure project ka directory tree.
   - **"Main Code Mein Kahan Dhundhu?"**: Feature-to-code cheat sheet (kaunsa route, kis file mein, kaunse function mein hai).
   - Important architectural design decisions aur viva/interview explanation points.

6. **[05. Admin Management & CLI Tool Guide](05_ADMIN_MANAGEMENT_CLI.md)**
   - Naye admin accounts kaise banaye jaate hain (`manage_admin.py`).
   - Admin passwords reset karne ka tareeqa.
   - Security reasons (Admin public signup kyun nahi hota).

7. **[Python Files Comprehensive Guide](../PYTHON_FILES.md)**
   - Saare 14 Python files ka ek-ek function, class, imports, aur interconnectivity.
   - Line numbers aur feature breakdown.

8. **[HTML Templates Comprehensive Guide](../HTML_FILES.md)**
   - Saare 33 HTML templates ka backend route, context variables, UI sections, forms aur conditional guards.

---

## 🔑 Default Test Credentials

Testing ke liye sabhi roles ke pre-seeded accounts:

| Role | Email | Password | Status |
|---|---|---|---|
| **Admin** | `admin@emp.local` | `Admin@123` | Active |
| **Admin** | `shubhamyadavji678@gmail.com` | `ShivA@123` | Active |
| **Examiner** | `priya@examiner.local` | `Password@123` | Active |
| **Examiner** | `vikram@emp.local` | `Password@123` | Active |
| **Student** | `rahul@student.local` | `Password@123` | Active |
| **Student** | `yaduvanshishubha678@gmail.com` | *(Aapka set kiya hua password)* | Active |
