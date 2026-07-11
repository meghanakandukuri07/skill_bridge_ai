"""
database.py
Lightweight SQLite persistence layer. Swap the connection string for
MySQL later (e.g. via SQLAlchemy) without changing the rest of the app.
"""

import sqlite3
import pandas as pd

DB_PATH = "data/platform.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT, skills TEXT, education TEXT, interests TEXT,
            location TEXT, availability TEXT, experience TEXT, preferred_domain TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            org_id TEXT PRIMARY KEY,
            org_name TEXT, role TEXT, required_skills TEXT, domain TEXT,
            location TEXT, mode TEXT, duration_weeks INTEGER, eligibility TEXT,
            min_experience TEXT, openings INTEGER, stipend INTEGER, deadline TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, org_id TEXT, match_score REAL,
            status TEXT DEFAULT 'Applied', applied_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(org_id) REFERENCES organizations(org_id)
        )
    """)
    conn.commit()
    conn.close()


def seed_from_csv():
    """Load the generated sample CSVs into the DB (run once, or whenever you regenerate data)."""
    conn = get_connection()
    users = pd.read_csv("data/users.csv")
    orgs = pd.read_csv("data/organizations.csv")
    users.to_sql("users", conn, if_exists="replace", index=False)
    orgs.to_sql("organizations", conn, if_exists="replace", index=False)
    conn.close()


def add_user(user_dict: dict):
    conn = get_connection()
    pd.DataFrame([user_dict]).to_sql("users", conn, if_exists="append", index=False)
    conn.close()


def add_organization(org_dict: dict):
    conn = get_connection()
    pd.DataFrame([org_dict]).to_sql("organizations", conn, if_exists="append", index=False)
    conn.close()


def add_application(user_id: str, org_id: str, match_score: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO applications (user_id, org_id, match_score) VALUES (?, ?, ?)",
        (user_id, org_id, match_score),
    )
    conn.commit()
    conn.close()


def fetch_df(table: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    conn.close()
    return df


if __name__ == "__main__":
    init_db()
    seed_from_csv()
    print("Database initialized and seeded from CSVs -> data/platform.db")
