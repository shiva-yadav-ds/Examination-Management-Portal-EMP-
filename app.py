import os

from flask import Flask, render_template

from config import Config
from extensions import db, login_manager


# Application factory function.
# Initializes Flask extensions, registers blueprints, creates tables, and sets up error handlers.
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance folder exists for SQLite storage
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize database and login session manager
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # Register blueprints for modular route handling
    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.examiner import examiner_bp
    from blueprints.student import student_bp
    from blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(examiner_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(api_bp)

    # Initialize tables and seed initial admin on first run
    with app.app_context():
        from models import (
            User,
            ExaminerProfile,
            Course,
            Examination,
            Rubric,
            ExamSlot,
            Booking,
            Evaluation,
        )

        db.create_all()

        from seed import seed_admin
        seed_admin()

    # Custom HTTP error pages
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Roll back any broken transactions to keep SQLite session healthy
        db.session.rollback()
        return render_template("500.html"), 500

    return app


# Flask-Login user loader callback.
# Fetches the user record from the database using the user ID stored in the session cookie.
@login_manager.user_loader
def load_user(user_id):
    from models import User

    return db.session.get(User, int(user_id))


# Create app instance for WSGI servers (e.g. gunicorn) and local execution
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)