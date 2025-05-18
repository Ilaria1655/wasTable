import os

# Configurazione del database
SQLALCHEMY_DATABASE_URI = 'sqlite:///C:/Users/ilari/PycharmProjects/wasTable/app.db'  # Usa un database SQLite locale
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Impostazioni per il file statico
STATIC_FOLDER = 'frontend/static'
TEMPLATES_FOLDER = 'backend/app/templates'

# Opzionali: Configurazioni aggiuntive per la sicurezza
SECRET_KEY = os.urandom(24)
