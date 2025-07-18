# database.py
from flask import current_app
from contextlib import closing
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

def _column_exists(cursor, table_name, column_name):
    """
    Verifica si una columna existe en una tabla dada.

    Args:
        cursor (sqlite3.Cursor): El cursor de la base de datos.
        table_name (str): El nombre de la tabla.
        column_name (str): El nombre de la columna a verificar.

    Returns:
        bool: True si la columna existe, False en caso contrario.
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        if col[1] == column_name: # col[1] es el nombre de la columna
            return True
    return False

def init_db():
    """Inicializa o actualiza la base de datos con la estructura corregida"""
    db_exists = os.path.exists('network_configs.db')
    conn = sqlite3.connect('network_configs.db')
    c = conn.cursor()

    # Crear tabla Tipo_usuario primero (se referencia desde User_Login)
    c.execute('''
    CREATE TABLE IF NOT EXISTS Tipo_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_usuario TEXT UNIQUE
    )
    ''')

    # Crear tabla User_Login
    c.execute('''
    CREATE TABLE IF NOT EXISTS User_Login (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        contrasena TEXT NOT NULL,
        tipo_usuario INTEGER NOT NULL,
        FOREIGN KEY (tipo_usuario) REFERENCES Tipo_usuario(id)
    )
    ''')

    # Crear trigger para proteger al admin principal
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS protect_admin
        BEFORE DELETE ON User_Login
        FOR EACH ROW
        BEGIN
            SELECT CASE
                WHEN OLD.id = 1 THEN
                    RAISE(ABORT, 'No se puede eliminar al administrador principal')
            END;
        END;
    ''')
    conn.commit()

    # Crear tabla Equipo (sin version_id)
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
        proveedor TEXT
    )
    ''')

    # Crear tabla Version con equipo_id
    c.execute('''
    CREATE TABLE IF NOT EXISTS Version (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT NOT NULL,
        fecha DATETIME NOT NULL,
        tamano REAL NOT NULL,
        autor_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Draft',
        contenido BLOB,
        equipo_id INTEGER NOT NULL,
        archivo_nombre TEXT,
        FOREIGN KEY (autor_id) REFERENCES User_Login(id),
        FOREIGN KEY (equipo_id) REFERENCES Equipo(id)
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
    
    # Migración: Si existe version_id en Equipo, eliminarlo
    if _column_exists(c, 'Equipo', 'version_id'):
        try:
            # Primero necesitamos eliminar la restricción de clave foránea
            c.execute("PRAGMA foreign_keys=off")
            
            # Crear una tabla temporal con la nueva estructura
            c.execute('''
            CREATE TABLE IF NOT EXISTS Equipo_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT,
                estado TEXT,
                localidad TEXT,
                nombre_equipo TEXT,
                acronimo TEXT UNIQUE,
                ip TEXT UNIQUE,
                modelo TEXT,
                proveedor TEXT
            )
            ''')
            
            # Copiar datos
            c.execute('''
            INSERT INTO Equipo_temp
            SELECT id, region, estado, localidad, nombre_equipo, 
                   acronimo, ip, modelo, proveedor
            FROM Equipo
            ''')
            
            # Eliminar tabla original
            c.execute("DROP TABLE Equipo")
            
            # Renombrar tabla temporal
            c.execute("ALTER TABLE Equipo_temp RENAME TO Equipo")
            
            # Reactivar claves foráneas
            c.execute("PRAGMA foreign_keys=on")
            
            logger.info("Columna version_id eliminada de la tabla Equipo")
        except sqlite3.Error as e:
            logger.error(f"Error al eliminar version_id: {e}")
            conn.rollback()
    
    conn.commit()
    conn.close()

def get_versions_for_equipo(equipo_id):
    """Obtiene todas las versiones para un equipo específico"""
    conn = get_db()
    return conn.execute('''
    SELECT v.id, v.version, v.fecha, v.tamano, 
           u.usuario as autor, v.status, v.contenido
    FROM Version v
    JOIN User_Login u ON v.autor_id = u.id
    WHERE v.equipo_id = ?
    ORDER BY v.fecha DESC
    ''', (equipo_id,)).fetchall()

def get_equipos_with_version_count():
    """Obtiene equipos con conteo de versiones"""
    conn = get_db()
    return conn.execute('''
    SELECT e.*, COUNT(v.id) as version_count
    FROM Equipo e
    LEFT JOIN Version v ON e.id = v.equipo_id
    GROUP BY e.id
    ''').fetchall()

def create_version(equipo_id, version_data, user_id, content):
    """Crea una nueva versión de configuración"""
    try:
        # Obtener conexión a la base de datos
        conn = sqlite3.connect(current_app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        
        with closing(conn) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Version (
                    equipo_id,
                    version,
                    fecha,
                    tamano,
                    status,
                    archivo_nombre,
                    contenido,
                    autor_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                equipo_id,
                version_data['version'],
                version_data['fecha'],
                version_data['tamano'],
                version_data['status'],
                version_data['filename'],
                content,
                user_id
            ))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos al crear versión: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al crear versión: {str(e)}")
        raise

def create_user_db(usuario, contrasena, tipo_usuario):
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