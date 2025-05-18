from backend.app import create_app, db
from backend.app.models.Menu_Item import MenuItem

# Crea un'applicazione Flask
app = create_app()

# Aggiungi il contesto dell'app
with app.app_context():
    menu_items = [
        MenuItem(name="Spaghetti alla Carbonara", price=12.5, category="primo"),
        MenuItem(name="Lasagna", price=14.0, category="primo"),
        MenuItem(name="Filetto di Manzo", price=25.0, category="secondo"),
        MenuItem(name="Pollo alla Griglia", price=18.0, category="secondo"),
        MenuItem(name="Coca-Cola", price=3.0, category="bevanda"),
        MenuItem(name="Acqua Minerale", price=2.0, category="bevanda"),
    ]

    # Salva gli elementi nel database
    db.session.bulk_save_objects(menu_items)
    db.session.commit()
