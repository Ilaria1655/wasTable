from .. import db
from  backend.app.models.user import User
from flask_login import UserMixin
from sqlalchemy import Date

class Reservation(db.Model):
    __tablename__ = 'reservation'

    # Colonne della tabella
    id = db.Column(db.Integer, primary_key=True)  # Colonna primaria
    date = db.Column(Date, nullable=False)  # Data della prenotazione
    time = db.Column(db.String(20), nullable=False)  # Orario della prenotazione
    guests = db.Column(db.Integer, nullable=False)  # Numero di ospiti
    note = db.Column(db.String(255))  # Note opzionali

    # Colonna di chiave esterna che si riferisce a User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Colonna con chiave esterna
    # reservation.py
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)
    table = db.relationship('Table', back_populates='reservations', cascade='all, delete', passive_deletes=True)
    user = db.relationship('User', backref='reservations')

    # Inizializzatore della classe
    def __init__(self, date, time, guests, note, user_id, table_id):
        self.date = date
        self.time = time
        self.guests = guests
        self.note = note
        self.user_id = user_id
        self.table_id = table_id

    def __repr__(self):
        return f"<Reservation {self.id} - {self.date} {self.time}>"
