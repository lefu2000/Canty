# Módulos estándar de Python
import os
import logging
import sqlite3
from datetime import timedelta
from contextlib import closing

# Módulos de Flask y extensiones
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# Módulos locales
from database import init_db

# Configuración inicial
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de seguridad
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
csrf = CSRFProtect(app)
limiter = Limiter(app=app, key_func=get_remote_address)

# Configuración combinada
app.config.update(
    # Seguridad
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_TIME_LIMIT=3600,
    
    # Aplicación
    DATABASE='network_configs.db',
    TEMPLATES_AUTO_RELOAD=True,
    
    # Rate limiting
    DEFAULT_LIMITS=["200 per day", "50 per hour"]
)

# Constantes para mensajes de error
ERROR_MESSAGES = {
    'credentials_required': "Username and password are required",
    'invalid_credentials': "Invalid credentials",
    'server_error': "Server error occurred",
    'username_taken': "Username already taken",
    'password_length': "Password must be at least 8 characters",
    'registration_failed': "Registration failed",
    'load_devices_failed': "Could not load equipo"
}

def get_db():
    """Obtiene una conexión a la base de datos con manejo de contexto."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def validate_credentials(username, password):
    """Valida que las credenciales no estén vacías."""
    return username and password

def is_authenticated():
    """Verifica si el usuario está autenticado."""
    return 'user_id' in session

@app.route('/index', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    """Maneja el inicio de sesión de usuarios."""
    if request.method == 'POST':
        username = request.form.get('usuario', '').strip()
        password = request.form.get('contrasena', '').strip()
        
        logger.info(f"Intento de login para usuario: {username}")
        
        # Validación básica
        if not all([username, password]):
            error_msg = ERROR_MESSAGES['credentials_required']
            return handle_response(error_msg, 400)
        
        try:
            with closing(get_db()) as conn:
                user = conn.execute(
                    'SELECT id, usuario, contrasena, tipo_usuario FROM User_Login WHERE usuario = ?', 
                    (username,)
                ).fetchone()
                
                if not user:
                    logger.warning(f"Usuario no encontrado: {username}")
                    return handle_response("Usuario o contraseña incorrectos", 401)

                if not check_password_hash(user['contrasena'], password):
                    logger.warning(f"Contraseña incorrecta para usuario: {username}")
                    return handle_response("Usuario o contraseña incorrectos", 401)

                setup_user_session(user)

                if user:
                    if check_password_hash(user['contrasena'], password):
                        setup_user_session(user)
                        logger.info(f"Login exitoso para usuario: {username}")
                        return handle_response(redirect_url=url_for('dashboard'))
                    else:
                        # Contraseña incorrecta
                        return handle_response("Usuario o contraseña incorrectos", 401)
                else:
                    # Usuario no encontrado
                    return handle_response("Usuario o contraseña incorrectos", 401)
                
        except sqlite3.Error as e:
            logger.error(f"Error de BD en login: {str(e)}")
            return handle_response("Error de base de datos", 500)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return handle_response("Error del servidor", 500)

    return render_template('index.html')

# Funciones auxiliares
def get_user_by_username(conn, username):
    """Obtiene usuario de la base de datos."""
    return conn.execute(
        'SELECT id, usuario, contrasena, tipo_usuario FROM User_Login WHERE usuario = ?', 
        (username,)
    ).fetchone()

def verify_password(hashed_pw, password):
    """Verifica la contraseña con el hash almacenado."""
    return check_password_hash(hashed_pw, password)

def setup_user_session(user):
    """Configura la sesión del usuario."""
    session.clear()
    session.update({
        'user_id': user['id'],
        'usuario': user['usuario'],
        'tipo_usuario': user['tipo_usuario'],
        '_fresh': True  # Sesión fresca
    })
    session.permanent = True

def handle_response(message=None, status_code=None, redirect_url=None):
    """Maneja respuestas consistentes para AJAX y formularios."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if redirect_url:
            return jsonify({'redirect': redirect_url})
        return jsonify({'error': message}), status_code
    if redirect_url:
        return redirect(redirect_url)
    return render_template('index.html', error=message)

@app.route('/device')
def device():
    # Configuración de paginación
    page = request.args.get('page', 1, type=int)  # Página actual, default 1
    per_page = request.args.get('per_page', 10, type=int)
    if per_page not in [10, 25, 50, 100]:  # Limitar opciones
        per_page = 10 #Numero de Item por pagina
    try:
        with closing(get_db()) as conn:
            # 1. Contar el total de registros
            total_versions = conn.execute('SELECT COUNT(*) FROM Version').fetchone()[0]
            
            # 2. Calcular el offset (desplazamiento)
            offset = (page - 1) * per_page
            
            # 3. Obtener registros paginados (últimas versiones primero)
            versions = conn.execute(
                '''
                SELECT * FROM Version 
                ORDER BY fecha DESC
                LIMIT ? OFFSET ?
                ''',
                (per_page, offset)
            ).fetchall()
            
            # 4. Calcular total de páginas
            total_pages = (total_versions + per_page - 1) // per_page
            
            return render_template('layout_device.html',
                all_version=versions,
                pagination={
                    'page': page,
                    'per_page': per_page,
                    'total': total_versions,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            )
    
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        return render_template('error.html', error="Error al acceder a los datos"), 500
        
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return render_template('error.html', error="Ocurrió un error inesperado"), 500

@app.route('/dashboard')
def dashboard():
    """Muestra el panel de control principal."""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    try:
        with closing(get_db()) as conn:
            equipos = conn.execute('SELECT * FROM Equipo ORDER BY ip').fetchall()
            return render_template('dashboard_finish.html', 
                                equipos=equipos, 
                                username=session['usuario'])  # Usar 'usuario' aquí también
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
        username = request.form.get('usuario', '').strip()
        password = request.form.get('contrasena', '').strip()
        
        # Validaciones
        if not all([username, password]):
            return render_template('register.html', 
                                error=ERROR_MESSAGES['credentials_required'])
        
        if len(password) < 8:
            return render_template('register.html',
                                error=ERROR_MESSAGES['password_length'])
        
        try:
            with closing(get_db()) as conn:
                if user_exists(conn, username):
                    return render_template('register.html',
                                        error=ERROR_MESSAGES['username_taken'])
                
                create_user(conn, username, password)
                conn.commit()
                
                # Auto-login después del registro
                user = get_user_by_username(conn, username)
                setup_user_session(user)
                return redirect(url_for('dashboard'))
            
        except Exception as e:
            logger.error(f"Error en registro: {str(e)}")
            return render_template('register.html',
                                error=ERROR_MESSAGES['registration_failed'])
    
    return render_template('register.html')

def user_exists(conn, username):
    """Verifica si el usuario ya existe."""
    return conn.execute(
        'SELECT id FROM User_Login WHERE usuario = ?', 
        (username,)
    ).fetchone()

def create_user(conn, username, password):
    """Crea un nuevo usuario en la base de datos."""
    hashed_pw = generate_password_hash(
        password,
        method='pbkdf2:sha256',
        salt_length=16
    )
    conn.execute(
        'INSERT INTO User_Login (usuario, contrasena) VALUES (?, ?)',
        (username, hashed_pw)
    )

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)