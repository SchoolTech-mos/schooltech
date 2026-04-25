import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'equipment')
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    USERS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')
    EQUIPMENT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'equipment.db')
    LOGS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs.db')
    
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Защита от брутфорса
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_TIMEOUT = 300  # 5 минут блокировки
    
    # CSP заголовки
    CONTENT_SECURITY_POLICY = {
        'default-src': ["'self'"],
        'img-src': ["'self'", "https://i.ibb.co", "data:"],
        'script-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'font-src': ["'self'"],
        'connect-src': ["'self'"],
        'frame-src': ["'none'"],
        'object-src': ["'none'"]
    }