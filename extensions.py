from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Shared extension instances.
# Declared separately from app.py to avoid circular import issues across blueprints and models.
db = SQLAlchemy()
login_manager = LoginManager()