# database.py
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

def init_db():
    """Inicializa o actualiza la base de datos"""
    db_exists = os.path.exists('network_configs.db')
    conn = sqlite3.connect('network_configs.db')
    c = conn.cursor()

 # Crear tabla Version
    c.execute('''
    CREATE TABLE IF NOT EXISTS Version (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT,
        fecha TEXT NOT NULL, 
        tamano REAL NOT NULL,
        autor TEXT NOT NULL,
        contenido TEXT
    )
    ''')

    #posible correccion
    #fecha (date)
    #Tamaño (decimal)
    
    # Crear tabla Equipo
    c.execute('''
    CREATE TABLE IF NOT EXISTS Equipo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        acronimo TEXT UNIQUE NOT NULL UNIQUE,
        ip TEXT UNIQUE NOT NULL UNIQUE,
        nombre_equipo TEXT,
        modelo TEXT,
        proveedor TEXT NOT NULL,
        version TEXT,
        localidad TEXT,
        region TEXT,
        estado TEXT
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
