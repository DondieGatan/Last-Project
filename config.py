import os
import secrets
import warnings
from dotenv import load_dotenv

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_APP_DIR, '.env'))


def _load_or_create_dev_secret_key():
    """Fallback used only when SECRET_KEY isn't set in the environment.
    Persists a random key to a gitignored local file so it survives the
    Flask debug reloader restarting the process on every code change —
    without this, every save would silently log everyone out."""
    key_path = os.path.join(_APP_DIR, '.flask_secret_key')
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(key_path, 'w') as f:
        f.write(key)
    return key


_env_secret_key = os.environ.get('SECRET_KEY')
if not _env_secret_key:
    warnings.warn(
        'SECRET_KEY is not set in the environment — using a locally generated '
        'dev key (.flask_secret_key, gitignored). Set SECRET_KEY in your .env '
        'for a real deployment (see .env.example).',
        RuntimeWarning
    )

class Config:
    SECRET_KEY = _env_secret_key or _load_or_create_dev_secret_key()

    # Microsoft SQL Server Database Configuration
    SQL_SERVER = os.environ.get('SQL_SERVER', 'localhost')
    SQL_DATABASE = os.environ.get('SQL_DATABASE', 'smart_resume_analyser')
    SQL_DRIVER = os.environ.get('SQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
    # Use Windows Authentication by default (Trusted Connection)
    SQL_TRUSTED_CONNECTION = os.environ.get('SQL_TRUSTED_CONNECTION', 'yes')
    # Or use SQL Server Authentication
    SQL_USERNAME = os.environ.get('SQL_USERNAME', '')
    SQL_PASSWORD = os.environ.get('SQL_PASSWORD', '')

    # Upload Configuration
    # Deliberately NOT under static/ — resumes contain PII (names, emails,
    # phone numbers) and static/ is served with no auth check. Uploaded
    # files are served through the authenticated /uploads/<filename> route
    # in app.py instead, which checks the requester owns the resume.
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif', 'webp'}

    # Email Configuration (for password reset)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')

    # Resend (HTTP-based transactional email) — used instead of SMTP when
    # set, since some hosts (e.g. Render's free tier) block outbound SMTP
    # ports entirely but always allow outbound HTTPS.
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    RESEND_FROM = os.environ.get('RESEND_FROM', 'onboarding@resend.dev')

    # Password reset token expiry (seconds)
    RESET_TOKEN_EXPIRY = 3600  # 1 hour
