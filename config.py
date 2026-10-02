from datetime import timedelta
import os

from dotenv import load_dotenv

# Load environment variables from local .env file if present
load_dotenv()


# Central application configuration.
# Keeps database settings, session timeouts, and security flags in one place.
class Config:
    # Secret key used for signing session cookies and CSRF tokens
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-later"
    )

    # SQLite database location
    # On Vercel serverless environment, local filesystem is read-only except /tmp
    if os.environ.get("VERCEL"):
        DEFAULT_DB_URI = "sqlite:////tmp/emp.db"
    else:
        DEFAULT_DB_URI = "sqlite:///emp.db"

    # Support DATABASE_URL from cloud providers with postgres:// compatibility fix
    db_url = os.environ.get("DATABASE_URL", DEFAULT_DB_URI)
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cross-Site Request Forgery protection for forms
    WTF_CSRF_ENABLED = True

    # 3-Day Persistent Login Session & Cookies
    # Users remain signed in across browser restarts for 3 days
    PERMANENT_SESSION_LIFETIME = timedelta(days=3)
    REMEMBER_COOKIE_DURATION = timedelta(days=3)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Enable debug mode only in development
    DEBUG = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")