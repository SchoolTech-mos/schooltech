from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from config import Config
from models import User, Equipment, Request, Notification, Log
from utils import get_db_connection, validate_username, validate_school_number, sanitize_input, save_uploaded_file

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

chat_messages_list = []

def init_all():
    print("=== ИНИЦИАЛИЗАЦИЯ ===")
    User.init_db()
    Equipment.init_db()
    Log.init_db()
    print("✅ Готово")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.get_by_id(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def teacher_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.get_by_id(session['user_id'])
        if not user or user['role'] != 'teacher':
            return "Доступ запрещен", 403
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@login_required
def home():
    user = User.get_by_id(session['user_id'])
    unread = Notification.get_unread_count(session['user_id'])
    return render_template('home.html', user=user, unread_count=unread)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = sanitize_input(request.form.get('first_name', '')).upper()
        last_name = sanitize_input(request.form.get('last_name', '')).upper()
        middle_name = sanitize_input(request.form.get('middle_name', '')).upper()
        school_number = sanitize_input(request.form.get('school_number', ''))
        class_name = sanitize_input(request.form.get('class', '')).upper()
        username = sanitize_input(request.form.get('username', '')).upper()
        email = sanitize_input(request.form.get('email', '')).lower()
        password = request.form.get('password', '')

        required = [first_name, last_name, school_number, class_name, username, password]
        if not all(required):
            return render_template('register.html', error='Заполните все обязательные поля')
        if not validate_username(username):
            return render_template('register.html', error='Логин от 3 до 20 символов (буквы, цифры, _)')
        if not validate_school_number(school_number):
            return render_template('register.html', error='Номер школы: 1-4 цифры')

        user_data = {
            'first_name': first_name, 'last_name': last_name, 'middle_name': middle_name,
            'school_number': school_number, 'class': class_name, 'username': username,
            'email': email if email else f"{username.lower()}@school.ru", 'password': password
        }
        user_id = User.create(user_data)
        if not user_id:
            return render_template('register.html', error='Логин или email занят')
        Log.add(user_id, 'REGISTER', username)
        session['user_id'] = user_id
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', '')).upper()
        password = request.form.get('password', '')
        if not username or not password:
            return render_template('login.html', error='Заполните все поля')
        user = User.get_by_username(username)
        if user and user['password'] == password:
            session['user_id'] = user['id']
            Log.add(user['id'], 'LOGIN')
            return redirect(url_for('home'))
        return render_template('login.html', error='Неверный логин или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        Log.add(session['user_id'], 'LOGOUT')
    session.clear()
    return redirect(url_for('login'))

@app.route('/account')
@login_required
def account():
    user = User.get_by_id(session['user_id'])
    unread = Notification.get_unread_count(session['user_id'])
    return render_template('account.html', user=user, unread_count=unread)

@app.route('/rentals')
@login_required
def rentals():
    user = User.get_by_id(session['user_id'])
    equipment = Equipment.get_by_school(user['school_number'])
    student_requests = []
    if user['role'] == 'student':
        student_requests = Request.get_by_student(session['user_id'])
    unread = Notification.get_unread_count(session['user_id'])
    return render_template('rentals.html', user=user, equipment=equipment,
                         student_requests=student_requests, unread_count=unread)

@app.route('/school')
@login_required
def school_page():
    user = User.get_by_id(session['user_id'])
    equipment = Equipment.get_by_school(user['school_number'])
    unread = Notification.get_unread_count(session['user_id'])
    return render_template('school.html', user=user, equipment=equipment, unread_count=unread)

@app.route('/get_equipment_info/<int:equipment_id>')
@login_required
def get_equipment_info(equipment_id):
    user = User.get_by_id(session['user_id'])
    equipment = Equipment.get_by_school(user['school_number'])
    item = next((i for i in equipment if i['id'] == equipment_id), None)
    if not item:
        return jsonify({'success': False})
    cats = {'technology': 'Технологии', 'biology': 'Биология', 'informatics': 'Информатика',
            'chemistry': 'Химия', 'physics': 'Физика', 'other': 'Другое'}
    return jsonify({'success': True, 'equipment': {
        'id': item['id'], 'name': item['name'],
        'description': item.get('description', ''),
        'category': cats.get(item.get('category', ''), 'Не указана'),
        'available': item.get('available', 0)
    }, 'user': {
        'full_name': f"{user['last_name']} {user['first_name']} {user.get('middle_name', '')}",
        'school': f"Школа №{user['school_number']}", 'class': user['class']
    }})

@app.route('/add_equipment', methods=['POST'])
@teacher_required
def add_equipment():
    name = sanitize_input(request.form.get('name', ''))
    description = sanitize_input(request.form.get('description', ''))
    category = request.form.get('category', 'technology')
    try:
        available = int(request.form.get('available', 1))
        if available < 1 or available > 1000:
            return jsonify({'success': False, 'error': 'Количество: 1-1000'})
    except: return jsonify({'success': False, 'error': 'Некорректное количество'})
    if not name:
        return jsonify({'success': False, 'error': 'Введите название'})
    image_filename = None
    if 'equipment_image' in request.files:
        file = request.files['equipment_image']
        if file and file.filename:
            image_filename = save_uploaded_file(file)
    user = User.get_by_id(session['user_id'])
    if Equipment.add({'name': name, 'description': description, 'category': category,
                      'available': available, 'image_filename': image_filename},
                     user['school_number'], session['user_id']):
        Log.add(session['user_id'], 'ADD_EQUIPMENT', name)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Ошибка БД'})

@app.route('/request_equipment', methods=['POST'])
@login_required
def request_equipment():
    user = User.get_by_id(session['user_id'])
    if user['role'] != 'student':
        return jsonify({'success': False, 'error': 'Только ученики'})
    try:
        eid = int(request.form.get('equipment_id', 0))
    except: return jsonify({'success': False, 'error': 'Неверный ID'})
    if Request.create(session['user_id'], eid):
        Log.add(session['user_id'], 'REQUEST_EQUIPMENT', str(eid))
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Недоступно'})

@app.route('/update_request_status', methods=['POST'])
@teacher_required
def update_request_status():
    rid = request.form.get('request_id')
    status = request.form.get('status')
    due_date = request.form.get('due_date', '')
    if not rid or status not in ['approved', 'rejected', 'returned']:
        return jsonify({'success': False, 'error': 'Некорректные данные'})
    if status == 'approved' and not due_date:
        return jsonify({'success': False, 'error': 'Укажите дату возврата'})
    if Request.update_status(int(rid), status, session['user_id'], due_date if due_date else None):
        Log.add(session['user_id'], 'UPDATE_REQUEST', f"{rid}->{status}")
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Ошибка БД'})

@app.route('/teacher_requests')
@teacher_required
def teacher_requests():
    user = User.get_by_id(session['user_id'])
    reqs = Request.get_by_school(user['school_number'])
    return jsonify({'success': True, 'requests': reqs})

@app.route('/admin')
@teacher_required
def admin_panel():
    user = User.get_by_id(session['user_id'])
    users = User.get_all()
    students = len([u for u in users if u['role'] == 'student'])
    teachers = len([u for u in users if u['role'] == 'teacher'])
    logs = Log.get_recent(50)
    unread = Notification.get_unread_count(session['user_id'])
    return render_template('admin_panel.html', user=user, student_count=students,
                         teacher_count=teachers, logs=logs, unread_count=unread)

@app.route('/admin/send_notification', methods=['POST'])
@teacher_required
def admin_send_notification():
    message = sanitize_input(request.form.get('message', ''))
    ntype = request.form.get('type', 'all')
    if not message:
        return jsonify({'success': False, 'error': 'Введите сообщение'})
    users = User.get_all()
    if ntype == 'students': target = [u for u in users if u['role'] == 'student']
    elif ntype == 'teachers': target = [u for u in users if u['role'] == 'teacher']
    else: target = users
    for u in target: Notification.create(u['id'], message)
    Log.add(session['user_id'], 'SEND_NOTIFICATION', str(len(target)))
    return jsonify({'success': True, 'message': f'Отправлено {len(target)} пользователям'})

@app.route('/admin/clear_logs', methods=['POST'])
@teacher_required
def admin_clear_logs():
    if Log.clear():
        Log.add(session['user_id'], 'CLEAR_LOGS')
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/admin/databases')
@teacher_required
def view_databases():
    user = User.get_by_id(session['user_id'])
    try:
        conn = get_db_connection(Config.EQUIPMENT_DB)
        c = conn.cursor()
        c.execute("SELECT * FROM equipment")
        eq = [dict(r) for r in c.fetchall()]
        c.execute('''SELECT r.*, u.username as student_username, e.name as equipment_name
                     FROM requests r LEFT JOIN users u ON r.student_id=u.id
                     LEFT JOIN equipment e ON r.equipment_id=e.id''')
        reqs = [dict(r) for r in c.fetchall()]
        conn.close()
    except: eq, reqs = [], []
    unread = Notification.get_unread_count(session['user_id'])
    return render_template('databases.html', user=user, users=User.get_all(),
                         equipment=eq, requests=reqs, logs=Log.get_all(), unread_count=unread)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    first_name = sanitize_input(request.form.get('first_name', '')).upper()
    last_name = sanitize_input(request.form.get('last_name', '')).upper()
    middle_name = sanitize_input(request.form.get('middle_name', '')).upper()
    email = sanitize_input(request.form.get('email', '')).lower()
    if not all([first_name, last_name, email]):
        return 'Ошибка', 400
    if User.update(session['user_id'], {'first_name': first_name, 'last_name': last_name,
                                         'middle_name': middle_name, 'email': email}):
        Log.add(session['user_id'], 'UPDATE_PROFILE')
        return 'Профиль обновлен'
    return 'Ошибка', 500

@app.route('/get_notifications')
@login_required
def get_notifications_api():
    return jsonify({'success': True, 'notifications': Notification.get_by_user(session['user_id'])})

@app.route('/mark_notification_read', methods=['POST'])
@login_required
def mark_notification_read_api():
    data = request.get_json()
    if data and 'notification_id' in data:
        Notification.mark_as_read(data['notification_id'])
    return jsonify({'success': True})

@app.route('/mark_all_notifications_read', methods=['POST'])
@login_required
def mark_all_notifications_read_api():
    Notification.mark_all_as_read(session['user_id'])
    return jsonify({'success': True})

@app.route('/chat')
@login_required
def chat():
    user = User.get_by_id(session['user_id'])
    unread = Notification.get_unread_count(session['user_id'])
    return render_template('chat.html', user=user, unread_count=unread)

@app.route('/chat/users')
@login_required
def chat_users():
    return jsonify({'success': True, 'users': User.get_all()})

@app.route('/chat/send', methods=['POST'])
@login_required
def chat_send():
    message = sanitize_input(request.form.get('message', ''))
    to_user_id = request.form.get('to_user_id', '0')
    if not message:
        return jsonify({'success': False})
    user = User.get_by_id(session['user_id'])
    chat_messages_list.append({
        'id': len(chat_messages_list) + 1,
        'user_id': session['user_id'],
        'username': user['username'],
        'to_user_id': int(to_user_id) if to_user_id and to_user_id != '0' else 0,
        'message': message,
        'created_at': __import__('datetime').datetime.now().strftime('%H:%M')
    })
    if to_user_id and to_user_id != '0':
        Notification.create(int(to_user_id), f'Новое личное сообщение от {user["username"]}')
    return jsonify({'success': True})

@app.route('/chat/messages')
@login_required
def chat_messages():
    return jsonify({'success': True, 'messages': chat_messages_list[-100:]})

@app.errorhandler(403)
def e403(e): return render_template('403.html'), 403

@app.errorhandler(404)
def e404(e): return render_template('404.html'), 404

@app.errorhandler(500)
def e500(e): return render_template('500.html'), 500

if __name__ == '__main__':
    init_all()
    app.run(debug=True, host='127.0.0.1', port=5000)