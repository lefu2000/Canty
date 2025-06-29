from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import closing
import logging
import database
import os

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
app.config.update(
    DATABASE='network_configs.db',
    TEMPLATES_AUTO_RELOAD=True
)

# Constantes para mensajes de error
ERROR_MESSAGES = {
    'credentials_required': "Username and password are required",
    'invalid_credentials': "Invalid credentials",
    'server_error': "Server error occurred",
    'username_taken': "Username already taken",
    'password_length': "Password must be at least 8 characters",
    'registration_failed': "Registration failed",
    'load_devices_failed': "Could not load devices"
}

def get_db():
    """Obtiene una conexión a la base de datos con manejo de contexto."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

#def init_db():
    """Inicializa la base de datos con las tablas necesarias."""
    with app.app_context(), closing(get_db()) as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')
        db.commit()

def validate_credentials(username, password):
    """Valida que las credenciales no estén vacías."""
    return username and password

def is_authenticated():
    """Verifica si el usuario está autenticado."""
    return 'user_id' in session

@app.route('/index', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión de usuarios."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        logger.info(f"Intento de login para usuario: {username}")
        
        if not validate_credentials(username, password):
            return render_template('index.html', error=ERROR_MESSAGES['credentials_required'])
        
        try:
            with closing(get_db()) as conn:
                user = conn.execute(
                    'SELECT * FROM users WHERE username = ?', 
                    (username,)
                ).fetchone()
                
                if user and check_password_hash(user['password'], password):
                    logger.info(f"Login exitoso para usuario: {username}")
                    session.update({
                        'user_id': user['id'],
                        'username': user['username']
                    })
                    return redirect(url_for('dashboard'))
                
                return render_template('index.html', error=ERROR_MESSAGES['invalid_credentials'])
                
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            return render_template('index.html', error=ERROR_MESSAGES['server_error'])

    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Muestra el panel de control principal."""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    try:
        with closing(get_db()) as conn:
            devices = conn.execute('SELECT * FROM devices ORDER BY hostname').fetchall()
            return render_template('dashboard.html', 
                                devices=devices, 
                                username=session['username'])
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        return render_template('index.html', error=ERROR_MESSAGES['load_devices_failed'])

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Maneja el registro de nuevos usuarios."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not validate_credentials(username, password):
            return render_template('register.html', error=ERROR_MESSAGES['credentials_required'])
        
        if len(password) < 8:
            return render_template('register.html', error=ERROR_MESSAGES['password_length'])
        
        try:
            with closing(get_db()) as conn:
                if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                    return render_template('register.html', error=ERROR_MESSAGES['username_taken'])
                
                conn.execute(
                    'INSERT INTO users (username, password) VALUES (?, ?)',
                    (username, generate_password_hash(password))
                )
                conn.commit()
                return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Error en registro: {str(e)}")
            return render_template('register.html', error=ERROR_MESSAGES['registration_failed'])
    
    return render_template('register.html')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    database.init_db
    app.run(debug=True, host='0.0.0.0', port=5000)