from app import app, init_all

print("=" * 50)
print("ШКОЛТЕХ - Инициализация...")
print("=" * 50)

init_all()

print("Базы данных готовы")
print("Сервер запущен: http://127.0.0.1:5000")
print("Логин: GOPTAR | Пароль: goptar1")
print("=" * 50)

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)