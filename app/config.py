import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-interim-app-2024'
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # MongoDB configuration
    MONGODB_URL = os.environ.get('MONGODB_URL') or 'mongodb://localhost:27017/interim_app'
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'interim_app'
    
    # JWT configuration (optional for authentication)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-interim-app'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Pagination
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100