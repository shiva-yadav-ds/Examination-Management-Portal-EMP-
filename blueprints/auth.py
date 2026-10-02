from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import ExaminerProfile, User

# Public authentication controller. It owns the first browser interaction:
# registration/login writes or reads User records, then Flask-Login stores an
# authenticated session. It intentionally has no URL prefix because /login and
# /register/* are public entry URLs used before any role-specific portal exists.
auth_bp = Blueprint("auth", __name__)


# Root route.
# If the user is already authenticated, routes them directly to their role-specific dashboard.
# Otherwise redirects unauthenticated visitors to the login page.
@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif current_user.role == "examiner":
            return redirect(url_for("examiner.dashboard"))
        elif current_user.role == "student":
            return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.login"))


# Handles the common login entry point for all three roles.
#
# Request path: templates/auth/login.html POSTs ``email`` and ``password`` ->
# User is read from the users table -> the stored password hash is verified ->
# Flask-Login writes the user id to the signed session cookie -> this function
# redirects to the dashboard selected by ``user.role``. Future protected
# requests reload that user through app.load_user before decorators run.
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # Check if email exists and password hash matches
        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        # Block login if examiner is pending admin approval or user is deactivated
        if user.status != "active":
            flash("Your account is not active.", "warning")
            return render_template("auth/login.html")

        # Configure session lifetime from Config, then let Flask-Login remember
        # only this user's id. Passwords are never put in a browser cookie.
        session.permanent = True
        login_user(user, remember=True)

        # Redirect to the respective portal dashboard
        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif user.role == "examiner":
            return redirect(url_for("examiner.dashboard"))

        return redirect(url_for("student.dashboard"))

    return render_template("auth/login.html")


# Destroys current user session and redirects to the login screen.
@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# Public student registration. The form posts directly here; this server-
# rendered flow has no separate API layer. On success it creates one User row
# with role=student/status=active, saves a password hash, and redirects to login.
@auth_bp.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        roll_no = request.form.get("roll_no", "").strip()

        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("auth/register_student.html")

        # Ensure email uniqueness across all users
        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return render_template("auth/register_student.html")

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="student",
            status="active",
            phone=phone if phone else None,
            roll_no=roll_no if roll_no else None,
        )
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_student.html")


# Public examiner registration. This request writes two connected rows: User
# stores shared identity/authentication data and ExaminerProfile stores faculty
# metadata. ``flush()`` obtains user.id before commit so the profile foreign key
# can point at it. The pending status makes auth.login reject the account until
# admin.approve_examiner changes it to active.
@auth_bp.route("/register/examiner", methods=["GET", "POST"])
def register_examiner():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()
        contact = request.form.get("contact", "").strip()

        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("auth/register_examiner.html")

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return render_template("auth/register_examiner.html")

        # User row with pending status
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="examiner",
            status="pending",
        )
        db.session.add(user)
        db.session.flush()

        # Examiner profile row with department details
        profile = ExaminerProfile(
            user_id=user.id,
            department=department if department else None,
            contact=contact if contact else None,
        )
        db.session.add(profile)
        db.session.commit()

        flash("Registration submitted! Account is pending admin approval.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_examiner.html")
