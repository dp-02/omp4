import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-default-secret-key-for-dev')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    DATABASE_URL = os.getenv('DATABASE_URL')
    ENV = os.environ.get('FLASK_ENV') or 'development'
    PROD_HOST = '0.0.0.0' # 生產環境通常監聽所有 IP
    PROD_PORT = 8000