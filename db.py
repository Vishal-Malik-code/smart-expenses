"""Data layer: every SQL statement in the app lives in this file."""

import sqlite3
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).with_name("expenses.db")
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Health", "Other"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,                     -- stored as YYYY-MM-DD
    amount      REAL NOT NULL CHECK (amount >= 0),
    category    TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

INSERT = "INSERT INTO expenses (date, amount, category, description) VALUES (?, ?, ?, ?)"


# ---- Helpers: open a connection, run SQL, close it again ---------------------

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us read columns by name: row["amount"]
    return conn


def _run(sql, params=()):
    """Run one statement, save the change, and return any rows it produced."""
    with closing(_connect()) as conn, conn:  # `with conn` commits when done
        return conn.execute(sql, params).fetchall()


def _table(sql, params=()):
    """Run a SELECT and return the result as a pandas DataFrame."""
    with closing(_connect()) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def init_db():
    with closing(_connect()) as conn, conn:
        conn.executescript(SCHEMA)
    _seed_demo_data()


# (days ago, amount, category, description), used to fill a brand-new database
DEMO_EXPENSES = [
    (0, 180, "Food", "Lunch with friends"), (1, 60, "Travel", "Metro card recharge"),
    (2, 1200, "Shopping", "New headphones"), (3, 250, "Food", "Groceries"),
    (4, 799, "Bills", "Internet bill"), (6, 90, "Food", "Coffee and snacks"),
    (8, 450, "Health", "Pharmacy"), (10, 320, "Travel", "Cab to airport"),
    (12, 2100, "Shopping", "Shoes"), (15, 150, "Food", "Dinner"),
    (18, 1500, "Bills", "Electricity bill"), (21, 700, "Health", "Gym membership"),
    (25, 380, "Food", "Weekend brunch"), (28, 240, "Travel", "Train tickets"),
    (33, 1800, "Shopping", "Clothes"), (38, 850, "Bills", "Phone recharge"),
    (42, 120, "Other", "Stationery"), (47, 600, "Food", "Party takeout"),
    (55, 950, "Travel", "Bus trip"), (62, 300, "Other", "Gift"),
]


def _seed_demo_data():
    """Give a brand-new database some demo data. Runs once, so deleting it later sticks."""
    if _run("SELECT 1 FROM settings WHERE key = 'seeded'"):
        return
    if not _run("SELECT 1 FROM expenses LIMIT 1"):  # only if the user has no data yet
        today = date.today()
        add_many((str(today - timedelta(days=ago)), amt, cat, desc) for ago, amt, cat, desc in DEMO_EXPENSES)
        set_budget(8000)
    _run("INSERT INTO settings (key, value) VALUES ('seeded', '1')")


# ---- Create ------------------------------------------------------------------

def add_expense(day, amount, category, description=""):
    _run(INSERT, (str(day), amount, category, description))


def add_many(rows):
    """rows: an iterable of (date, amount, category, description) tuples."""
    with closing(_connect()) as conn, conn:
        conn.executemany(INSERT, rows)


# ---- Read --------------------------------------------------------------------

def get_expenses(start=None, end=None, categories=None):
    """All expenses, newest first, optionally limited by date range and categories."""
    conditions, params = [], []
    if start:
        conditions.append("date >= ?")
        params.append(str(start))
    if end:
        conditions.append("date <= ?")
        params.append(str(end))
    if categories:
        conditions.append(f"category IN ({', '.join('?' * len(categories))})")
        params += categories

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    df = _table(f"SELECT * FROM expenses {where} ORDER BY date DESC, id DESC", params)
    df["date"] = pd.to_datetime(df["date"])
    return df


def get_expense(expense_id):
    return _run("SELECT * FROM expenses WHERE id = ?", (expense_id,))[0]


def category_totals():
    return _table(
        "SELECT category, SUM(amount) AS total FROM expenses "
        "GROUP BY category ORDER BY total DESC"
    )


def monthly_totals():
    return _table(
        "SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS total "
        "FROM expenses GROUP BY month ORDER BY month"
    )


def total_between(start, end):
    row = _run(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE date BETWEEN ? AND ?",
        (str(start), str(end)),
    )[0]
    return row["total"]


def daily_average():
    """Average spend on the days that have at least one expense."""
    row = _run(
        "SELECT AVG(day_total) AS avg FROM "
        "(SELECT SUM(amount) AS day_total FROM expenses GROUP BY date)"
    )[0]
    return row["avg"] or 0.0


# ---- Update / Delete ---------------------------------------------------------

def update_expense(expense_id, day, amount, category, description):
    _run(
        "UPDATE expenses SET date = ?, amount = ?, category = ?, description = ? WHERE id = ?",
        (str(day), amount, category, description, expense_id),
    )


def delete_expense(expense_id):
    _run("DELETE FROM expenses WHERE id = ?", (expense_id,))


# ---- Monthly budget (kept in the settings table) -----------------------------

def get_budget():
    rows = _run("SELECT value FROM settings WHERE key = 'monthly_budget'")
    return float(rows[0]["value"]) if rows else 0.0


def set_budget(amount):
    # "Upsert": insert the row, or update it if the key already exists.
    _run(
        "INSERT INTO settings (key, value) VALUES ('monthly_budget', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(amount),),
    )
