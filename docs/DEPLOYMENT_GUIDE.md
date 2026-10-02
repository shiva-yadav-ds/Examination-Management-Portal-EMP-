# Examination Management Portal (EMP) - Deployment Guide

Yeh guide explain karti hai ki EMP project ko **GitHub par kaise push karein** aur **live cloud platforms (Render, Railway, Vercel, PythonAnywhere) par kaise deploy karein** bina kisi issue ke.

---

## 1. Important: Platforms Ka Difference Samajhein

Deployment se pehle yeh technical farq samajhna zaroori hai:

| Platform | Type | Kya EMP chal sakta hai? | Notes |
|---|---|---|---|
| **GitHub Repo** | Code Hosting | ✅ Yes | Code store karne aur version control ke liye perfect hai. |
| **GitHub Pages** | Static Website Hosting | ❌ No | GitHub Pages sirf static HTML/CSS/JS chalata hai. Isme Python backend ya SQLite database run nahi hota. |
| **Netlify** | JAMstack / Static | ❌ Not Recommended | Netlify frontend static sites ke liye hai, long-running Python Flask servers ke liye nahi. |
| **Render.com** | Full Cloud Web Service | ⭐ **BEST & RECOMMENDED** | Free tier available. Python + Gunicorn + SQLite ko 1-click mein chalata hai. |
| **Railway.app** | Cloud Container Platform | ⭐ **EXCELLENT** | Automatic GitHub connect, zero config, fast deployment. |
| **PythonAnywhere** | Dedicated Python Host | ⭐ **GREAT FOR STUDENTS** | Built specifically for Flask/Django + SQLite. |
| **Vercel** | Serverless Cloud | ✅ Supported | Humne `vercel.json` add kar diya hai. Vercel par serverless Python chalta hai (Note: serverless mein local SQLite `/tmp` mein rehta hai). |

---

## 2. Step 1: Code Ko GitHub Par Push Karein

Aapka `.gitignore` pehle se configured hai taaki koi secret ya `.venv` push na ho.

Terminal mein yeh commands run karein:

```bash
# 1. Sabhi project files ko stage karein
git add .

# 2. Pehla commit banayein
git commit -m "Initial commit: Examination Management Portal (EMP)"

# 3. GitHub par naya repository banayein (https://github.com/new)
# Example repo URL: https://github.com/your-username/examination-management-portal.git

# 4. Apne GitHub repository ko remote add karein
git remote add origin https://github.com/your-username/examination-management-portal.git

# 5. Branch ko main set karein aur push karein
git branch -M main
git push -u origin main
```

> **Security Note**: Aapka `.env` file aur local database (`instance/emp.db`) automatically ignore rahenge. Sirf `.env.example` push hoga, jisse aapke private secrets safe rahenge.

---

## 3. Step 2: Render.com Par Live Deploy Karein (Recommended)

Render par Flask app deploy karna sabse aasan aur reliable hai:

1. **Render par account banayein**: [render.com](https://render.com) par jayein aur "Sign Up with GitHub" karein.
2. **Naya Web Service create karein**:
   - Dashboard mein **New +** button dabayein -> **Web Service** select karein.
   - Apni GitHub repository choose karein.
3. **Settings fill karein**:
   - **Name**: `examination-portal` (ya apni pasand ka naam)
   - **Region**: `Singapore` ya `Frankfurt` (closest to you)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
   - **Instance Type**: `Free`
4. **Environment Variables Add Karein** (Environment Tab mein):
   - `SECRET_KEY`: `(kisi random string ya python secrets.token_hex(32) ka output daalein)`
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `0`
5. **Deploy**:
   - **Create Web Service** button dabayein.
   - Render automatically dependencies install karega aur app ko live URL de dega (e.g. `https://examination-portal.onrender.com`).

---

## 4. Step 3: Vercel Par Deploy Karein

Agar aap Vercel use karna chahte hain:

Humne project mein already [`vercel.json`](../vercel.json) aur [`wsgi.py`](../wsgi.py) ready kar diya hai.

### Option A: Vercel Web Dashboard se
1. [vercel.com](https://vercel.com) par login karein via GitHub.
2. **Add New...** -> **Project** par click karein.
3. Apni GitHub repository import karein.
4. **Environment Variables** mein add karein:
   - `SECRET_KEY`: `(Aapka secret key)`
   - `FLASK_ENV`: `production`
5. **Deploy** button click karein. Vercel `@vercel/python` se WSGI build karke deploy kar dega.

### Option B: Vercel CLI se
```bash
# Vercel CLI install karein
npm i -g vercel

# Deploy command
vercel
```

---

## 5. Step 4: Railway.app Par Deploy Karein

1. [railway.app](https://railway.app) par login karein via GitHub.
2. **New Project** -> **Deploy from GitHub repo** select karein.
3. Railway automatically `Procfile` aur `requirements.txt` detect karke `gunicorn wsgi:app` start kar dega.
4. Settings mein jaakar **Generate Domain** click karein taaki public live link mil sake.

---

## 6. Pre-configured Deployment Files Checklist

Aapke project mein deployment ke liye sabhi required files pehle se configured hain:

- ✅ **`Procfile`**: `web: gunicorn wsgi:app` (Render, Railway, Heroku ke liye).
- ✅ **`wsgi.py`**: Production WSGI entry point.
- ✅ **`vercel.json`**: Vercel serverless Python routing rules.
- ✅ **`runtime.txt`**: Python 3.12 version declaration.
- ✅ **`requirements.txt`**: All pinned packages including `gunicorn` and `python-dotenv`.
- ✅ **`config.py`**:
  - `postgres://` to `postgresql://` auto-compatibility fix.
  - Vercel serverless `/tmp` database path fallback.
  - Safe production `DEBUG` toggle.
- ✅ **`app.py`**:
  - `os.makedirs(app.instance_path, exist_ok=True)` taaki fresh server par SQLite crash na ho.
  - Automatic DB creation and admin seeding on initial boot.
- ✅ **`.gitignore`**: Secrets, virtual environments, aur local caches excluded.

---

## 7. Production Post-Deployment Verification

App deploy hone ke baad yeh test karein:
1. Live URL open karein: Login page open hona chahiye (`/login`).
2. Default credentials se login karein:
   - Email: `admin@emp.local`
   - Password: `Admin@123`
3. Student self-registration test karein (`/register/student`).
4. Ek test exam aur slot check karein.
