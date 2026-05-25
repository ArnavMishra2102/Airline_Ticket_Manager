# ✈️ Airline Ticket Manager
**Flask + MySQL full-stack web application**

---

## 🗂 Project Structure
```
airline_ticket_manager/
├── app.py                  # Flask routes & business logic
├── schema.sql              # MySQL database schema + seed data
├── requirements.txt        # Python dependencies
├── templates/
│   ├── base.html           # Navbar, layout, Bootstrap
│   ├── index.html          # Home / flight search
│   ├── search.html         # Search results
│   ├── book.html           # Booking form
│   ├── confirmation.html   # Boarding pass
│   ├── status.html         # PNR lookup & cancel
│   ├── admin.html          # Admin dashboard
│   ├── flights.html        # Manage all flights
│   └── add_flight.html     # Add new flight form
└── README.md
```

---

## 🚀 Setup & Run

### 1. Install MySQL and create the database
```bash
mysql -u root -p < schema.sql
```

### 2. Set your MySQL credentials in app.py
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "your_password",   # ← change this
    "database": "airline_db",
}
```
Or use environment variables:
```bash
export DB_PASSWORD=your_password
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```
Open `http://localhost:5000` in your browser.

---

## 📋 Features

| Feature | Description |
|---|---|
| **Flight Search** | Search by origin, destination, date, seat class |
| **Best Price** | Automatically highlights cheapest flight |
| **Booking** | Full passenger form, auto-generates PNR + seat |
| **Boarding Pass** | Visual boarding pass with all trip details |
| **PNR Status** | Look up any booking by PNR |
| **Cancellation** | Cancel bookings, seat count restored automatically |
| **Admin Dashboard** | Stats: revenue, bookings, popular routes |
| **Manage Flights** | View all flights, update status |
| **Add Flights** | Admin form to add new flights to the DB |
| **REST API** | `/api/routes` returns route stats as JSON |

---

## 🗄 Database Tables

| Table | Description |
|---|---|
| `airlines` | Airline code, name, country |
| `airports` | IATA code, city, country |
| `flights` | Schedule, seats, price, status |
| `passengers` | Name, email, phone, passport |
| `bookings` | PNR, seat, fare, status — links flight+passenger |

---

## 🌐 Pages

| URL | Page |
|---|---|
| `/` | Search flights |
| `/search?origin=DEL&destination=BOM&date=2026-06-01&seat_class=economy` | Results |
| `/book/<flight_id>` | Booking form |
| `/confirmation/<pnr>` | Boarding pass |
| `/status` | PNR lookup |
| `/admin` | Dashboard |
| `/admin/flights` | All flights |
| `/admin/flights/add` | Add flight |
| `/api/routes` | JSON route stats |
