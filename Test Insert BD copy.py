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

    # Insertar usuario admin si no existe por defecto (password: admin)
    try:
        c.execute('''
            INSERT INTO Equipo (region, estado, localidad, nombre_equipo, acronimo, ip, modelo, proveedor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Central', 'Distrito Capital', 'Chaguaramos', 'procuraduría general de la república venezuela', 'CGS-PGR-00', '10.150.217.30', '5928', 'ZTE'))
        logger.info("Usuario admin creado o verificado")
    except sqlite3.IntegrityError:
        logger.info("equipo ya existe")
        pass  # El usuario ya existe

    conn.commit()
    conn.close()
    conn = sqlite3.connect('network_configs.db')
    c = conn.cursor()
    
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
   






"""


    c.execute('''
    CREATE TABLE IF NOT EXISTS Equipo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        acronimo TEXT NOT NULL UNIQUE,
        ip TEXT NOT NULL UNIQUE,
        nombre_equipo TEXT,
        modelo TEXT,
        proveedor TEXT NOT NULL,
        version TEXT,
        localidad TEXT,
        region TEXT,
        estado TEXT
    )
    ''')

"""