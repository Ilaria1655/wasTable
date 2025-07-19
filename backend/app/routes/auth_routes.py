from flask import flash, Blueprint, request, render_template, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime, timedelta, time
from backend.app.models import Reservation, Table
from backend.app.models.Menu_Item import MenuItem
from backend.app.models.user import User
from backend.app.models.Order import Order
import json
import logging

from backend.app import db
from flask_login import login_required
from flask_login import current_user
from flask_login import LoginManager
from flask_login import login_user

bp = Blueprint('auth', __name__)


# Rotta per la home
@bp.route("/")
def index():
    session.clear()
    return render_template("index.html")


# Rotta per il login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['user_id'] = user.id
            session['user'] = user.email
            session['role'] = user.role

            # Redirect in base al ruolo
            if user.role == 'admin':
                return redirect(url_for('auth.admin_dashboard'))
            else:
                return redirect(url_for('auth.dashboard'))

        flash("Credenziali non valide", 'danger')
        return redirect(url_for('auth.login'))

    return render_template('login.html')


# Rotta per la registrazione
@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]  # Recupera il ruolo selezionato

        # Hash della password
        hashed_pw = generate_password_hash(password)

        # Crea l'utente con il ruolo selezionato
        user = User(username=username, email=email, password_hash=hashed_pw, role=role)

        # Aggiungi l'utente al database
        db.session.add(user)
        db.session.commit()

        flash("Registrazione avvenuta con successo. Effettua il login.")
        return redirect(url_for('auth.login'))

    return render_template("register.html")


# Rotta per il logout
@bp.route('/logout')
def logout():
    session.clear()
    flash("Sei stato disconnesso", 'info')
    return redirect(url_for('auth.index'))


# Rotta per dashboard utente
@bp.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user:
        flash("Utente non trovato.")
        return redirect(url_for("auth.login"))

    current_time = datetime.now()

    today = date.today()
    reservation = Reservation.query.filter_by(user_id=user.id, date=today) \
        .order_by(Reservation.time.asc()) \
        .first()

    can_order = False

    if reservation:
        print(f"Raw reservation.time: {reservation.time} (type: {type(reservation.time)})")

        # Prova a convertire in modo robusto
        try:
            if isinstance(reservation.time, str):
                # Se ha anche i secondi, gestiscili
                if len(reservation.time) == 5:
                    reservation_time = datetime.strptime(reservation.time, "%H:%M").time()
                elif len(reservation.time) == 8:
                    reservation_time = datetime.strptime(reservation.time, "%H:%M:%S").time()
                else:
                    raise ValueError("Formato orario prenotazione non riconosciuto")
            elif isinstance(reservation.time, time):
                reservation_time = reservation.time
            else:
                raise ValueError("Tipo orario prenotazione sconosciuto")

            reservation_datetime = datetime.combine(today, reservation_time)
            reservation_end_time = reservation_datetime + timedelta(minutes=90)

            print(f"Current time: {current_time}")
            print(f"Reservation datetime: {reservation_datetime}")
            print(f"Reservation end time: {reservation_end_time}")

            if reservation_datetime <= current_time <= reservation_end_time:
                can_order = True

        except Exception as e:
            print("Errore conversione orario:", e)
            flash("Errore interno nel controllo dell'orario prenotazione.", "danger")

    return render_template("dashboard.html", user=user, reservation=reservation, can_order=can_order)


# Rotta per dashboard admin
@bp.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Accesso non autorizzato", 'danger')
        return redirect(url_for('auth.index'))

    # Ottieni tutte le prenotazioni e ordina per data e numero di persone
    reservations = Reservation.query.order_by(Reservation.date, Reservation.guests).all()

    return render_template('admin_dashboard.html', reservations=reservations)


# Pagina di prenotazione
@bp.route('/reservation', methods=['GET', 'POST'])
def reservation():
    if request.method == 'POST':
        data = request.form['data']
        ora = request.form['ora']
        persone = int(request.form['persone'])
        note = request.form.get('note')
        table_id = request.form.get('table_id')

        if not table_id:
            flash("Devi selezionare un tavolo per la prenotazione.", "danger")
            return redirect(url_for('auth.reservation'))

        date_obj = datetime.strptime(data, '%Y-%m-%d').date()
        time_obj = datetime.strptime(ora, '%H:%M').time()
        time_str = time_obj.strftime('%H:%M')
        table = Table.query.get(table_id)

        if not table:
            flash("Tavolo non trovato.", "danger")
            return redirect(url_for('auth.reservation'))

        if persone > table.seats:
            flash(f"Errore: il tavolo scelto ha solo {table.seats} posti disponibili.", "error")
            return redirect(url_for('auth.reservation'))

        # Fascia oraria +/- 90 minuti
        datetime_obj = datetime.combine(date_obj, time_obj)
        start_range = (datetime_obj - timedelta(minutes=90)).time()
        end_range = (datetime_obj + timedelta(minutes=90)).time()

        conflicting_res = Reservation.query.filter(
            Reservation.table_id == table_id,
            Reservation.date == date_obj,
            Reservation.time >= start_range,
            Reservation.time <= end_range
        ).first()

        if conflicting_res:
            flash("Errore: questo tavolo è già prenotato in un intervallo di 1 ora e mezza dalla fascia oraria scelta.",
                  "error")
            return redirect(url_for('auth.reservation'))

        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            flash("Devi essere loggato per fare una prenotazione.", "danger")
            return redirect(url_for('auth.login'))

        new_reservation = Reservation(
            date=date_obj,
            time=time_str,
            guests=persone,
            note=note,
            user_id=user_id,
            table_id=table_id
        )

        # Imposta manualmente status "occupato" (opzionale se usi calcolo dinamico)
        table.status = "occupato"

        db.session.add(new_reservation)
        db.session.commit()
        session['reservation_id'] = new_reservation.id

        flash("Prenotazione effettuata con successo!", "success")
        return redirect(url_for('auth.reservations'))

    return render_template('reservation.html', tables=Table.query.order_by(Table.number).all())


@bp.route("/reservations")
def reservations():
    user_id = session.get('user_id')
    if not user_id:
        flash("Devi essere loggato per vedere le tue prenotazioni.", "danger")
        return redirect(url_for('auth.login'))

    reservations = Reservation.query.filter_by(user_id=user_id).all()
    today_date = date.today().strftime("%Y-%m-%d")

    return render_template("reservations_user.html", reservations=reservations, today_date=today_date)


@bp.route('/delete_reservation/<int:reservation_id>', methods=['POST'])
def delete_reservation(reservation_id):
    # Recupera la prenotazione dal database
    reservation = Reservation.query.get_or_404(reservation_id)

    for order in reservation.orders:
        db.session.delete(order)
    # Elimina la prenotazione dal database
    db.session.delete(reservation)
    db.session.commit()

    flash('Prenotazione eliminata con successo.', 'success')
    return redirect(url_for('auth.reservations'))


@bp.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    tables = Table.query.all()  # recupera tutti i tavoli
    if request.method == 'POST':
        # Ottieni i dati dal form
        reservation.date = request.form['data']
        reservation.time = request.form['ora']
        reservation.guests = request.form['persone']
        reservation.table_id = request.form['table_id']
        reservation.note = request.form.get('note')

        # Commit le modifiche nel database
        db.session.commit()

        flash('Prenotazione aggiornata con successo.', 'success')
        return redirect(url_for('auth.admin_dashboard'))

    return render_template('admin_edit_reservation.html', reservation=reservation, tables=tables)


@bp.route('/admin_reservations', methods=['GET', 'POST'])
def view_reservations():
    reservations = Reservation.query.all()  # Ottieni tutte le prenotazioni
    return render_template('view_reservations.html', reservations=reservations)


@bp.route('/tables')
def view_tables():
    tables = Table.query.order_by(Table.number).all()
    return render_template('view_tables.html', tables=tables)


@bp.route("/api/tables/<int:table_id>/reservations/today")
def reservations_today(table_id):
    today = date.today()
    reservations = Reservation.query.filter_by(table_id=table_id).filter(Reservation.date == today).all()
    return jsonify([
        {
            "id": r.id,
            "customer_name": r.user.username,
            "time": r.time,
            "table_id": r.table_id
        } for r in reservations
    ])


@bp.route("/api/tables/status")
def table_status():
    now = datetime.now()
    today = date.today()
    result = []
    tables = Table.query.all()
    for table in tables:
        is_occupied = False
        for r in table.reservations:
            if r.date == today:
                res_time = datetime.combine(r.date, datetime.strptime(r.time, "%H:%M").time())
                if abs((now - res_time).total_seconds()) <= 90 * 60:
                    is_occupied = True
                    break
        result.append({
            "id": table.id,
            "name": table.name,
            "seats": table.seats,
            "occupied": is_occupied
        })
    return jsonify(result)


@bp.route("/api/reservations/today")
def all_reservations_today():
    today = date.today()
    reservations = Reservation.query.filter(Reservation.date == today).all()
    return jsonify([
        {
            "id": r.id,
            "table_id": r.table_id,
            "customer_name": r.user.username if r.user else "Utente sconosciuto",
            "time": datetime.strptime(r.time, "%H:%M").strftime('%H:%M')
        } for r in reservations
    ])


@bp.route('/ordina/<int:reservation_id>')
def menu(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    table = reservation.table
    current_time = datetime.now().time()
    if isinstance(reservation.time, str):
        reservation_time = datetime.strptime(reservation.time, "%H:%M").time()
    elif isinstance(reservation.time, time):
        reservation_time = reservation.time
    if current_time < reservation_time:
        return "Non puoi ancora ordinare. Torna più tardi.", 403

    primi = MenuItem.query.filter_by(category='primo').all()
    secondi = MenuItem.query.filter_by(category='secondo').all()
    bevande = MenuItem.query.filter_by(category='bevanda').all()

    return render_template('ordina.html', primi=primi, secondi=secondi, bevande=bevande, reservation_id=reservation.id,
                           selected_table_id=table.id)


@bp.route('/submit/<int:reservation_id>', methods=['POST'])
def submit(reservation_id):
    import json
    from datetime import datetime

    # Recupera e carica i dati dell'ordine dal form
    data = json.loads(request.form['order_data'])

    # Recupera il table_id dal form (assicurati che sia incluso nel form)
    table_id = request.form.get('table_id')  # Assicurati che table_id sia passato dal form

    # Controlla se table_id è valido
    if not table_id:
        flash("Errore: il tavolo non è stato selezionato.", "danger")
        return redirect(url_for('auth.order_history', reservation_id=reservation_id))

    # Calcola il totale
    total_price = sum(item['price'] * item['quantity'] for item in data)

    # Crea un nuovo ordine
    new_order = Order(
        reservation_id=reservation_id,
        items=json.dumps(data),  # salva tutti gli item come JSON
        total_price=total_price,  # valore richiesto dal database
        created_at=datetime.now(),  # opzionale: assicurati che esista il campo nel modello
        table_id=table_id
    )

    # Salva nel database
    db.session.add(new_order)
    try:
        # operazioni su db
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Errore durante commit:", e)
        flash("Si è verificato un errore durante il commit del nuovo ordine. Riprova")
        return redirect(url_for('auth.dashboard'))
        raise
    finally:
        db.session.close()
    flash("Ordine inviato!", "success")
    return redirect(url_for('auth.order_history', reservation_id=reservation_id))


@bp.route('/orders/<int:reservation_id>', methods=['GET'])
def order_history(reservation_id):
    orders = Order.query.filter_by(reservation_id=reservation_id).all()
    reservation = Reservation.query.get_or_404(reservation_id)
    # Decodifica gli elementi degli ordini in Python
    for order in orders:
        order.items = json.loads(order.items)  # Decodifica JSON direttamente in Python

    return render_template('order_history.html', orders=orders, reservation_id=reservation_id)


@bp.route('/admin_tables', methods=['GET'])
def admin_tables():
    # Ottieni tutti i tavoli occupati
    tables = Table.query.filter_by(is_occupied=True).all()
    return render_template('admin_tables.html.html', tables=tables)


@bp.route('/admin_orders/<int:table_id>', methods=['GET'])
def admin_orders(table_id):
    table = Table.query.get(table_id)
    if not table:
        flash('Tavolo non trovato', 'danger')
        return redirect(url_for('admin_tables'))

    orders = Order.query.filter_by(table_id=table.id).all()
    return render_template('admin_orders.html', table=table, orders=orders)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_old_reservations():
    """
    Elimina tutte le prenotazioni più vecchie di 24 ore.
    """
    now = datetime.now()
    logger.info(f"Esecuzione cleanup prenotazioni alle {now}")

    try:
        reservations = Reservation.query.all()
        deleted_count = 0

        for reservation in reservations:
            try:
                # Costruisce datetime da data e ora
                res_datetime = datetime.strptime(
                    f"{reservation.date} {reservation.time}",
                    "%Y-%m-%d %H:%M"
                )

                if now > res_datetime + timedelta(hours=24):
                    db.session.delete(reservation)
                    deleted_count += 1

            except ValueError as e:
                logger.warning(f"Errore parsing prenotazione ID {reservation.id}: {e}")

        db.session.commit()
        logger.info(f"Pulizia completata. Prenotazioni eliminate: {deleted_count}")

    except Exception as e:
        logger.error(f"Errore durante la pulizia delle prenotazioni: {e}")


@bp.route('/current_reservation/<int:reservation_id>')
def current_reservation(reservation_id):
    # Prendi la prenotazione dal db
    reservation = Reservation.query.get_or_404(reservation_id)
    # Prendi gli ordini associati a quella prenotazione
    orders = Order.query.filter_by(reservation_id=reservation_id).all()
    for order in orders:
        if isinstance(order.items, str):  # se è una stringa JSON
            order.items = json.loads(order.items)
    return render_template('current_reservation.html', reservation=reservation, orders=orders)


@bp.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)

    new_status = request.form.get('status')
    if new_status not in ['pending', 'delivered', 'rejected']:
        flash('Stato non valido.', 'warning')
    else:
        order.status = new_status
        db.session.commit()
        flash('Stato ordine aggiornato.', 'success')

        # Se rifiutato, invialo al "wasTable"
        if new_status == 'rejected':
            was_table_res = get_or_create_was_table_reservation()
            order.reservation_id = was_table_res.id
            db.session.commit()
            flash('Ordine spostato al tavolo wasTable.', 'info')

    return redirect(request.referrer or url_for('auth.current_reservation'))


def get_or_create_was_table_reservation():
    today = date.today()
    was_table = Table.query.filter_by(name='wasTable').first()

    if not was_table:
        raise Exception("Tavolo 'wasTable' non trovato nel database!")

    reservation = Reservation.query.filter_by(date=today, table_id=was_table.id).first()

    if not reservation:
        system_user = User.query.filter_by(email='system@example.com').first()
        if not system_user:
            # Crea un utente sistema se non esiste
            system_user = User(username='Sistema', email='system@example.com', password_hash='...', role='system')
            db.session.add(system_user)
            db.session.commit()

        reservation = Reservation(
            user_id=system_user.id,
            table_id=was_table.id,
            date=today,
            time=datetime.now().strftime('%H:%M'),
            guests=0,
            note='Prenotazione automatica per ordini rifiutati'
        )
        db.session.add(reservation)
        db.session.commit()

    return reservation
