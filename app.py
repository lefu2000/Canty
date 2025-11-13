# Módulos estándar de Python
import os
import logging
import sqlite3
from datetime import datetime, timedelta
from contextlib import closing 
from functools import wraps
from contextlib import closing
import socket


# Módulos de Flask y extensiones
from flask import Flask, flash, jsonify, render_template, request, redirect, url_for, session, abort, send_file, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_login import login_required, current_user

# Módulos locales
from database import init_db, create_version, create_user_db

# Configuración inicial
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Después de crear la app Flask
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Especifica la vista de login

# Configuración de seguridad
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
csrf = CSRFProtect(app)
limiter = Limiter(app=app, key_func=get_remote_address)

#Llamado a las configuraciones
app.config.from_object('config.Config')

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

class User(UserMixin):
    def __init__(self, user_id, username, user_type):
        self.id = user_id
        self.username = username
        self.user_type = user_type
        
    @property
    def is_admin(self):
        return self.user_type == 1 # Asumiendo que 1 es el tipo para admin
    
@login_manager.user_loader
def load_user(user_id):
    with closing(get_db()) as conn:
        user = conn.execute(
            'SELECT id, usuario, tipo_usuario FROM User_Login WHERE id = ?', 
            (user_id,)
        ).fetchone()
        if user:
            return User(user['id'], user['usuario'], user['tipo_usuario'])
    return None

# Para rutas de admin
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Prohibido
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    """Obtiene una conexión a la base de datos con manejo de contexto."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.template_filter('datetime_format')
def datetime_format(value):
    if value is None:
        return ""
    return value.strftime('%d/%m/%Y %H:%M')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    """Maneja el inicio de sesión de usuarios."""
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        username = request.form.get('usuario', '').strip()
        password = request.form.get('contrasena', '').strip()

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
                
                # Crear objeto User para Flask-Login
                user_obj = User(
                    user_id=user['id'],
                    username=user['usuario'],
                    user_type=user['tipo_usuario']
                )
                
                # Iniciar sesión con Flask-Login
                login_user(user_obj)
                
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
                ORDER BY nombre_equipo DESC 
                LIMIT 10
            ''').fetchall()
            
            return render_template('dashboard.html',
                                total_devices=total_devices,
                                active_devices=active_devices,
                                total_configs=total_configs,
                                total_users=total_users,
                                equipos=equipos)
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        return render_template('error.html', error="Error al cargar el dashboard")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def user_exists(conn, username):
    """Verifica si el usuario ya existe."""
    return conn.execute(
        'SELECT id FROM User_Login WHERE usuario = ?', 
        (username,)
    ).fetchone()

@app.route('/list_device')
@login_required
def list_device():
    """Lista todos los equipos"""
    try:
        with closing(get_db()) as conn:
            equipos = conn.execute('''
                SELECT * FROM Equipo 
                ORDER BY nombre_equipo DESC
                LIMIT 10
            ''').fetchall()
            
            return render_template('equipos/list_device.html', equipos=equipos)
    except Exception as e:
        logger.error(f"Error al listar equipos: {str(e)}")
        return render_template('error.html', error="Error al cargar los equipos")

@app.route('/list_device/crear', methods=['GET', 'POST'])
@login_required
def create_device():
    """Crea un nuevo equipo"""
    if request.method == 'POST':
        try:
            data = {
                'acronimo': request.form['acronimo'],
                'ip': request.form['ip'],
                'nombre_equipo': request.form['nombre_equipo'],
                'modelo': request.form['modelo'],
                'proveedor': request.form.get('ALCATE', 'ZTE', 'HUAWEI'),
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
            return redirect(url_for('list_device'))
            
        except sqlite3.IntegrityError as e:
            flash('El acrónimo o la IP ya existen en el sistema', 'error')
            return redirect(url_for('create_device'))
        except Exception as e:
            logger.error(f"Error al crear equipo: {str(e)}")
            flash('Error al crear el equipo', 'error')
            return redirect(url_for('create_device'))
    
    # GET: Mostrar formulario
    return render_template('equipos/create_device.html')

@app.route('/list_device/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_device(id):
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
                return redirect(url_for('list_device'))
            
            # GET: Mostrar formulario con datos actuales
            equipo = conn.execute('SELECT * FROM Equipo WHERE id = ?', (id,)).fetchone()
            if not equipo:
                flash('Equipo no encontrado', 'error')
                return redirect(url_for('list_device'))
                
            return render_template('equipos/edit_device.html', equipo=equipo)
            
    except sqlite3.IntegrityError as e:
        flash('El acrónimo o la IP ya existen en el sistema', 'error')
        return redirect(url_for('edit_equipo', id=id))
    except Exception as e:
        logger.error(f"Error al editar equipo: {str(e)}")
        flash('Error al editar el equipo', 'error')
        return redirect(url_for('list_device'))

@app.route('/list_device/eliminar/<int:id>', methods=['POST'])
@login_required
def delete_device(id):
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
            
    return redirect(url_for('list_device'))

@app.route('/user_management')
@admin_required
def user_management():
    """Muestra la gestión de usuarios para administradores"""
    with closing(get_db()) as conn:
        users = conn.execute('''
            SELECT u.id, u.usuario, t.tipo_usuario 
            FROM User_Login u
            JOIN Tipo_usuario t ON u.tipo_usuario = t.id
            ORDER BY u.id
        ''').fetchall()
        
        user_types = conn.execute(
            'SELECT id, tipo_usuario FROM Tipo_usuario'
        ).fetchall()
        
    return render_template('admin/user_management.html', 
                         users=users, 
                         user_types=user_types)

@app.route('/user_management/create', methods=['GET', 'POST'])
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
        if create_user_db(username, password, user_type):
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
        
    return render_template('admin/create_users.html', 
                         user_types=user_types)

@app.route('/list_version')
@login_required
def dashboard_list_version():
    """ Lista las versiones de configuracion generalizada"""
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
                ORDER BY nombre_equipo DESC 
                LIMIT 10
            ''').fetchall()
            
            return render_template('equipos/version/dashboard_version.html',
                                total_devices=total_devices,
                                active_devices=active_devices,
                                total_configs=total_configs,
                                total_users=total_users,
                                equipos=equipos)
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        return render_template('error.html', error="Error al cargar el dashboard_list_version")


@app.route('/list_version/<acronimo>')
@app.route('/equipo/<int:id>/versions')  # Ruta alternativa para compatibilidad
@login_required
def list_version(acronimo):
    """Lista las versiones de configuración para un equipo específico"""
    try:
        # Configuración de paginación
        page = max(1, int(request.args.get('page', 1)))
        per_page = int(request.args.get('per_page', '10'))

        with closing(get_db()) as conn:
            # Obtener equipo por acrónimo
            equipo = conn.execute('''
                SELECT id, nombre_equipo, acronimo, ip, modelo, estado 
                FROM Equipo WHERE acronimo = ?
            ''', (acronimo,)).fetchone()
            
            if not equipo:
                flash('Equipo no encontrado', 'error')
                return redirect(url_for('list_device'))

            # Consulta corregida para las versiones
            versions_query = '''
                SELECT 
                    v.id,
                    v.version,
                    strftime('%Y-%m-%d %H:%M', v.fecha) as fecha_formateada,
                    v.tamano,
                    v.status,
                    u.usuario as autor,
                    v.contenido
                FROM Version v
                JOIN User_Login u ON v.autor_id = u.id
                WHERE v.equipo_id = ?
                ORDER BY v.fecha DESC
                LIMIT ? OFFSET ?
            '''
            
            # Query corregida para contar el total de versiones
            count_query = '''
                SELECT COUNT(*)
                FROM Version
                WHERE equipo_id = ?
            '''
            
            total_versions = conn.execute(count_query, (equipo['id'],)).fetchone()[0]
            
            versions = conn.execute(
                versions_query, 
                (equipo['id'], per_page, (page-1)*per_page)
            ).fetchall()
            
            total_pages = max(1, (total_versions + per_page - 1) // per_page)
            page = min(page, total_pages)
            
            return render_template('equipos/version/list_version.html',
                equipo=equipo,
                all_version=versions,
                current_equipo=equipo['id'],
                pagination={
                    'page': page,
                    'per_page': per_page,
                    'total': total_versions,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            )
            
    except Exception as e:
        logger.error(f"Error en list_version: {str(e)}", exc_info=True)
        flash('Error al listar versiones', 'error')
        return redirect(url_for('dashboard'))


@app.route('/download_version/<int:id>')
@login_required
def download_version(id):
    try:
        with closing(get_db()) as conn:
            version = conn.execute(
                'SELECT version, contenido FROM Version WHERE id = ?',
                (id,)
            ).fetchone()
            
            if not version:
                abort(404)
                
            # Crear respuesta de descarga
            from io import BytesIO
            mem = BytesIO(version['contenido'])
            mem.seek(0)
            
            return send_file(
                mem,
                as_attachment=True,
                download_name=f'config_{version["version"]}.txt',
                mimetype='text/plain'
            )
            
    except Exception as e:
        logger.error(f"Error al descargar versión: {str(e)}")
        abort(500)

@app.route('/upload_version', methods=['GET', 'POST'])
@login_required
def upload_version():
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        try:
            # Verificar archivo
            if 'config_file' not in request.files:
                error_msg = 'No se seleccionó ningún archivo'
                if is_ajax:
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(request.url)
                
            file = request.files['config_file']
            
            # Validar equipo
            with closing(get_db()) as conn:
                equipo = conn.execute(
                    'SELECT id FROM Equipo WHERE acronimo = ?', 
                    (request.form.get('acronym'),)
                ).fetchone()
                
                if not equipo:
                    error_msg = 'El acrónimo del equipo no existe'
                    if is_ajax:
                        return jsonify({'success': False, 'error': error_msg}), 400
                    flash(error_msg, 'error')
                    return redirect(request.url)
            
                equipo_id = equipo['id']  # Obtenemos el ID del equipo
            
            # Leer y validar contenido
            file.seek(0)
            content = file.read()
            MAX_SIZE = 5 * 1024 * 1024  # 5MB
            if len(content) > MAX_SIZE:
                error_msg = 'El archivo es demasiado grande (máximo 5MB)'
                if is_ajax:
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(request.url)
            
            # Obtener datos del formulario
            version_data = {
                'version': request.form.get('version', '1.0').strip(),
                'fecha': request.form.get('creation_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'tamano': len(content),
                'status': 'active',
                'filename': file.filename,
                'equipo_id': equipo['id']
            }
            
            if not version_data['version']:
                error_msg = 'La versión es requerida'
                if is_ajax:
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(request.url)
            
            try:
                version_id = create_version(
                    equipo_id=equipo_id,
                    version_data={
                        'version': request.form.get('version'),
                        'fecha': request.form.get('creation_date'),
                        'tamano': len(content),
                        'status': 'active',
                        'filename': file.filename
                    },
                    user_id=current_user.id,
                    content=content
                )
            except Exception as e:
                logger.error(f"Error en create_version: {str(e)}")
                raise ValueError("Error al guardar en la base de datos")
            
            
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': 'Versión subida correctamente',
                    'redirect': url_for('list_version', acronimo=request.form.get('acronym'))
                })
            
            flash('Versión subida correctamente', 'success')
            return redirect(url_for('list_version', acronimo=request.form.get('acronym')))
                
        except ValueError as e:
            error_msg = str(e)
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 500
            flash(error_msg, 'error')
            return redirect(request.url)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            error_msg = "Error interno del servidor"
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 500
            flash(error_msg, 'error')
            return redirect(request.url)
    
    return render_template('equipos/version/upload_version.html')

@app.route('/api/equipment')
@login_required
def get_equipment_list():
    try:
        with closing(get_db()) as conn:
            equipos = conn.execute('''
                SELECT acronimo, nombre_equipo, ip 
                FROM Equipo 
                ORDER BY nombre_equipo
            ''').fetchall()
            
            return jsonify([dict(equipo) for equipo in equipos])
    except Exception as e:
        logger.error(f"Error getting equipment list: {str(e)}")
        return jsonify([])

@app.route('/user_management/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edita un usuario existente"""
    with closing(get_db()) as conn:
        if request.method == 'POST':
            try:
                username = request.form['username'].strip()
                user_type = int(request.form['user_type'])
                password = request.form['password']
                confirm_password = request.form['confirm_password']
                
                # Validaciones básicas
                if not username:
                    flash('El nombre de usuario es requerido', 'error')
                    return redirect(url_for('edit_user', user_id=user_id))
                
                if password and password != confirm_password:
                    flash('Las contraseñas no coinciden', 'error')
                    return redirect(url_for('edit_user', user_id=user_id))
                
                if password and len(password) < 8:
                    flash('La contraseña debe tener al menos 8 caracteres', 'error')
                    return redirect(url_for('edit_user', user_id=user_id))
                
                # Actualizar usuario
                if password:
                    hashed_pw = generate_password_hash(password)
                    conn.execute('''
                        UPDATE User_Login 
                        SET usuario = ?, tipo_usuario = ?, contrasena = ?
                        WHERE id = ?
                    ''', (username, user_type, hashed_pw, user_id))
                else:
                    conn.execute('''
                        UPDATE User_Login 
                        SET usuario = ?, tipo_usuario = ?
                        WHERE id = ?
                    ''', (username, user_type, user_id))
                
                conn.commit()
                flash('Usuario actualizado exitosamente', 'success')
                return redirect(url_for('user_management'))
                
            except sqlite3.IntegrityError:
                flash('El nombre de usuario ya existe', 'error')
                return redirect(url_for('edit_user', user_id=user_id))
            except Exception as e:
                logger.error(f"Error al editar usuario: {str(e)}")
                flash('Error al actualizar el usuario', 'error')
                return redirect(url_for('edit_user', user_id=user_id))
        
        # GET: Mostrar formulario de edición
        user = conn.execute('''
            SELECT id, usuario, tipo_usuario 
            FROM User_Login 
            WHERE id = ?
        ''', (user_id,)).fetchone()
        
        if not user:
            abort(404)
            
        tipos_usuario = conn.execute(
            'SELECT id, tipo_usuario FROM Tipo_usuario'
        ).fetchall()
        
        return render_template('admin/edit_user.html', 
                             user=user, 
                             tipos_usuario=tipos_usuario)

@app.route('/user_management/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Elimina un usuario con protección para el admin principal"""
    try:
        with closing(get_db()) as conn:
            # Protección para el admin principal (ID 1)
            if user_id == 1:
                flash('No puedes eliminar al administrador principal del sistema', 'error')
                return redirect(url_for('user_management'))
            
            # Verificar que no se está eliminando a sí mismo
            if user_id == current_user.id:
                flash('No puedes eliminarte a ti mismo', 'error')
                return redirect(url_for('user_management'))
            
            # Verificar que no sea el último administrador
            if current_user.is_admin:
                admins_count = conn.execute(
                    'SELECT COUNT(*) FROM User_Login WHERE tipo_usuario = 1'
                ).fetchone()[0]
                
                user_to_delete = conn.execute(
                    'SELECT tipo_usuario FROM User_Login WHERE id = ?', 
                    (user_id,)
                ).fetchone()
                
                if user_to_delete and user_to_delete['tipo_usuario'] == 1 and admins_count <= 1:
                    flash('No puedes eliminar el último administrador', 'error')
                    return redirect(url_for('user_management'))
            
            # Ejecutar eliminación
            conn.execute('DELETE FROM User_Login WHERE id = ?', (user_id,))
            conn.commit()
            flash('Usuario eliminado exitosamente', 'success')
            
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {str(e)}")
        flash('Error al eliminar el usuario', 'error')
    
    return redirect(url_for('user_management'))

@app.route('/documentacion')
@admin_required
def documentacion():
    """Sirve el documento PDF de guía del sistema"""
    try:
        filename = 'Documento Guia del Sistema.pdf'
        return send_from_directory(
            directory=app.config['DOCUMENTATION_FOLDER'],
            path=filename,
            as_attachment=False  # Para mostrar en el navegador en lugar de descargar
        )
    except FileNotFoundError:
        abort(404)

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

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    logger.warning(f"CSRF token missing/invalid: {e.description}")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': 'CSRF token missing or invalid'}), 400
    flash('Token CSRF inválido o ausente', 'error')
    return redirect(request.referrer or url_for('index'))

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

def validate_credentials(username, password):
    """Valida que las credenciales no estén vacías."""
    return username and password



@app.route('/')
def index():
    return redirect(url_for('login'))


    
if __name__ == '__main__':
    init_db()
    
    # Obtener IP local automáticamente
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    #app.run(debug=True, host='161.196.49.37', port=5000)
    app.run(debug=True, host='0.0.0.0', port=5000)