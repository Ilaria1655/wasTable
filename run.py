from backend.app import create_app, db
from backend.app.models.table import Table
from backend.app.models.user import User

# Crea l'app usando la funzione create_app
app = create_app()

# Crea tutte le tabelle nel database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
