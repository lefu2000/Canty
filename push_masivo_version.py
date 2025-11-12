import os
import sqlite3
from datetime import datetime

# Ruta de la carpeta con archivos TXT
folder_path = 'txt_versions'

# Crear carpeta si no existe
os.makedirs(folder_path, exist_ok=True)

# Conexión a la base de datos
conn = sqlite3.connect('network_configs.db')
cursor = conn.cursor()

# Obtener el ID del equipo por acrónimo
def get_equipo_id(acronimo):
    result = cursor.execute("SELECT id FROM Equipo WHERE acronimo = ?", (acronimo,)).fetchone()
    return result[0] if result else None

# ID del autor (por ejemplo, admin)
autor_id = 1

# Contador de inserciones
insertados = 0
no_encontrados = []

# Procesar cada archivo TXT
for filename in os.listdir(folder_path):
    if filename.endswith('.txt'):
        acronimo = filename.split('_')[0]  # Ejemplo: router1_config.txt → acronimo = 'router1'
        equipo_id = get_equipo_id(acronimo)
        if not equipo_id:
            no_encontrados.append(filename)
            continue

        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'rb') as f:
            content = f.read()

        version_data = {
            'version': '1.0',
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tamano': len(content),
            'status': 'active',
            'filename': filename
        }

        cursor.execute('''
            INSERT INTO Version (
                equipo_id, version, fecha, tamano, status, archivo_nombre, contenido, autor_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            equipo_id,
            version_data['version'],
            version_data['fecha'],
            version_data['tamano'],
            version_data['status'],
            version_data['filename'],
            content,
            autor_id
        ))
        insertados += 1

conn.commit()
conn.close()

print(f"Carga masiva completada. Archivos insertados: {insertados}")
if no_encontrados:
    print("Archivos ignorados por acrónimo no encontrado:")
    for nf in no_encontrados:
        print(f" - {nf}")