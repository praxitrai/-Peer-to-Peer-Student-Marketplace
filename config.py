import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core / secrets ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")

    # --- Database (MySQL via PyMySQL driver) ---
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "student_marketplace")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Session / cookie security (LO1: user & session management) ---
    # Sessions expire after 30 minutes of being "permanent" (set on login)
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True      # JS cannot read the cookie -> mitigates XSS cookie theft
    SESSION_COOKIE_SAMESITE = "Lax"     # mitigates basic CSRF via cross-site requests
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"  # HTTPS only in prod
    REMEMBER_COOKIE_HTTPONLY = True

    # --- File uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size

    # --- Misc ---
    ITEMS_PER_PAGE = 9
    RECENTLY_VIEWED_MAX = 6
