import re
import sqlite3
import time
from threading import Lock
from werkzeug.utils import secure_filename
from config import Config
import os

db_locks = {
    Config.USERS_DB: Lock(),
    Config.EQUIPMENT_DB: Lock(),
    Config.LOGS_DB: Lock()
}

def get_db_connection(db_path):
    """Подключение к базе данных с таймаутом"""
    for attempt in range(20):
        try:
            conn = sqlite3.connect(db_path, timeout=60.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA cache_size = -20000")
            return conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < 19:
                time.sleep(0.3)
                continue
            raise e
    
    raise sqlite3.OperationalError(f"Could not connect to {db_path}")

def validate_username(username):
    if not username or len(username) < 3 or len(username) > 20:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

def validate_email(email):
    if not email or len(email) > 254:
        return False
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def validate_school_number(school_number):
    if not school_number:
        return False
    return bool(re.match(r'^\d{1,4}$', school_number))

def validate_class_name(class_name):
    if not class_name:
        return False
    return 1 <= len(class_name.strip()) <= 10

def sanitize_input(text):
    if not text:
        return ""
    text = re.sub(r'[<>{}]', '', text)
    return text.strip()[:500]

def save_uploaded_file(file):
    if not file or not file.filename:
        return None
    
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in Config.ALLOWED_EXTENSIONS:
        return None
    
    import uuid
    new_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, new_filename)
    
    if not os.path.abspath(filepath).startswith(os.path.abspath(Config.UPLOAD_FOLDER)):
        return None
    
    file.save(filepath)
    return new_filename

PRE_CREATED_ACCOUNTS = {
    'GOPTAR': {
        'password': 'goptar1',
        'first_name': 'ЕВГЕНИЙ',
        'last_name': 'ГОПТАРЬ',
        'middle_name': 'АНДРЕЕВИЧ',
        'school_number': '2098',
        'class': 'УЧИТЕЛЬ',
        'email': 'goptar@yandex.ru',
        'role': 'teacher'
    }
}