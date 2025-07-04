# Módulos estándar de Python
import os
import logging
import sqlite3
from datetime import timedelta
from contextlib import closing 
from functools import wraps

# Módulos de Flask y extensiones
from flask import Flask, flash, jsonify, render_template, request, redirect, url_for, session, abort, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# Módulos locales
from database import init_db, create_version

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        if session.get('tipo_usuario') != 1:  # 1 = Administrador
            abort(403)  # Prohibido
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    """Obtiene una conexión a la base de datos con manejo de contexto."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.template_filter('datetime_format')
def datetime_format(value):
    if value is None:
        return ""
    return value.strftime('%d/%m/%Y %H:%M')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    """Maneja el inicio de sesión de usuarios."""
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        username = request.form.get('usuario', '').strip()
        password = request.form.get('contrasena', '').strip()
        
        # Validación básica
        if not all([username, password]):
            error_msg = 'Usuario y contraseña son requeridos'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('login'))

        try:
            with closing(get_db()) as conn:
                user = conn.execute(
                    'SELECT id, usuario, contrasena, tipo_usuario FROM User_Login WHERE usuario = ?', 
                    (username,)
                ).fetchone()
                
                if not user or not check_password_hash(user['contrasena'], password):
                    error_msg = 'Usuario o contraseña incorrectos'
                    if is_ajax:
                        return jsonify({'success': False, 'error': error_msg}), 401
                    flash(error_msg, 'error')
                    return redirect(url_for('login'))

                setup_user_session(user)
                
                if is_ajax:
                    return jsonify({
                        'success': True,
                        'redirect': url_for('dashboard')
                    })
                return redirect(url_for('dashboard'))
                
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            error_msg = 'Error en el servidor'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 500
            flash(error_msg, 'error')
            return redirect(url_for('login'))

    return render_template('auth/login.html')

@app.route('/device')
def device():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    try:
        # Configuración de paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        device_id = request.args.get('device_id', type=int)  # Filtro por dispositivo
        
        # Validar parámetros
        per_page = 10 if per_page not in [10, 25, 50, 100] else per_page
        
        with closing(get_db()) as conn:
            # Query base con filtro opcional
            base_query = '''
                SELECT 
                    v.id, 
                    v.version, 
                    v.fecha, 
                    v.status,
                    d.name as device_name
                FROM Version v
                LEFT JOIN Device d ON v.device_id = d.id
                {where}
                ORDER BY v.fecha DESC
            '''
            
            # Construir WHERE dinámico
            where_clause = 'WHERE v.device_id = ?' if device_id else ''
            params = [device_id] if device_id else []
            
            # 1. Contar total
            count_query = f'SELECT COUNT(*) FROM Version v {where_clause}'
            total_versions = conn.execute(count_query, params).fetchone()[0]
            
            # 2. Obtener datos paginados
            offset = (page - 1) * per_page
            data_query = base_query.format(where=where_clause) + ' LIMIT ? OFFSET ?'
            versions = conn.execute(data_query, params + [per_page, offset]).fetchall()
            
            # 3. Calcular paginación
            total_pages = (total_versions + per_page - 1) // per_page
            
            # Obtener lista de dispositivos para el filtro
            devices = conn.execute('SELECT id, name FROM Device ORDER BY name').fetchall()
            
            return render_template('device.html',
                all_version=versions,
                devices=devices,
                current_device=device_id,
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
        logger.error(f"Database error: {e}")
        return render_template('error.html', error="Database operation failed"), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return render_template('error.html', error="Internal server error"), 500

@app.route('/dashboard')
@login_required
def dashboard():
    """Muestra el panel de control principal"""
    try:
        with closing(get_db()) as conn:
            # Obtener estadísticas
            total_devices = conn.execute('SELECT COUNT(*) FROM Equipo').fetchone()[0]
            active_devices = conn.execute('SELECT COUNT(*) FROM Equipo WHERE estado = "activo"').fetchone()[0]
            total_configs = conn.execute('SELECT COUNT(*) FROM Version').fetchone()[0]
            total_users = conn.execute('SELECT COUNT(*) FROM User_Login').fetchone()[0]
            
            # Obtener últimos dispositivos
            equipos = conn.execute('''
                SELECT * FROM Equipo 
                ORDER BY id DESC 
                LIMIT 10
            ''').fetchall()
            
            return render_template('dashboard_finish.html',
                                total_devices=total_devices,
                                active_devices=active_devices,
                                total_configs=total_configs,
                                total_users=total_users,
                                equipos=equipos)
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        return render_template('error.html', error="Error al cargar el dashboard")

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    if request.method == 'POST':
        usuario = request.form['usuario'].strip()
        contrasena = request.form['contrasena']
        tipo_usuario = int(request.form['tipo_usuario'])
        
        if not usuario or not contrasena:
            flash('Usuario y contraseña son requeridos', 'error')
            return redirect(url_for('manage_users'))
        
        if len(contrasena) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'error')
            return redirect(url_for('manage_users'))
        
        if create_user(usuario, contrasena, tipo_usuario):
            flash('Usuario creado exitosamente', 'success')
        else:
            flash('El nombre de usuario ya existe', 'error')
        
        return redirect(url_for('manage_users'))
    
    # GET: Mostrar lista de usuarios y formulario
    with closing(get_db()) as conn:
        users = conn.execute('''
            SELECT u.id, u.usuario, t.tipo_usuario 
            FROM User_Login u
            JOIN Tipo_usuario t ON u.tipo_usuario = t.id
            ORDER BY u.usuario
        ''').fetchall()
        
        tipos_usuario = conn.execute(
            'SELECT id, tipo_usuario FROM Tipo_usuario'
        ).fetchall()
        
    return render_template('admin_users.html', 
                         users=users, 
                         tipos_usuario=tipos_usuario)

def user_exists(conn, username):
    """Verifica si el usuario ya existe."""
    return conn.execute(
        'SELECT id FROM User_Login WHERE usuario = ?', 
        (username,)
    ).fetchone()

@app.route('/equipos')
@login_required
def list_equipos():
    """Lista todos los equipos"""
    try:
        with closing(get_db()) as conn:
            equipos = conn.execute('''
                SELECT * FROM Equipo 
                ORDER BY nombre_equipo
            ''').fetchall()
            
            return render_template('equipos/list.html', equipos=equipos)
    except Exception as e:
        logger.error(f"Error al listar equipos: {str(e)}")
        return render_template('error.html', error="Error al cargar los equipos")

@app.route('/equipos/crear', methods=['GET', 'POST'])
@login_required
def crear_equipo():
    """Crea un nuevo equipo"""
    if request.method == 'POST':
        try:
            data = {
                'acronimo': request.form['acronimo'],
                'ip': request.form['ip'],
                'nombre_equipo': request.form['nombre_equipo'],
                'modelo': request.form['modelo'],
                'proveedor': request.form['proveedor'],
                'localidad': request.form['localidad'],
                'region': request.form['region'],
                'estado': request.form.get('estado', 'inactivo')
            }
            
            with closing(get_db()) as conn:
                conn.execute('''
                    INSERT INTO Equipo 
                    (acronimo, ip, nombre_equipo, modelo, proveedor, localidad, region, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['acronimo'], data['ip'], data['nombre_equipo'],
                    data['modelo'], data['proveedor'], data['localidad'],
                    data['region'], data['estado']
                ))
                conn.commit()
                
            flash('Equipo creado exitosamente', 'success')
            return redirect(url_for('list_equipos'))
            
        except sqlite3.IntegrityError as e:
            flash('El acrónimo o la IP ya existen en el sistema', 'error')
            return redirect(url_for('crear_equipo'))
        except Exception as e:
            logger.error(f"Error al crear equipo: {str(e)}")
            flash('Error al crear el equipo', 'error')
            return redirect(url_for('crear_equipo'))
    
    # GET: Mostrar formulario
    return render_template('equipos/crear.html')

@app.route('/equipos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_equipo(id):
    """Edita un equipo existente"""
    try:
        with closing(get_db()) as conn:
            if request.method == 'POST':
                data = {
                    'id': id,
                    'acronimo': request.form['acronimo'],
                    'ip': request.form['ip'],
                    'nombre_equipo': request.form['nombre_equipo'],
                    'modelo': request.form['modelo'],
                    'proveedor': request.form['proveedor'],
                    'localidad': request.form['localidad'],
                    'region': request.form['region'],
                    'estado': request.form.get('estado', 'inactivo')
                }
                
                conn.execute('''
                    UPDATE Equipo SET
                    acronimo = ?, ip = ?, nombre_equipo = ?, modelo = ?,
                    proveedor = ?, localidad = ?, region = ?, estado = ?
                    WHERE id = ?
                ''', (
                    data['acronimo'], data['ip'], data['nombre_equipo'],
                    data['modelo'], data['proveedor'], data['localidad'],
                    data['region'], data['estado'], data['id']
                ))
                conn.commit()
                
                flash('Equipo actualizado exitosamente', 'success')
                return redirect(url_for('list_equipos'))
            
            # GET: Mostrar formulario con datos actuales
            equipo = conn.execute('SELECT * FROM Equipo WHERE id = ?', (id,)).fetchone()
            if not equipo:
                flash('Equipo no encontrado', 'error')
                return redirect(url_for('list_equipos'))
                
            return render_template('equipos/editar.html', equipo=equipo)
            
    except sqlite3.IntegrityError as e:
        flash('El acrónimo o la IP ya existen en el sistema', 'error')
        return redirect(url_for('editar_equipo', id=id))
    except Exception as e:
        logger.error(f"Error al editar equipo: {str(e)}")
        flash('Error al editar el equipo', 'error')
        return redirect(url_for('list_equipos'))

@app.route('/equipos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_equipo(id):
    """Elimina un equipo"""
    if request.method == 'POST':
        try:
            with closing(get_db()) as conn:
                conn.execute('DELETE FROM Equipo WHERE id = ?', (id,))
                conn.commit()
                
            flash('Equipo eliminado exitosamente', 'success')
        except Exception as e:
            logger.error(f"Error al eliminar equipo: {str(e)}")
            flash('Error al eliminar el equipo', 'error')
            
    return redirect(url_for('list_equipos'))

# Ruta para obtener versiones
@app.route('/api/devices/<int:device_id>/versions')
@login_required
def get_device_versions(device_id):
    versions = Version.query.filter_by(device_id=device_id).all()
    return jsonify([{
        'id': v.id,
        'version': v.version_number,
        'fecha': v.date_created.isoformat(),
        'status': 'active' if v.is_active else 'inactive'
    } for v in versions])

# Ruta para activar versión
@app.route('/api/versions/<int:version_id>/activate', methods=['POST'])
@login_required
def activate_version(version_id):
    version = Version.query.get_or_404(version_id)
    # Lógica para desactivar otras versiones y activar esta
    return jsonify({'success': True})








@app.route('/admin/users')
@admin_required
def user_management():
    """Muestra la gestión de usuarios para administradores"""
    with closing(get_db()) as conn:
        users = conn.execute('''
            SELECT u.id, u.usuario, t.tipo_usuario 
            FROM User_Login u
            JOIN Tipo_usuario t ON u.tipo_usuario = t.id
            ORDER BY u.usuario
        ''').fetchall()
        
        user_types = conn.execute(
            'SELECT id, tipo_usuario FROM Tipo_usuario'
        ).fetchall()
        
    return render_template('admin/user_management.html', 
                         users=users, 
                         user_types=user_types)

@app.route('/admin/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Crea un nuevo usuario"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        user_type = int(request.form['user_type'])
        
        # Validaciones
        if not all([username, password, password_confirm]):
            flash('Todos los campos son requeridos', 'error')
            return redirect(url_for('create_user'))
            
        if password != password_confirm:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('create_user'))
            
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'error')
            return redirect(url_for('create_user'))
            
        # Crear usuario
        if create_user_in_db(username, password, user_type):
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('user_management'))
        else:
            flash('El nombre de usuario ya existe', 'error')
            return redirect(url_for('create_user'))
    
    # GET: Mostrar formulario
    with closing(get_db()) as conn:
        user_types = conn.execute(
            'SELECT id, tipo_usuario FROM Tipo_usuario'
        ).fetchall()
        
    return render_template('admin/created_users.html', 
                         user_types=user_types)

@app.route('/download/<version>')
def download_config(version):
    if not is_authenticated():
        return redirect(url_for('login'))
    
    try:
        with closing(get_db()) as conn:
            config = conn.execute(
                'SELECT contenido FROM Version WHERE version = ?',
                (version,)
            ).fetchone()
            
            if not config:
                abort(404)
                
            # Crear respuesta de descarga
            from io import BytesIO
            mem = BytesIO(config['contenido'])
            mem.seek(0)
            
            return send_file(
                mem,
                as_attachment=True,
                download_name=f'config_{version}.bin',
                mimetype='application/octet-stream'
            )
            
    except Exception as e:
        logger.error(f"Error al descargar: {str(e)}")
        abort(500)

@app.route('/upload_version', methods=['POST'])
def upload_version():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    try:
        version_data = {
            'version': request.form['version'],
            'fecha': request.form['fecha'],
            'tamano': request.form['tamano']
        }
        
        # Obtener el archivo subido
        file = request.files['config_file']
        content = file.read()
        
        # Crear versión asociada al usuario actual
        version_id = create_version(version_data, session['user_id'], content)
        
        return redirect(url_for('device'))
    
    except Exception as e:
        logger.error(f"Error subiendo versión: {str(e)}")
        return render_template('error.html',
                            error="Error al subir versión",
                            error_code="UPLOAD_ERROR"), 500

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    if request.method == 'POST':
        # Lógica para actualizar usuario
        pass
    
    # Mostrar formulario de edición
    with closing(get_db()) as conn:
        user = conn.execute('''
            SELECT u.id, u.usuario, u.tipo_usuario 
            FROM User_Login u 
            WHERE u.id = ?
        ''', (user_id,)).fetchone()
        
        tipos_usuario = conn.execute(
            'SELECT id, tipo_usuario FROM Tipo_usuario'
        ).fetchall()
        
    if not user:
        abort(404)
        
    return render_template('edit_user.html', 
                         user=user, 
                         tipos_usuario=tipos_usuario)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('No puedes eliminarte a ti mismo', 'error')
        return redirect(url_for('manage_users'))
    
    with closing(get_db()) as conn:
        conn.execute('DELETE FROM User_Login WHERE id = ?', (user_id,))
        conn.commit()
    
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('manage_users'))

@app.route('/documentacion')
@admin_required
def documentacion():  # Nota: Nombre con mayúscula
    """Muestra la documentación del sistema"""
    return render_template('Docs.html')

@app.errorhandler(404)
def page_not_found(e):
    # Verifica si es una petición AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'Recurso no encontrado'}), 404
    return render_template('error.html', 
                        error="Página no encontrada",
                        error_code="404"), 404

@app.errorhandler(500)
def internal_server_error(e):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'Error interno del servidor'}), 500
    return render_template('error.html',
                        error="Error interno del servidor",
                        error_code="500",
                        debug=app.debug,
                        error_details=str(e)), 500

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
    """Maneja respuestas consistentes para formularios tradicionales (no AJAX)"""
    if redirect_url:
        return redirect(redirect_url)
    flash(message, 'error')
    return redirect(url_for('login'))

def validate_credentials(username, password):
    """Valida que las credenciales no estén vacías."""
    return username and password

def is_authenticated():
    """Verifica si el usuario está autenticado."""
    return 'user_id' in session

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        if session.get('tipo_usuario') != 1:  # 1 = Administrador
            abort(403)  # Prohibido
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    return redirect(url_for('login'))
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)