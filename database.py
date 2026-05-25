"""
database.py — SQLite setup & seed data
Run this once:

python database.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "airline.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS airlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS airports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iata_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number TEXT NOT NULL,
    airline_id INTEGER NOT NULL,
    origin_id INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_time TEXT NOT NULL,
    total_seats INTEGER NOT NULL DEFAULT 180,
    available_seats INTEGER NOT NULL DEFAULT 180,
    price_economy REAL NOT NULL,
    price_business REAL NOT NULL,
    status TEXT DEFAULT 'scheduled',

    FOREIGN KEY (airline_id) REFERENCES airlines(id),
    FOREIGN KEY (origin_id) REFERENCES airports(id),
    FOREIGN KEY (destination_id) REFERENCES airports(id)
);

CREATE TABLE IF NOT EXISTS passengers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    passport_no TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pnr TEXT NOT NULL UNIQUE,
    flight_id INTEGER NOT NULL,
    passenger_id INTEGER NOT NULL,
    seat_class TEXT DEFAULT 'economy',
    seat_number TEXT,
    total_fare REAL NOT NULL,
    status TEXT DEFAULT 'confirmed',
    booked_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (flight_id) REFERENCES flights(id),
    FOREIGN KEY (passenger_id) REFERENCES passengers(id)
);
"""


SEED = """
INSERT OR IGNORE INTO airlines (code, name, country) VALUES
('AI', 'Air India', 'India'),
('6E', 'IndiGo', 'India'),
('SG', 'SpiceJet', 'India'),
('UK', 'Vistara', 'India'),
('EK', 'Emirates', 'UAE'),
('QR', 'Qatar Airways', 'Qatar'),
('SQ', 'Singapore Airlines', 'Singapore'),
('BA', 'British Airways', 'UK'),
('AA', 'American Airlines', 'USA'),
('G8', 'GoAir', 'India');

INSERT OR IGNORE INTO airports (iata_code, name, city, country) VALUES
('DEL', 'Indira Gandhi International', 'New Delhi', 'India'),
('BOM', 'Chhatrapati Shivaji International', 'Mumbai', 'India'),
('CCU', 'Netaji Subhas Chandra Bose International', 'Kolkata', 'India'),
('MAA', 'Chennai International', 'Chennai', 'India'),
('BLR', 'Kempegowda International', 'Bengaluru', 'India'),
('HYD', 'Rajiv Gandhi International', 'Hyderabad', 'India'),
('GOI', 'Goa International', 'Goa', 'India'),
('DXB', 'Dubai International', 'Dubai', 'UAE'),
('LHR', 'Heathrow Airport', 'London', 'UK'),
('JFK', 'John F. Kennedy International', 'New York', 'USA'),
('SIN', 'Changi Airport', 'Singapore', 'Singapore'),
('DOH', 'Hamad International', 'Doha', 'Qatar');
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.executescript(SCHEMA)
    conn.executescript(SEED)

    conn.commit()
    conn.close()

    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    init_db()