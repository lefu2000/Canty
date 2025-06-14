# database.py
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('network_configs.db')
    c = conn.cursor()
    
    # Tabla de usuarios para el login
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL
                )''')
    
    # Tabla de equipos
    c.execute('''CREATE TABLE IF NOT EXISTS devices
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  hostname TEXT NOT NULL,
                  ip TEXT NOT NULL UNIQUE,
                  vendor TEXT NOT NULL,
                  last_config_date TEXT,
                  last_config_text TEXT)''')
    
    # Insertar usuario admin por defecto (password: admin)
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 ('admin', 'admin'))
    except sqlite3.IntegrityError:
        pass  # El usuario ya existe
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()

# Falta crear las tablas en funcion al proyecto.