# Smart Expenses

A personal expense tracker built with **Python**, **Streamlit** and **SQLite**. Log what you spend, search and filter it, see where your money goes, and stay on top of a monthly budget.

## Features

- **Add expenses** with date, amount, category and description
- **Edit / delete** any record
- **Filter** by date range and category
- **Insights**: top category, average daily spend, last 7 / 30 day totals, category breakdown and monthly trend charts, and a warning when one category dominates your spending
- **Monthly budget** that is saved between sessions, with a progress bar showing spent vs. remaining
- **Import / export** expenses as CSV

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| UI | Streamlit |
| Database | SQLite (via the built-in `sqlite3` module) |
| Data handling | pandas |

## Getting started

```bash
# 1. create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
streamlit run app.py
```

The app opens at http://localhost:8501. The database file (`expenses.db`) is created automatically on first run. A brand-new database starts with a set of demo expenses and a sample budget so the dashboard isn't empty; delete them anytime and they won't come back.

## Project structure

```
smart_expenses/
├── app.py            # Streamlit UI (pages and layout)
├── db.py             # SQLite data layer (schema and all SQL queries)
├── requirements.txt
└── expenses.db       # created on first run (git-ignored)
```

## Database schema

```sql
CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,                 -- YYYY-MM-DD
    amount      REAL NOT NULL CHECK (amount >= 0),
    category    TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

All queries are parameterized, and aggregations (totals, monthly trends, daily averages) are done in SQL.

## CSV import format

```csv
Date,Amount,Category,Description
2025-01-01,500,Food,Lunch
2025-01-02,1200,Shopping,Clothes
```

## Ideas for the future

- User accounts and login
- Recurring expenses
- Custom categories
- Deployment to Streamlit Community Cloud

## Author

**Vishal Malik** · [GitHub](https://github.com/Vishal-Malik-code)
