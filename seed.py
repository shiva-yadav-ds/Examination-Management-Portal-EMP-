from werkzeug.security import generate_password_hash

from extensions import db
from models import User


# Seeds the initial default administrator account on first application start.
# If an admin already exists in the database, this function exits without modifying anything.
def seed_admin():
    existing_admin = User.query.filter_by(role="admin").first()

    if existing_admin:
        return

    admin = User(
        name="System Admin",
        email="admin@emp.local",
        password=generate_password_hash("Admin@123"),
        role="admin",
        status="active"
    )

    db.session.add(admin)
    db.session.commit()