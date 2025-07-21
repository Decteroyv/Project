from flask import Flask, render_template, jsonify, session, redirect, url_for, request, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import random
from sympy import symbols, integrate, simplify, parse_expr
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2 import sql, IntegrityError

app = Flask(__name__)
app.secret_key = '456123'

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "postgres",
    "password": "1234",
    "port": "5432",
    "database": "datab1"
}

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"]
)

# Создание примеров
x = symbols('x')

def generate_math_task():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    operation = random.choice(['×', '+', '-'])

    if operation == '×':
        answer = a * b
        task = f"{a} × {b} = ?"
    elif operation == '+':
        answer = a + b
        task = f"{a} + {b} = ?"
    else:
        answer = a - b
        task = f"{a} - {b} = ?"

    return task, answer

def generate_geometry_task():
    tasks = [
        {
            'task': "Найдите площадь треугольника с основанием 10 и высотой 8",
            'figure': '''
                <svg width="200" height="200" viewBox="0 0 200 200">
                    <polygon points="100,30 30,170 170,170" fill="#e3f2fd" stroke="#2196f3" stroke-width="3"/>
                    <text x="100" y="50" text-anchor="middle" fill="#2196f3" font-size="16">a=10</text>
                    <text x="40" y="160" text-anchor="middle" fill="#2196f3" font-size="16">h=8</text>
                </svg>
            ''',
            'answer': 40
        },
        {
            'task': "Найдите площадь круга с радиусом 5 (π ≈ 3.14)",
            'figure': '''
                <svg width="200" height="200" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="80" fill="#e8f5e9" stroke="#4caf50" stroke-width="3"/>
                    <text x="100" y="100" text-anchor="middle" fill="#4caf50" font-size="16">r=5</text>
                </svg>
            ''',
            'answer': 78.5
        },
        {
            'task': "Найдите периметр прямоугольника со сторонами 6 и 4",
            'figure': '''
                <svg width="200" height="200" viewBox="0 0 200 200">
                    <rect x="40" y="60" width="120" height="80" fill="#fff3e0" stroke="#ff9800" stroke-width="3"/>
                    <text x="100" y="80" text-anchor="middle" fill="#ff9800" font-size="16">a=6</text>
                    <text x="100" y="150" text-anchor="middle" fill="#ff9800" font-size="16">b=4</text>
                </svg>
            ''',
            'answer': 20
        }
    ]
    return random.choice(tasks)

def generate_derivative_task():
    coeffs = [random.randint(1, 10) for _ in range(2)]
    powers = [random.randint(0, 3) for _ in range(2)]

    terms = []
    for c, p in zip(coeffs, powers):
        if p == 0:
            terms.append(f"{c}")
        elif p == 1:
            terms.append(f"{c} * x")
        else:
            terms.append(f"{c} * x^{p}")

    random.shuffle(terms)
    expr_str = " + ".join(terms)

    expr = parse_expr(expr_str.replace('^', '**'))
    integral = integrate(expr, x)

    task = str(simplify(expr)).replace('**', '^')
    answer = str(simplify(integral)).replace('**', '^') + " + C"

    return task, answer

def generate_integral_task():
    coeffs = [random.randint(1, 10) for _ in range(2)]
    powers = [random.randint(0, 3) for _ in range(2)]

    terms = []
    for c, p in zip(coeffs, powers):
        if p == 0:
            terms.append(f"{c}")
        elif p == 1:
            terms.append(f"{c} * x")
        else:
            terms.append(f"{c} * x^{p}")

    random.shuffle(terms)
    expr_str = " + ".join(terms)

    expr = parse_expr(expr_str.replace('^', '**'))
    integral = integrate(expr, x)

    task = str(simplify(expr)).replace('**', '^')
    answer = str(simplify(integral)).replace('**', '^') + " + C"

    return task, answer

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_db_connection():
    """Создает подключение к БД"""
    return psycopg2.connect(**DB_CONFIG)

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        """Получение пользователя по ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE id = %s", (user_id,))
        user_data = cur.fetchone()
        conn.close()
        return User(*user_data) if user_data else None

    @staticmethod
    def find_by_username(username):
        """Поиск пользователя по логину"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user_data = cur.fetchone()
        conn.close()
        return User(*user_data) if user_data else None

@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя для Flask-Login"""
    return User.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.find_by_username(username)

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))

        flash('Неверный логин или пароль', 'danger')

    return render_template('login.html')

@login_manager.unauthorized_handler
def unauthorized():
    flash('Для доступа к заданиям необходимо войти в систему', 'info')
    return redirect(url_for('login', next=request.url))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            # Увеличиваем размер поля password до 255 символов
            cur.execute("""
                INSERT INTO users (username, password) 
                VALUES (%s, %s) 
                RETURNING id
            """, (username, password))
            conn.commit()
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            flash('Это имя пользователя уже занято', 'danger')
        except Exception as e:
            flash(f'Ошибка регистрации: {str(e)}', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/zadania')
@login_required
def zadania():
    math_task, math_answer = generate_math_task()
    geometry_data = generate_geometry_task()
    derivative_task, derivative_answer = generate_derivative_task()
    integral_task, integral_answer = generate_integral_task()

    session['math_answer'] = math_answer
    session['geometry_answer'] = geometry_data['answer']
    session['derivative_answer'] = derivative_answer
    session['integral_answer'] = integral_answer

    return render_template(
        'zadania.html',
        math_task=math_task,
        geometry_task=geometry_data['task'],
        geometry_figure=geometry_data['figure'],
        derivative_task=derivative_task,
        integral_task=integral_task
    )

@app.route('/check_math_answer', methods=['POST'])
def check_math_answer():
    user_answer = request.form.get('answer')
    correct_answer = session.get('math_answer')

    try:
        is_correct = int(user_answer) == int(correct_answer)
        return jsonify({
            'correct': is_correct,
            'message': "✅ Верно!" if is_correct else "❌ Неверно!"
        })
    except ValueError:
        return jsonify({'correct': False, 'message': "Ошибка! Введите целое число."})

@app.route('/check_geometry_answer', methods=['POST'])
def check_geometry_answer():
    user_answer = request.form.get('answer')
    correct_answer = session.get('geometry_answer')

    try:
        is_correct = abs(float(user_answer) - float(correct_answer)) < 0.1
        return jsonify({
            'correct': is_correct,
            'message': "✅ Верно!" if is_correct else "❌ Неверно!"
        })
    except ValueError:
        return jsonify({'correct': False, 'message': "Ошибка! Введите число."})

@app.route('/check_derivative_answer', methods=['POST'])
def check_derivative_answer():
    user_answer = request.form.get('answer')
    correct_answer = session.get('derivative_answer')

    try:
        user_expr = parse_expr(user_answer.replace('^', '**'))
        correct_expr = parse_expr(correct_answer.replace('^', '**'))
        is_correct = simplify(user_expr - correct_expr) == 0
        return jsonify({
            'correct': is_correct,
            'message': "✅ Верно!" if is_correct else f"❌ Неверно!"
        })
    except:
        return jsonify({'correct': False, 'message': "Ошибка! Проверьте формат ввода."})

@app.route('/check_integral_answer', methods=['POST'])
def check_integral_answer():
    user_answer = request.form.get('answer')
    correct_answer = session.get('integral_answer')

    try:
        user_answer_no_c = user_answer.replace('+ C', '').replace('+C', '').strip()
        correct_answer_no_c = correct_answer.replace('+ C', '').replace('+C', '').strip()
        user_expr = parse_expr(user_answer_no_c.replace('^', '**'))
        correct_expr = parse_expr(correct_answer_no_c.replace('^', '**'))
        is_correct = simplify(user_expr - correct_expr) == 0
        return jsonify({
            'correct': is_correct,
            'message': "✅ Верно!" if is_correct else f"❌ Неверно!"
        })
    except:
        return jsonify({'correct': False, 'message': "Ошибка! Проверьте формат ввода."})

if __name__ == '__main__':
    app.run(debug=True)