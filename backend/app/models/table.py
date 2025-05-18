from backend.app import db

class Table(db.Model):
    __tablename__ = 'table'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    seats = (db.Column(db.Integer, nullable=False))
    status = db.Column(db.String(20), default='disponibile')  # disponibile, occupato, riservato
    name = db.Column(db.String(20), unique=True, nullable=False)
    is_wastable = db.Column(db.Boolean, default=False)
    occupied = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Table {self.number} - {self.status}>"

    # table.py
    reservations = db.relationship('Reservation', back_populates='table')
