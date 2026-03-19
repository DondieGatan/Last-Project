import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-resume-analyser-secret-key-2024')

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
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
