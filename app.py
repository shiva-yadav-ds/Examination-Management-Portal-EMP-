import os

from flask import Flask, render_template

from config import Config
from extensions import db, login_manager


# Application factory: this is the backend's composition root.
#
# Every web request starts on the ``app`` object returned here. The factory
# creates Flask first, attaches shared extensions, then registers route groups.
# That order matters because blueprints use ``db`` and ``login_manager`` from
# extensions.py, while route functions need a configured app during requests.
# Keeping this wiring together also lets tests create an isolated application.
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance folder exists for SQLite storage
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Attach the shared objects declared in extensions.py to this Flask app.
    # Models use ``db`` to describe tables; routes use that same ``db`` to
    # query/commit. Flask-Login uses ``login_manager`` to turn the user id in a
    # signed session cookie back into ``current_user`` for each request.
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # Register route controller groups. A blueprint is not a separate app:
    # POST /student/book/<slot_id> reaches student_bp, while /login reaches
    # auth_bp. These blueprint names are also used by url_for(), for example
    # url_for("student.dashboard").
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

    # Database startup work needs an application context so SQLAlchemy knows
    # which app/configuration it belongs to. The first run creates tables from
    # models.py and seed_admin() inserts one administrator. Later runs reuse
    # existing data and leave the existing administrator unchanged.
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

    # Keep failures inside the normal EMP UI. The 500 handler also clears a
    # failed transaction so the next request does not inherit a broken session.
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


# Flask-Login calls this before each protected request. login_user() in
# auth.login stores only the user's id in the session cookie; this callback
# fetches the fresh User row and exposes it as ``current_user`` to decorators,
# blueprints, and Jinja templates. The local import avoids a circular import
# while app.py is still building the application.
@login_manager.user_loader
def load_user(user_id):
    from models import User

    return db.session.get(User, int(user_id))


# Importing ``app`` from this module gives WSGI servers (for example gunicorn)
# the fully configured application. Running this file directly uses the same
# object for local development.
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
