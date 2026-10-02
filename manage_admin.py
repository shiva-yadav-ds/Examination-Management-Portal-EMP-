#!/usr/bin/env python3
"""
EMP Admin Management CLI Tool
Usage:
  python manage_admin.py list
  python manage_admin.py add "Name" email@example.com "Password@123"
  python manage_admin.py reset-password email@example.com "NewPassword@123"
"""

import sys
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import User


# Lists all registered system administrators in the database along with their active statuses.
def list_admins():
    app = create_app()
    with app.app_context():
        admins = User.query.filter_by(role="admin").all()
        print(f"\nTotal Admins: {len(admins)}")
        print("-" * 60)
        for a in admins:
            print(f"ID: {a.id:<3} | Name: {a.name:<22} | Email: {a.email:<30} | Status: {a.status}")
        print("-" * 60)


# Securely creates a new administrator account with a hashed password.
# Checks email uniqueness across all existing portal users to prevent collisions.
def add_admin(name, email, password):
    app = create_app()
    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"Error: User with email '{email}' already exists (Role: {existing.role}).")
            return False

        admin = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="admin",
            status="active"
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Success: Admin '{name}' ({email}) created successfully!")
        return True


# Resets the password for an existing administrator account.
def reset_password(email, new_password):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"Error: No user found with email '{email}'.")
            return False

        user.password = generate_password_hash(new_password)
        db.session.commit()
        print(f"Success: Password for '{email}' has been updated.")
        return True


# CLI argument parser entrypoint
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "list":
        list_admins()
    elif command == "add":
        if len(sys.argv) != 5:
            print('Usage: python manage_admin.py add "Full Name" email@domain.com "Password"')
            sys.exit(1)
        add_admin(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "reset-password":
        if len(sys.argv) != 4:
            print('Usage: python manage_admin.py reset-password email@domain.com "NewPassword"')
            sys.exit(1)
        reset_password(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command '{command}'.")
        print(__doc__)
