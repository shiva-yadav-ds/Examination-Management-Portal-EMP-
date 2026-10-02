from functools import wraps

from flask import abort
from flask_login import current_user


# Custom decorator for role-based access control (RBAC).
# Verifies that the user is logged in (401 if unauthenticated) and
# belongs to one of the authorized roles (403 if unauthorized).
def role_required(*roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            # Check if user has an active session
            if not current_user.is_authenticated:
                abort(401)

            # Check if user role matches one of the allowed roles
            if current_user.role not in roles:
                abort(403)

            if getattr(current_user, "status", None) != "active":
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator
