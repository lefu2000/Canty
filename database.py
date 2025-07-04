# database.py
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

def get_db():
    """Devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect('network_configs.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o actualiza la base de datos"""
    db_exists = os.path.exists('network_configs.db')
    conn = sqlite3.connect('network_configs.db')
    c = conn.cursor()

 # Crear tabla Version
    c.execute('''
    CREATE TABLE IF NOT EXISTS Version (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT NOT NULL,
        fecha DATE NOT NULL,
        tamano REAL NOT NULL,
        autor_id INTEGER NOT NULL,
        contenido BLOB,
        FOREIGN KEY (autor_id) REFERENCES User_Login(id)
    )
    ''')

    #posible correccion
    #fecha (date)
    #Tamaño (decimal)
    
    # Crear tabla Equipo
    c.execute('''
    CREATE TABLE IF NOT EXISTS Equipo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region TEXT,
        estado TEXT,
        localidad TEXT,
        nombre_equipo TEXT,
        acronimo TEXT UNIQUE,
        ip TEXT UNIQUE,
        modelo TEXT,
        proveedor TEXT,
        version_id INTEGER,
        FOREIGN KEY (version_id) REFERENCES Version(id)
    )
    ''')
    
    # Crear tabla User_Login
    c.execute('''
    CREATE TABLE IF NOT EXISTS User_Login (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        contrasena TEXT NOT NULL,
        tipo_usuario INTEGER NOT NULL
    )
    ''')

    # Usuario administrador = 1
    # Usuario Trabajador    = 2
    
    # Crear tabla Tipo_usuario
    c.execute('''
    CREATE TABLE IF NOT EXISTS Tipo_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_usuario TEXT
    )
    ''')

  # Insertar tipos de usuario si no existen
    tipos_usuario = [
        (1, 'Administrador'),
        (2, 'Trabajador')
    ]
    
    for tipo_id, tipo_nombre in tipos_usuario:
        try:
            c.execute(
                'INSERT INTO Tipo_usuario (id, tipo_usuario) VALUES (?, ?)',
                (tipo_id, tipo_nombre)
            )
        except sqlite3.IntegrityError:
            pass  # El tipo ya existe
    
    # Insertar usuario admin si no existe por defecto (password: admin)
    try:
        hashed_pw = generate_password_hash('admin', method='pbkdf2:sha256')
        c.execute(
            'INSERT INTO User_Login (usuario, contrasena, tipo_usuario) VALUES (?, ?, ?)',
            ('admin', hashed_pw, 1)  # 1 para Administrador
        )
        logger.info("Usuario admin creado o verificado")
    except sqlite3.IntegrityError:
        logger.info("Usuario admin ya existe")
        pass  # El usuario ya existe
    
    conn.commit()
    conn.close()

def get_versions_with_authors():
    """Obtiene versiones con información del autor"""
    conn = get_db()
    return conn.execute('''
    SELECT v.id, v.version, v.fecha, v.tamano, 
           u.usuario as autor, v.contenido
    FROM Version v
    JOIN User_Login u ON v.autor_id = u.id
    ORDER BY v.fecha DESC
    ''').fetchall()

def get_equipos_with_versions():
    """Obtiene equipos con información de versión"""
    conn = get_db()
    return conn.execute('''
    SELECT e.id, e.nombre_equipo, e.acronimo, e.ip,
           v.version as version_firmware
    FROM Equipo e
    LEFT JOIN Version v ON e.version_id = v.id
    ''').fetchall()

def create_version(version_data, user_id, content):
    """Crea una nueva versión asociada a un usuario"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
    INSERT INTO Version (version, fecha, tamano, autor_id, contenido)
    VALUES (?, ?, ?, ?, ?)
    ''', (
        version_data['version'],
        version_data['fecha'],
        version_data['tamano'],
        user_id,
        content
    ))
    conn.commit()
    return c.lastrowid

def create_user(usuario, contrasena, tipo_usuario=2):
    """Crea un nuevo usuario con tipo especificado"""
    conn = get_db()
    hashed_pw = generate_password_hash(contrasena)
    try:
        conn.execute(
            'INSERT INTO User_Login (usuario, contrasena, tipo_usuario) VALUES (?, ?, ?)',
            (usuario, hashed_pw, tipo_usuario)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Usuario ya existe

def reset_db():
    """Reinicia completamente la base de datos (solo para desarrollo)"""
    if os.path.exists('network_configs.db'):
        os.remove('network_configs.db')
    init_db()
    logger.warning("Base de datos reiniciada completamente")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Para desarrollo: reset_db() para forzar recreación
    #reset_db()
    init_db()
