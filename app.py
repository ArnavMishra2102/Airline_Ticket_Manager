"""
app.py — Airline Ticket Manager
Flask + SQLite full-stack web application
"""

import os
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
app = Flask(__name__)
app.secret_key = "airline_secret_key_2026"

DB_PATH = os.path.join(os.path.dirname(__file__), "airline.db")



def parse_datetime(value):
    """Convert SQLite datetime text into Python datetime for templates."""
    if not value or isinstance(value, datetime):
        return value

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    return value


def row_to_dict(row):
    """Convert sqlite3.Row into dict and parse datetime fields."""
    if row is None:
        return None

    data = dict(row)

    for field in ("departure_time", "arrival_time", "booked_at", "created_at"):
        if field in data:
            data[field] = parse_datetime(data[field])

    return data


def query(sql, params=(), fetchone=False, fetchall=False, commit=False):
    """Execute SQLite query."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()
        cur.execute(sql, params)

        if commit:
            conn.commit()
            return cur.lastrowid

        if fetchone:
            return row_to_dict(cur.fetchone())

        if fetchall:
            return [row_to_dict(row) for row in cur.fetchall()]

        return None

    finally:
        conn.close()


def gen_pnr():
    """Generate a unique 6-char PNR like AB1234."""
    while True:
        pnr = (
            random.choice(string.ascii_uppercase) +
            random.choice(string.ascii_uppercase) +
            str(random.randint(1000, 9999))
        )
        exists = query("SELECT id FROM bookings WHERE pnr=?", (pnr,), fetchone=True)
        if not exists:
            return pnr


def gen_seat(seat_class):
    row = random.randint(1, 30 if seat_class == "economy" else 6)
    col = random.choice("ABCDEF")
    return f"{row}{col}"


# ── Home / Search ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    airports = query("SELECT * FROM airports ORDER BY city", fetchall=True)
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("index.html", airports=airports, now=today)


# ── Search Flights ─────────────────────────────────────────────────────────────
@app.route("/search", methods=["GET"])
def search():
    origin      = request.args.get("origin")
    destination = request.args.get("destination")
    date        = request.args.get("date")
    seat_class  = request.args.get("seat_class", "economy")

    airports = query("SELECT * FROM airports ORDER BY city", fetchall=True)

    if not all([origin, destination, date]):
        return render_template("index.html", airports=airports,
                               now=datetime.now().strftime("%Y-%m-%d"),
                               error="Please fill all search fields.")

    if origin == destination:
        return render_template("index.html", airports=airports,
                               now=datetime.now().strftime("%Y-%m-%d"),
                               error="Origin and destination cannot be the same.")

    price_col = "f.price_economy" if seat_class == "economy" else "f.price_business"

    sql = f"""
        SELECT
            f.id, f.flight_number, f.departure_time, f.arrival_time,
            f.available_seats, f.status,
            {price_col}           AS price,
            al.name               AS airline_name,
            al.code               AS airline_code,
            orig.iata_code        AS origin_code,
            orig.city             AS origin_city,
            dest.iata_code        AS dest_code,
            dest.city             AS dest_city,
            CAST(
                (julianday(f.arrival_time) - julianday(f.departure_time)) * 24 * 60
                AS INTEGER
            ) AS duration_min
        FROM flights f
        JOIN airlines al  ON f.airline_id     = al.id
        JOIN airports orig ON f.origin_id     = orig.id
        JOIN airports dest ON f.destination_id= dest.id
        WHERE orig.iata_code = ?
          AND dest.iata_code = ?
          AND DATE(f.departure_time) = ?
          AND f.available_seats > 0
          AND f.status != 'cancelled'
        ORDER BY price ASC
    """
    flights = query(sql, (origin, destination, date), fetchall=True)

    # Best flight logic
    best = None
    if flights:
        best = min(flights, key=lambda f: f["price"])

    return render_template(
        "search.html",
        flights=flights,
        origin=origin,
        destination=destination,
        date=date,
        seat_class=seat_class,
        airports=airports,
        best=best,
    )


# ── Book Flight ───────────────────────────────────────────────────────────────
@app.route("/book/<int:flight_id>", methods=["GET", "POST"])
def book(flight_id):
    sql = """
        SELECT f.*, al.name AS airline_name, al.code AS airline_code,
               orig.iata_code AS origin_code, orig.city AS origin_city,
               dest.iata_code AS dest_code, dest.city AS dest_city,
               f.price_economy, f.price_business
        FROM flights f
        JOIN airlines al   ON f.airline_id      = al.id
        JOIN airports orig ON f.origin_id        = orig.id
        JOIN airports dest ON f.destination_id   = dest.id
        WHERE f.id = ?
    """
    flight = query(sql, (flight_id,), fetchone=True)
    if not flight:
        flash("Flight not found.", "danger")
        return redirect(url_for("index"))

    seat_class = request.args.get("seat_class", "economy")
    price = float(flight["price_economy"] if seat_class == "economy" else flight["price_business"])

    if request.method == "POST":
        name        = request.form.get("full_name", "").strip()
        email       = request.form.get("email", "").strip()
        phone       = request.form.get("phone", "").strip()
        passport    = request.form.get("passport_no", "").strip()
        seat_class  = request.form.get("seat_class", "economy")

        if not all([name, email, phone]):
            flash("Please fill all required fields.", "danger")
            return render_template("book.html", flight=flight, seat_class=seat_class, price=price)

        price = float(flight["price_economy"] if seat_class == "economy" else flight["price_business"])

        # Upsert passenger
        existing = query("SELECT id FROM passengers WHERE email=?", (email,), fetchone=True)
        if existing:
            passenger_id = existing["id"]
            query("UPDATE passengers SET full_name=?, phone=? WHERE id=?",
                  (name, phone, passenger_id), commit=True)
        else:
            passenger_id = query(
                "INSERT INTO passengers (full_name, email, phone, passport_no) VALUES (?,?,?,?)",
                (name, email, phone, passport or None), commit=True
            )

        pnr        = gen_pnr()
        seat_no    = gen_seat(seat_class)

        # Create booking
        booking_id = query(
            """INSERT INTO bookings
               (pnr, flight_id, passenger_id, seat_class, seat_number, total_fare, status)
               VALUES (?,?,?,?,?,?,'confirmed')""",
            (pnr, flight_id, passenger_id, seat_class, seat_no, price),
            commit=True
        )

        # Decrement available seats
        query("UPDATE flights SET available_seats = available_seats - 1 WHERE id=?",
              (flight_id,), commit=True)

        flash(f"Booking confirmed! Your PNR is {pnr}", "success")
        return redirect(url_for("confirmation", pnr=pnr))

    return render_template("book.html", flight=flight, seat_class=seat_class, price=price)


# ── Booking Confirmation ──────────────────────────────────────────────────────
@app.route("/confirmation/<pnr>")
def confirmation(pnr):
    sql = """
        SELECT b.*, p.full_name, p.email, p.phone,
               f.flight_number, f.departure_time, f.arrival_time,
               al.name AS airline_name, al.code AS airline_code,
               orig.city AS origin_city, orig.iata_code AS origin_code,
               dest.city AS dest_city,  dest.iata_code AS dest_code
        FROM bookings b
        JOIN passengers p  ON b.passenger_id = p.id
        JOIN flights f     ON b.flight_id    = f.id
        JOIN airlines al   ON f.airline_id   = al.id
        JOIN airports orig ON f.origin_id    = orig.id
        JOIN airports dest ON f.destination_id=dest.id
        WHERE b.pnr = ?
    """
    booking = query(sql, (pnr,), fetchone=True)
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("index"))
    return render_template("confirmation.html", booking=booking)


# ── PNR Status ────────────────────────────────────────────────────────────────
@app.route("/status", methods=["GET", "POST"])
def status():
    booking = None
    if request.method == "POST":
        pnr = request.form.get("pnr", "").strip().upper()
        sql = """
            SELECT b.*, p.full_name, p.email, p.phone,
                   f.flight_number, f.departure_time, f.arrival_time, f.status AS flight_status,
                   al.name AS airline_name, al.code AS airline_code,
                   orig.city AS origin_city, orig.iata_code AS origin_code,
                   dest.city AS dest_city,  dest.iata_code AS dest_code
            FROM bookings b
            JOIN passengers p  ON b.passenger_id = p.id
            JOIN flights f     ON b.flight_id    = f.id
            JOIN airlines al   ON f.airline_id   = al.id
            JOIN airports orig ON f.origin_id    = orig.id
            JOIN airports dest ON f.destination_id=dest.id
            WHERE b.pnr = ?
        """
        booking = query(sql, (pnr,), fetchone=True)
        if not booking:
            flash("No booking found with that PNR.", "warning")
    return render_template("status.html", booking=booking)


# ── Cancel Booking ────────────────────────────────────────────────────────────
@app.route("/cancel/<pnr>", methods=["POST"])
def cancel(pnr):
    booking = query("SELECT * FROM bookings WHERE pnr=?", (pnr,), fetchone=True)
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("status"))
    if booking["status"] == "cancelled":
        flash("Booking is already cancelled.", "warning")
        return redirect(url_for("status"))

    query("UPDATE bookings SET status='cancelled' WHERE pnr=?", (pnr,), commit=True)
    query("UPDATE flights SET available_seats = available_seats + 1 WHERE id=?",
          (booking["flight_id"],), commit=True)

    flash(f"Booking {pnr} has been cancelled. Refund will be processed in 5–7 days.", "success")
    return redirect(url_for("status"))


# ── Admin Dashboard ───────────────────────────────────────────────────────────
@app.route("/admin")
def admin():
    stats = {
        "total_flights":   query("SELECT COUNT(*) AS c FROM flights",   fetchone=True)["c"],
        "total_bookings":  query("SELECT COUNT(*) AS c FROM bookings",  fetchone=True)["c"],
        "confirmed":       query("SELECT COUNT(*) AS c FROM bookings WHERE status='confirmed'", fetchone=True)["c"],
        "cancelled":       query("SELECT COUNT(*) AS c FROM bookings WHERE status='cancelled'",fetchone=True)["c"],
        "total_revenue":   query("SELECT COALESCE(SUM(total_fare),0) AS r FROM bookings WHERE status='confirmed'", fetchone=True)["r"],
        "total_passengers":query("SELECT COUNT(*) AS c FROM passengers", fetchone=True)["c"],
    }

    recent_bookings = query("""
        SELECT b.pnr, b.status, b.total_fare, b.seat_class, b.booked_at,
               p.full_name, f.flight_number,
               orig.city AS origin_city, dest.city AS dest_city
        FROM bookings b
        JOIN passengers p  ON b.passenger_id = p.id
        JOIN flights f     ON b.flight_id    = f.id
        JOIN airports orig ON f.origin_id    = orig.id
        JOIN airports dest ON f.destination_id=dest.id
        ORDER BY b.booked_at DESC LIMIT 10
    """, fetchall=True)

    popular_routes = query("""
        SELECT orig.city AS origin, dest.city AS destination,
               COUNT(*) AS bookings
        FROM bookings b
        JOIN flights f     ON b.flight_id    = f.id
        JOIN airports orig ON f.origin_id    = orig.id
        JOIN airports dest ON f.destination_id=dest.id
        WHERE b.status = 'confirmed'
        GROUP BY origin, destination
        ORDER BY bookings DESC LIMIT 5
    """, fetchall=True)

    return render_template("admin.html", stats=stats,
                           recent_bookings=recent_bookings,
                           popular_routes=popular_routes)


# ── All Flights (Admin) ───────────────────────────────────────────────────────
@app.route("/admin/flights")
def admin_flights():
    flights = query("""
        SELECT f.*, al.name AS airline_name, al.code AS airline_code,
               orig.city AS origin_city, orig.iata_code AS origin_code,
               dest.city AS dest_city, dest.iata_code AS dest_code
        FROM flights f
        JOIN airlines al   ON f.airline_id     = al.id
        JOIN airports orig ON f.origin_id       = orig.id
        JOIN airports dest ON f.destination_id  = dest.id
        ORDER BY f.departure_time
    """, fetchall=True)
    return render_template("flights.html", flights=flights)


# ── Add Flight ────────────────────────────────────────────────────────────────
@app.route("/admin/flights/add", methods=["GET", "POST"])
def add_flight():
    airlines = query("SELECT * FROM airlines ORDER BY name", fetchall=True)
    airports = query("SELECT * FROM airports ORDER BY city", fetchall=True)

    if request.method == "POST":
        f = request.form
        query("""
            INSERT INTO flights
            (flight_number, airline_id, origin_id, destination_id,
             departure_time, arrival_time, total_seats, available_seats,
             price_economy, price_business, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            f["flight_number"], f["airline_id"], f["origin_id"], f["destination_id"],
            f["departure_time"].replace("T", " "), f["arrival_time"].replace("T", " "),
            int(f["total_seats"]), int(f["total_seats"]),
            float(f["price_economy"]), float(f["price_business"]),
            f.get("status", "scheduled")
        ), commit=True)
        flash("Flight added successfully!", "success")
        return redirect(url_for("admin_flights"))

    return render_template("add_flight.html", airlines=airlines, airports=airports)


# ── Update Flight Status ──────────────────────────────────────────────────────
@app.route("/admin/flights/<int:fid>/status", methods=["POST"])
def update_flight_status(fid):
    new_status = request.form.get("status")
    query("UPDATE flights SET status=? WHERE id=?", (new_status, fid), commit=True)
    flash("Flight status updated.", "success")
    return redirect(url_for("admin_flights"))


# ── API: Route Stats (JSON) ───────────────────────────────────────────────────
@app.route("/api/routes")
def api_routes():
    data = query("""
        SELECT orig.city AS origin, dest.city AS destination,
               COUNT(*) AS bookings,
               ROUND(AVG(b.total_fare), 2) AS avg_fare
        FROM bookings b
        JOIN flights f     ON b.flight_id    = f.id
        JOIN airports orig ON f.origin_id    = orig.id
        JOIN airports dest ON f.destination_id=dest.id
        WHERE b.status='confirmed'
        GROUP BY origin, destination
        ORDER BY bookings DESC
    """, fetchall=True)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
