# Examination Management Portal (EMP) - Run & Setup Guide

Yeh document explain karta hai ki **is portal ko shuru se kaise setup karna hai aur kaunsi command dekar chalana hai**.

---

## 1. Quick Start (Sirf 2 Commands Mein Run Karein)

Agar aapke paas virtual environment already ready hai (jaise abhi hai):

```bash
# Step 1: Virtual environment activate karein
source .venv/bin/activate

# Step 2: Flask application start karein
python app.py
```

Application start ho jayegi:
```text
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Ab apne browser mein open karein:
👉 **`http://127.0.0.1:5000`**

---

## 2. Complete Fresh Setup (Agar Kisi Doosre PC / Naye System Par Chalana Ho)

Agar aap kisi naye laptop ya friend ke system par pehli baar project clone/download karke chalana chahte hain:

### Step 1: Terminal mein project folder par jayein
```bash
cd examination-management-portal
```

### Step 2: Python Virtual Environment banayein
```bash
python3 -m venv .venv
```

### Step 3: Virtual Environment activate karein
- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate
  ```
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

*(Notice: Terminal prompt ke aage `(.venv)` likh kar aane lagega).*

### Step 4: Sabhi Dependencies Install Karein
```bash
pip install -r requirements.txt
```

### Step 5: Environment File Configure Karein
```bash
# Template file ko copy karke .env banayein
cp .env.example .env
```
*(Optional: Agar naya secret key banana ho toh `python -c "import secrets; print(secrets.token_hex(32))"` chala kar `.env` mein `SECRET_KEY` replace kar sakte hain).*

### Step 6: App Run Karein
```bash
python app.py
```

> **Automatic DB Seeding**: Jab aap pehli baar `python app.py` chalayenge, SQLite database (`instance/emp.db`) aur default Admin account automatically create ho jayenge. Koi alag se migration command dene ki zaroorat nahi hai.

---

## 3. Alternative Ways to Run

### Option A: `python app.py` (Recommended for Local Dev)
```bash
python app.py
```
Isme Flask ka auto-reloader aur debugger on rehta hai (koi bhi code save karne par server auto-restart ho jata hai).

### Option B: Flask CLI
```bash
flask run --port=5000 --debug
```

### Option C: Production Server (Gunicorn)
Agar cloud ya staging server par deploy karna ho:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 4. Default Login Credentials (Pre-configured Accounts)

Portal par test karne ke liye sabhi roles ke ready-to-use accounts:

| Role | Email Address | Password | Kaam / Access |
|---|---|---|---|
| **Admin** | `admin@emp.local` | `Admin@123` | System Admin (Full control) |
| **Admin** | `shubhamyadavji678@gmail.com` | `ShivA@123` | Shubham Yadav (Full admin control) |
| **Examiner** | `priya@examiner.local` | `Password@123` | Faculty (Dr. Priya Mehta) |
| **Examiner** | `vikram@emp.local` | `Password@123` | Faculty (Prof. Vikram Rao) |
| **Student** | `rahul@student.local` | `Password@123` | Student (Rahul Sharma) |

---

## 5. Naye Accounts Banana

### A. Student Account:
- Browser mein jao: `http://127.0.0.1:5000/register/student`
- Form fill karo -> Instant account activate ho jata hai -> Turant login kar sakte ho.

### B. Examiner Account:
- Browser mein jao: `http://127.0.0.1:5000/register/examiner`
- Form fill karo -> Status `pending` rahega.
- Admin account (`admin@emp.local`) se login karke `/admin/examiners` page par jao aur **"Approve"** button dabao.

### C. Naya Admin Banana (CLI Command):
```bash
# Naya admin add karein:
python manage_admin.py add "Full Name" email@example.com "Password@123"

# Example:
python manage_admin.py add "New Admin" newadmin@emp.local "AdminPass@123"

# Sabhi admins dekhne ke liye:
python manage_admin.py list

# Kisi admin ka password reset karne ke liye:
python manage_admin.py reset-password email@example.com "NewPassword@123"
```

---

## 6. Server Band Aur Restart Kaise Karein?

- **Server Rokne ke liye**: Terminal mein `Ctrl + C` dabayein.
- **Server Dubara Chalane ke liye**:
  ```bash
  python app.py
  ```
- **Virtual environment deactivate karne ke liye**:
  ```bash
  deactivate
  ```

---

## 7. Common Troubleshooting (Agar Koi Issue Aaye)

### Issue 1: "Address already in use" (Port 5000 busy hai)
Agar pehle se koi process port 5000 par chal rahi ho:
```bash
# Check karein kaunsi process chal rahi hai
lsof -i :5000

# Ya seedha kisi doosre port par chala lein
flask run --port=5001
```

### Issue 2: "ModuleNotFoundError"
Iska matlab virtual environment activate nahi hai:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue 3: Database Reset Karna (Fresh Start)
Agar aapko testing ka saara purana data clear karke fresh portal start karna ho:
```bash
# 1. Purani DB file delete karein
rm instance/emp.db

# 2. App chalayein (naya clean database auto ban jayega)
python app.py
```
*(Fresh DB banne par `admin@emp.local` / `Admin@123` auto create ho jayega).*

---

## 8. Detailed Documentation Links

- **Step-by-Step Practical Walkthrough**: [`docs/guide/00_OVERVIEW_AND_LIFECYCLE.md`](docs/guide/00_OVERVIEW_AND_LIFECYCLE.md)
- **Admin Features Guide**: [`docs/guide/01_ADMIN_GUIDE.md`](docs/guide/01_ADMIN_GUIDE.md)
- **Examiner Features Guide**: [`docs/guide/02_EXAMINER_GUIDE.md`](docs/guide/02_EXAMINER_GUIDE.md)
- **Student Features Guide**: [`docs/guide/03_STUDENT_GUIDE.md`](docs/guide/03_STUDENT_GUIDE.md)
- **Backend Code Cheat Sheet**: [`docs/guide/04_BACKEND_CODE_MAP.md`](docs/guide/04_BACKEND_CODE_MAP.md)
- **Admin CLI Tool Guide**: [`docs/guide/05_ADMIN_MANAGEMENT_CLI.md`](docs/guide/05_ADMIN_MANAGEMENT_CLI.md)

---

## 9. Verify the Current Workflow

Core regression tests run against a temporary SQLite database, so they do not alter `instance/emp.db`:

```bash
python -m unittest -v tests.test_emp_workflows
```

The suite covers booking rules, immediate Close Booking protection against stale student forms, lifecycle locking, evaluation, completion, result publication, and the lifecycle confirmation/toast markup.

For a manual admin flow, use this sequence:

1. Examiner completes every booked student's rubric evaluation.
2. Admin selects **Close Booking** and confirms in the EMP modal.
3. Admin selects **Mark as Completed**.
4. Admin selects **Publish Results**.

Each completed action redirects back to the exam detail page and shows a top-right EMP toast. No browser-native confirmation popup is used for these lifecycle actions.
