from database import get_db, create_user_db, create_version
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import sqlite3
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    conn = get_db()
    c = conn.cursor()
    
    try:
        # 1. Insertar usuarios
        users = [
            ('admin', 'admin123', 1),  # Administrador
            ('trabajador', 'trabajador123', 2)  # Trabajador
        ]
        
        for username, password, user_type in users:
            if not c.execute('SELECT id FROM User_Login WHERE usuario = ?', (username,)).fetchone():
                hashed_pw = generate_password_hash(password)
                c.execute(
                    'INSERT INTO User_Login (usuario, contrasena, tipo_usuario) VALUES (?, ?, ?)',
                    (username, hashed_pw, user_type)
                )
        
        # Obtener IDs de usuarios recién creados
        admin_id = c.execute('SELECT id FROM User_Login WHERE usuario = "admin"').fetchone()[0]
        trabajador_id = c.execute('SELECT id FROM User_Login WHERE usuario = "trabajador"').fetchone()[0]
        
        # 2. Insertar 5 equipos (sin version_id)
        equipos = [
            ('Norte', 'Activo', 'Ciudad A', 'Router Principal', 'RTR-PRI', '192.168.1.1', 'Cisco 3945', 'Cisco'),
            ('Sur', 'Activo', 'Ciudad B', 'Switch Core', 'SWC-CORE', '192.168.1.2', 'Cisco 3850', 'Cisco'),
            ('Este', 'Mantenimiento', 'Ciudad C', 'Firewall Perimeter', 'FW-PERIM', '192.168.1.3', 'Fortigate 100F', 'Fortinet'),
            ('Oeste', 'Activo', 'Ciudad D', 'Access Point', 'AP-WIFI', '192.168.1.4', 'Ubiquiti UAP-AC-PRO', 'Ubiquiti'),
            ('Centro', 'Inactivo', 'Ciudad E', 'Servidor NAS', 'NAS-STOR', '192.168.1.5', 'Synology DS1821+', 'Synology')
        ]
        
        equipo_ids = []
        for equipo in equipos:
            c.execute('''
                INSERT INTO Equipo 
                (region, estado, localidad, nombre_equipo, acronimo, ip, modelo, proveedor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', equipo)
            equipo_ids.append(c.lastrowid)
        
        conn.commit()
        
        # 3. Insertar 10 configuraciones (2 por equipo)
        # Fechas de ejemplo (últimos 5 días)
        fechas = [datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
        
        for i, equipo_id in enumerate(equipo_ids):
            for j in range(2):  # 2 versiones por equipo
                fecha = fechas[i].strftime('%Y-%m-%d %H:%M')
                version_data = {
                    'version': f'1.{i+1}.{j+1}',
                    'fecha': fecha,
                    'tamano': random.uniform(10.5, 50.3),  # Tamaño aleatorio entre 10.5 y 50.3 KB
                    'status': 'active' if j == 1 else 'draft'
                }
                
                # Contenido de ejemplo
                contenido = f"Configuración para equipo {equipo_id}, versión {version_data['version']}".encode()
                
                # Insertar versión con referencia al equipo
                c.execute('''
                    INSERT INTO Version 
                    (version, fecha, tamano, autor_id, status, contenido, equipo_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version_data['version'],
                    version_data['fecha'],
                    version_data['tamano'],
                    admin_id if j == 1 else trabajador_id,
                    version_data['status'],
                    contenido,
                    equipo_id  # <- Aquí asignamos el equipo correctamente
                ))
        
        conn.commit()
        logger.info("✅ Datos de prueba insertados correctamente:")
        logger.info(f"- {len(users)} usuarios creados")
        logger.info(f"- {len(equipos)} equipos insertados")
        logger.info(f"- {len(equipo_ids)*2} versiones de configuración creadas")
        
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"❌ Error al insertar datos: {e}")
        raise
    finally:
        conn.close()

def verify_seed_data():
    """Verifica que los datos se hayan insertado correctamente"""
    conn = get_db()
    try:
        # Verificar equipos
        equipos = conn.execute('SELECT * FROM Equipo').fetchall()
        logger.info(f"Equipos en DB: {len(equipos)}")
        
        # Verificar versiones por equipo
        for equipo in equipos:
            versiones = conn.execute(
                'SELECT * FROM Version WHERE equipo_id = ?', 
                (equipo['id'],)
            ).fetchall()
            logger.info(f"Equipo {equipo['acronimo']} tiene {len(versiones)} versiones")
        
        # Verificar relaciones
        problemas = conn.execute('''
            SELECT e.acronimo 
            FROM Equipo e
            LEFT JOIN Version v ON e.id = v.equipo_id
            WHERE v.id IS NULL
        ''').fetchall()
        
        if problemas:
            logger.warning(f"Equipos sin versiones: {[p['acronimo'] for p in problemas]}")
        
    except sqlite3.Error as e:
        logger.error(f"Error al verificar datos: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("=== Ejecutando seed de la base de datos ===")
    seed_database()
    print("\n=== Verificando datos insertados ===")
    verify_seed_data()