from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv
load_dotenv()

# Inizializzazione estensioni globali
db = SQLAlchemy()
login_manager = LoginManager()

def start_scheduler(app):
    """
    Avvia lo scheduler in background che esegue il cleanup delle prenotazioni ogni ora.
    """
    with app.app_context():
        from backend.app.routes.auth_routes import delete_old_reservations
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=delete_old_reservations, trigger="interval", hours=1)
        scheduler.start()

def create_app():
    """
    Crea e configura l'app Flask.
    """
    app = Flask(__name__, template_folder="templates")

    # Configurazioni generali
    app.config['SECRET_KEY'] = 'supersegretokey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'

    # Inizializza le estensioni con l'app
    db.init_app(app)
    Session(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Registra blueprint
    from backend.app.routes.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp)

    # Avvia lo scheduler in background
    start_scheduler(app)

    return app
