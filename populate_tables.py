from backend.app import db, create_app
from backend.app.models import Table

app = create_app()

with app.app_context():
    db.create_all()
    Table.query.delete()

    tables = []
    number = 1

    # 2 tavoli da 10 posti
    for i in range(2):
        tables.append(Table(number=number, seats=10, name=f"{number}", status="disponibile", is_wastable=False))
        number += 1

    # 8 tavoli da 4 posti (uno speciale chiamato "wasTable")
    for i in range(7):
        tables.append(Table(number=number, seats=4, name=f"{number}", status="disponibile", is_wastable=False))
        number += 1
    tables.append(Table(number=number, seats=4, name="wasTable", status="disponibile", is_wastable=True))
    number += 1

    # 6 tavoli da 6 posti
    for i in range(6):
        tables.append(Table(number=number, seats=6, name=f"{number}", status="disponibile", is_wastable=False))
        number += 1

    # 4 tavoli da 2 posti
    for i in range(4):
        tables.append(Table(number=number, seats=2, name=f"{number}", status="disponibile", is_wastable=False))
        number += 1

    db.session.bulk_save_objects(tables)
    db.session.commit()

    print(f"Inseriti {len(tables)} tavoli nel database.")
