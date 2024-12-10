from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from functools import wraps
import random
from fractions import Fraction

app = Flask(__name__)
app.secret_key = 'ProyectoIntegracion2024'

# Configuración de la base de datos (importada desde config.py)
app.config.from_object('config')

# Inicialización de MySQL y Bcrypt
mysql = MySQL(app)
bcrypt = Bcrypt(app)

# Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Por favor, inicia sesión primero.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Página de inicio
@app.route('/')
def home():
    return redirect(url_for('login'))

# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        country = request.form.get('country')

        if not username or not password or not email or not phone or not country:
            flash('Por favor, completa todos los campos.', 'error')
            return redirect(url_for('register'))

        try:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor = mysql.connection.cursor()
            cursor.execute("""INSERT INTO users (username, password, email, phone, country) 
                              VALUES (%s, %s, %s, %s, %s)""", (username, hashed_password, email, phone, country))
            mysql.connection.commit()
            cursor.close()

            flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Error al registrar el usuario: {e}', 'error')

    return render_template('register.html')

# Página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Por favor, completa todos los campos.', 'error')
            return redirect(url_for('login'))

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id, password FROM users WHERE username = %s", [username])
            user = cursor.fetchone()
            cursor.close()

            if user:
                user_id, stored_password = user
                if bcrypt.check_password_hash(stored_password, password):
                    session['user'] = user_id
                    session['correct'] = 0
                    session['incorrect'] = 0
                    session.pop('correct_answer', None)
                    flash('Inicio de sesión exitoso.', 'success')
                    return redirect(url_for('menu'))
                else:
                    flash('Contraseña incorrecta.', 'error')
            else:
                flash('Usuario no encontrado.', 'error')

        except Exception as e:
            flash(f'Error al iniciar sesión: {e}', 'error')

    return render_template('login.html')

# Página del menú
@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

# Página de operaciones matemáticas
@app.route('/operation', methods=['GET', 'POST'])
@login_required
def operation():
    if 'correct' not in session:
        session['correct'] = 0
    if 'incorrect' not in session:
        session['incorrect'] = 0
    
    if request.method == 'POST':
        if 'start' in request.form:
            selected_difficulty = request.form.get('difficulty')
            
            if session.get('difficulty') != selected_difficulty:
                session['correct'] = 0
                session['incorrect'] = 0
            
            session['operation'] = request.form.get('operation')
            session['difficulty'] = selected_difficulty

        elif 'answer' in request.form:
            try:
                answer = request.form.get('answer')
                correct_answer = session.get('correct_answer')

                if '/' in answer:  
                    answer = Fraction(answer)
                else:
                    answer = float(answer)

                correct_answer = Fraction(correct_answer) if '/' in str(correct_answer) else float(correct_answer)

                if answer == correct_answer:
                    session['correct'] += 1
                    flash('¡Respuesta correcta!', 'success')
                else:
                    session['incorrect'] += 1
                    flash(f'Incorrecto. La respuesta correcta era: {correct_answer}', 'error')
            except ValueError:
                flash('Por favor, ingresa un número o fracción válido.', 'error')

        elif 'reset' in request.form:
            session['correct'] = 0
            session['incorrect'] = 0
            flash('Contadores reiniciados.', 'success')

        # Generar una nueva pregunta dependiendo de la operación
        operation = session.get('operation')
        difficulty = session.get('difficulty', 'facil')

        num_range = {
            'facil': (1, 10),
            'medio': (10, 50),
            'dificil': (50, 200)
        }[difficulty]

        # Operaciones con fracciones
        if operation in ['sumar_fraccion', 'restar_fraccion', 'multiplicar_fraccion', 'dividir_fraccion']:
            if difficulty == 'facil':
                num1 = Fraction(random.randint(1, 10), random.randint(1, 10))
                num2 = Fraction(random.randint(1, 10), random.randint(1, 10)) 
            elif difficulty == 'medio':
                num1 = Fraction(random.randint(1, 20), random.randint(1, 20)) 
                num2 = Fraction(random.randint(1, 20), random.randint(1, 20)) 
            else: 
                num1 = Fraction(random.randint(1, 50), random.randint(1, 50)) 
                num2 = Fraction(random.randint(1, 50), random.randint(1, 50))

            if operation == 'sumar_fraccion':
                correct_answer = num1 + num2
                question = f"\\( \\frac{{{num1.numerator}}}{{{num1.denominator}}} + \\frac{{{num2.numerator}}}{{{num2.denominator}}} = ? \\)"
            elif operation == 'restar_fraccion':
                correct_answer = num1 - num2
                question = f"\\( \\frac{{{num1.numerator}}}{{{num1.denominator}}} - \\frac{{{num2.numerator}}}{{{num2.denominator}}} = ? \\)"
            elif operation == 'multiplicar_fraccion':
                correct_answer = num1 * num2
                question = f"\\( \\frac{{{num1.numerator}}}{{{num1.denominator}}} \\times \\frac{{{num2.numerator}}}{{{num2.denominator}}} = ? \\)"
            elif operation == 'dividir_fraccion':
                if num2 == 0:
                    num2 = random.randint(1, num_range[1]) 
                correct_answer = num1 / num2
                question = f"\\( \\frac{{{num1.numerator}}}{{{num1.denominator}}} \\div \\frac{{{num2.numerator}}}{{{num2.denominator}}} = ? \\)"

            session['correct_answer'] = str(correct_answer)

        # Operaciones con enteros
        elif operation in ['sumar', 'restar', 'multiplicar', 'dividir']:
            num1 = random.randint(*num_range)  
            num2 = random.randint(*num_range)  

            if operation == 'sumar':
                correct_answer = num1 + num2
                question = f"{num1} + {num2} = ?"
            elif operation == 'restar':
                correct_answer = num1 - num2
                question = f"{num1} - {num2} = ?"
            elif operation == 'multiplicar':
                correct_answer = num1 * num2
                question = f"{num1} × {num2} = ?"
            elif operation == 'dividir':
                if num2 == 0:
                    num2 = random.randint(1, num_range[1]) 
                correct_answer = num1 / num2
                question = f"{num1} ÷ {num2} = ?"

            session['correct_answer'] = str(correct_answer)

        return render_template(
            'operation.html',
            question=question,
            correct=session['correct'],
            incorrect=session['incorrect'],
            operation=session.get('operation'),
            difficulty=session.get('difficulty')
        )

    return render_template('operation.html', correct=session['correct'], incorrect=session['incorrect'])

# Cerrar sesión
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
