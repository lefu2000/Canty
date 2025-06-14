from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'lriver14'  # Change this to a random secret key!

# Configuration
DATABASE = 'network_configs.db'
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates during development

def get_db():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """Initialize the database with required tables"""
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')
        db.commit()
        db.close()

@app.route('/index', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 1. Obtención de datos del formulario
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"Login attempt - Username: {username}")  # Debug print
        
        # 2. Validación básica
        if not username or not password:
            return render_template('index.html', error="Username and password are required")
        
        try:
            # 3. Conexión a la base de datos
            conn = get_db()

            # 4. Búsqueda del usuario
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', 
                (username,)
            ).fetchone()
            conn.close()
            
            # 5. Verificación de credenciales
            if user and check_password_hash(user['password'], password):
                print("Login successful!")  # Debug print
                 # 6. Creación de sesión
                session['user_id'] = user['id']
                session['username'] = user['username']
                print(f"Session after login: {dict(session)}")  # Debug print
                return redirect(url_for('dashboard'))
            
             # 7. Manejo de credenciales inválidas
            print("Invalid credentials")  # Debug print
            return render_template('index.html', error="Invalid credentials")
        
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            return render_template('index.html', error="Server error occurred")

    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Display the dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db()
        devices = conn.execute('SELECT * FROM devices ORDER BY hostname').fetchall()
        conn.close()
        return render_template('dashboard.html', 
                             devices=devices, 
                             username=session['username'])
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        return render_template('index.html', error="Could not load devices")

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('register.html', error="Username and password are required")
        
        if len(password) < 8:
            return render_template('register.html', error="Password must be at least 8 characters")
        
        try:
            conn = get_db()
            # Check if username already exists
            if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                return render_template('register.html', error="Username already taken")
            
            # Create new user with hashed password
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            conn.commit()
            conn.close()
            
            return redirect(url_for('login'))
        
        except Exception as e:
            conn.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            return render_template('register.html', error="Registration failed")
    
    return render_template('register.html')

if __name__ == '__main__':
    init_db()  # Initialize database tables
    app.run(debug=True, host='0.0.0.0', port=5000)