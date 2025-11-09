import os
from datetime import timedelta

class Config:
    # Seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Aplicación
    DATABASE = 'network_configs.db'
    TEMPLATES_AUTO_RELOAD = True
    DOCUMENTATION_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'docs')
    
    # Rate limiting
    DEFAULT_LIMITS = ["200 per day", "50 per hour"]
