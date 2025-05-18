# models.py
from .. import db
from datetime import datetime
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id', ondelete='CASCADE'), nullable=False)
    items = db.Column(db.JSON, nullable=False)  # I piatti ordinati saranno memorizzati come JSON
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'delivered', 'rejected'
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)
    table = db.relationship('Table', backref=db.backref('orders', lazy=True))
    # Relazione con la prenotazione
    reservation = db.relationship('Reservation', backref='orders')
    def __repr__(self):
        return f"<Order {self.id} - Reservation {self.reservation_id}>"
