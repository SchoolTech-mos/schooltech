import time
from utils import get_db_connection
from config import Config
import sqlite3

class User:
    @staticmethod
    def init_db():
        conn = get_db_connection(Config.USERS_DB)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      first_name TEXT NOT NULL,
                      last_name TEXT NOT NULL,
                      middle_name TEXT,
                      school_number TEXT NOT NULL,
                      class TEXT NOT NULL,
                      username TEXT UNIQUE NOT NULL,
                      email TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      role TEXT NOT NULL DEFAULT 'student',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        from utils import PRE_CREATED_ACCOUNTS
        for username, account_data in PRE_CREATED_ACCOUNTS.items():
            c.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if c.fetchone()[0] == 0:
                c.execute('''INSERT INTO users 
                            (first_name, last_name, middle_name, school_number, class, username, email, password, role)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (account_data['first_name'], account_data['last_name'], account_data['middle_name'],
                          account_data['school_number'], account_data['class'], username,
                          account_data['email'], account_data['password'], account_data['role']))
                print(f"✅ Создан аккаунт: {username}")
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_id(user_id):
        try:
            conn = get_db_connection(Config.USERS_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = c.fetchone()
            conn.close()
            return User._format_user(dict(user)) if user else None
        except Exception as e:
            print(f"Ошибка получения пользователя: {e}")
            return None
    
    @staticmethod
    def get_by_username(username):
        try:
            conn = get_db_connection(Config.USERS_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (username.upper(),))
            user = c.fetchone()
            conn.close()
            return User._format_user(dict(user)) if user else None
        except Exception as e:
            print(f"Ошибка: {e}")
            return None
    
    @staticmethod
    def get_all():
        try:
            conn = get_db_connection(Config.USERS_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM users ORDER BY created_at DESC")
            users = [User._format_user(dict(row)) for row in c.fetchall()]
            conn.close()
            return users
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
    
    @staticmethod
    def create(data):
        try:
            conn = get_db_connection(Config.USERS_DB)
            c = conn.cursor()
            c.execute('''INSERT INTO users 
                        (first_name, last_name, middle_name, school_number, class, username, email, password, role)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'student')''',
                     (data['first_name'], data['last_name'], data['middle_name'],
                      data['school_number'], data['class'], data['username'].upper(),
                      data['email'], data['password']))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    @staticmethod
    def update(user_id, data):
        try:
            conn = get_db_connection(Config.USERS_DB)
            c = conn.cursor()
            c.execute('''UPDATE users 
                        SET first_name = ?, last_name = ?, middle_name = ?, email = ?
                        WHERE id = ?''',
                     (data['first_name'], data['last_name'], data['middle_name'], data['email'], user_id))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    @staticmethod
    def _format_user(user_dict):
        user_dict['avatar'] = f"{user_dict['last_name'][0]}{user_dict['first_name'][0]}"
        user_dict['role_display'] = 'УЧИТЕЛЬ' if user_dict['role'] == 'teacher' else 'УЧЕНИК'
        return user_dict


class Equipment:
    @staticmethod
    def init_db():
        conn = get_db_connection(Config.EQUIPMENT_DB)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS equipment
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      description TEXT,
                      category TEXT NOT NULL,
                      school_number TEXT NOT NULL,
                      available INTEGER DEFAULT 1,
                      image_filename TEXT,
                      created_by INTEGER,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS requests
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      student_id INTEGER NOT NULL,
                      equipment_id INTEGER NOT NULL,
                      status TEXT DEFAULT 'pending',
                      due_date TEXT,
                      request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      approve_date TIMESTAMP,
                      return_date TIMESTAMP,
                      approved_by INTEGER)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS notifications
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('CREATE INDEX IF NOT EXISTS idx_equipment_school ON equipment(school_number)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_requests_student ON requests(student_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_school(school_number):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM equipment WHERE school_number = ? ORDER BY name", (school_number,))
            equipment = [dict(row) for row in c.fetchall()]
            conn.close()
            
            for item in equipment:
                item['image_path'] = f"uploads/equipment/{item['image_filename']}" if item.get('image_filename') else "images/placeholder.jpg"
                creator = User.get_by_id(item['created_by']) if item.get('created_by') else None
                item['creator_name'] = f"{creator['first_name']} {creator['last_name']}" if creator else 'Система'
            
            return equipment
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
    
    @staticmethod
    def add(data, school_number, user_id):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute('''INSERT INTO equipment 
                        (name, description, category, school_number, available, image_filename, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (data['name'].upper(), data['description'], data['category'],
                      school_number, data['available'], data.get('image_filename'), user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False


class Request:
    @staticmethod
    def create(student_id, equipment_id):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            
            c.execute("SELECT available FROM equipment WHERE id = ?", (equipment_id,))
            equipment = c.fetchone()
            if not equipment or equipment[0] <= 0:
                conn.close()
                return False
            
            c.execute("UPDATE equipment SET available = available - 1 WHERE id = ?", (equipment_id,))
            c.execute("INSERT INTO requests (student_id, equipment_id, status) VALUES (?, ?, 'pending')",
                     (student_id, equipment_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка создания заявки: {e}")
            return False
    
    @staticmethod
    def get_by_student(student_id):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute('''SELECT r.*, e.name as equipment_name, e.description as equipment_description
                        FROM requests r
                        JOIN equipment e ON r.equipment_id = e.id
                        WHERE r.student_id = ?
                        ORDER BY r.request_date DESC''', (student_id,))
            requests = [dict(row) for row in c.fetchall()]
            conn.close()
            return requests
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
    
    @staticmethod
    def get_by_school(school_number):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute('''SELECT r.*, e.name as equipment_name
                        FROM requests r
                        JOIN equipment e ON r.equipment_id = e.id
                        WHERE e.school_number = ?
                        ORDER BY r.request_date DESC''', (school_number,))
            
            requests = []
            for row in c.fetchall():
                req = dict(row)
                student = User.get_by_id(req['student_id'])
                req['student_name'] = f"{student['last_name']} {student['first_name']}" if student else 'Unknown'
                if req.get('request_date'):
                    req['request_date'] = str(req['request_date'])[:16]
                if req.get('due_date'):
                    req['due_date'] = str(req['due_date'])
                requests.append(req)
            
            conn.close()
            return requests
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
    
    @staticmethod
    def update_status(request_id, status, approved_by, due_date=None):
        for attempt in range(10):
            try:
                conn = get_db_connection(Config.EQUIPMENT_DB)
                c = conn.cursor()
                
                c.execute("BEGIN IMMEDIATE")
                
                if status == 'approved':
                    c.execute('''UPDATE requests 
                                SET status = ?, due_date = ?, approve_date = CURRENT_TIMESTAMP, approved_by = ?
                                WHERE id = ?''', (status, due_date, approved_by, request_id))
                    
                    c.execute("SELECT student_id FROM requests WHERE id = ?", (request_id,))
                    student = c.fetchone()
                    if student:
                        c.execute("INSERT INTO notifications (user_id, message) VALUES (?, ?)",
                                 (student[0], f'Заявка одобрена! Вернуть до: {due_date}'))
                
                elif status == 'returned':
                    c.execute("UPDATE requests SET status = ?, return_date = CURRENT_TIMESTAMP WHERE id = ?",
                             (status, request_id))
                    c.execute("SELECT equipment_id FROM requests WHERE id = ?", (request_id,))
                    equipment = c.fetchone()
                    if equipment:
                        c.execute("UPDATE equipment SET available = available + 1 WHERE id = ?", (equipment[0],))
                
                else:
                    c.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))
                    c.execute("SELECT equipment_id FROM requests WHERE id = ?", (request_id,))
                    equipment = c.fetchone()
                    if equipment:
                        c.execute("UPDATE equipment SET available = available + 1 WHERE id = ?", (equipment[0],))
                
                conn.commit()
                conn.close()
                return True
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < 9:
                    try:
                        conn.close()
                    except:
                        pass
                    time.sleep(0.3)
                    continue
                try:
                    conn.close()
                except:
                    pass
                return False
            except Exception as e:
                print(f"Ошибка обновления заявки: {e}")
                try:
                    conn.close()
                except:
                    pass
                return False
        
        return False


class Notification:
    @staticmethod
    def create(user_id, message):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute("INSERT INTO notifications (user_id, message) VALUES (?, ?)", (user_id, message))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка создания уведомления: {e}")
    
    @staticmethod
    def get_unread_count(user_id):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,))
            count = c.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
    
    @staticmethod
    def get_by_user(user_id):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            notifications = [dict(row) for row in c.fetchall()]
            conn.close()
            return notifications
        except Exception:
            return []
    
    @staticmethod
    def mark_as_read(notification_id):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    @staticmethod
    def mark_all_as_read(user_id):
        try:
            conn = get_db_connection(Config.EQUIPMENT_DB)
            c = conn.cursor()
            c.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass


class Log:
    @staticmethod
    def init_db():
        conn = get_db_connection(Config.LOGS_DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      action TEXT NOT NULL,
                      details TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
    
    @staticmethod
    def add(user_id, action, details=""):
        try:
            conn = get_db_connection(Config.LOGS_DB)
            c = conn.cursor()
            c.execute("INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
                     (user_id, action, details[:500]))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    @staticmethod
    def get_recent(limit=50):
        try:
            conn = get_db_connection(Config.LOGS_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT ?", (limit,))
            logs = [dict(row) for row in c.fetchall()]
            conn.close()
            
            for log in logs:
                if log['user_id']:
                    user = User.get_by_id(log['user_id'])
                    log['username'] = user['username'] if user else 'Deleted'
                    log['first_name'] = user['first_name'] if user else 'N/A'
                    log['last_name'] = user['last_name'] if user else 'N/A'
                else:
                    log['username'] = 'System'
                    log['first_name'] = 'N/A'
                    log['last_name'] = 'N/A'
            
            return logs
        except Exception:
            return []
    
    @staticmethod
    def clear():
        try:
            conn = get_db_connection(Config.LOGS_DB)
            c = conn.cursor()
            c.execute("DELETE FROM logs")
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_all():
        try:
            conn = get_db_connection(Config.LOGS_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM logs ORDER BY created_at DESC")
            logs = [dict(row) for row in c.fetchall()]
            conn.close()
            return logs
        except Exception:
            return []