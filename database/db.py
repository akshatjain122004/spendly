import sqlite3
import os
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "expense_tracker.db")

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if existing > 0:
        conn.close()
        return

    password_hash = generate_password_hash("demo123")
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cursor.lastrowid

    # 8 expenses: one per category (7) + one repeat (Food), spread across the current month
    today = date.today()
    days_in_month = (today.replace(month=today.month % 12 + 1, day=1) - timedelta(days=1)).day \
        if today.month != 12 else 31
    spread_days = [round(i * (days_in_month - 1) / 7) + 1 for i in range(8)]

    expenses = [
        (12.50, "Food", "Groceries"),
        (8.00, "Transport", "Bus fare"),
        (45.00, "Bills", "Electricity bill"),
        (30.00, "Health", "Pharmacy"),
        (15.00, "Entertainment", "Movie ticket"),
        (60.00, "Shopping", "New shoes"),
        (20.00, "Other", "Miscellaneous"),
        (25.00, "Food", "Restaurant dinner"),
    ]

    rows = [
        (user_id, amount, category, today.replace(day=day).strftime("%Y-%m-%d"), description)
        for day, (amount, category, description) in zip(spread_days, expenses)
    ]

    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
