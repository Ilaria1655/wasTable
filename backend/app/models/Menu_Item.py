from .. import db
from datetime import datetime
class MenuItem(db.Model):
    __tablename__ = 'menu_items'  # Nome della tabella nel database
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # es. "primo", "secondo", "bevanda"

    def __repr__(self):
        return f"<MenuItem {self.name} - {self.category}>"
