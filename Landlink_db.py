
import sqlite3
from pathlib import Path

# Always use the database in this project folder
DB_PATH = Path(__file__).with_name("landlink.db")


def connect_db():
    conn = sqlite3.connect(DB_PATH)

    # Create the table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS land_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            district TEXT NOT NULL,
            location TEXT NOT NULL,
            land_area REAL NOT NULL,
            area_unit TEXT NOT NULL,
            price REAL NOT NULL,
            land_type TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Available'
        )
    """)

    # Add status to an existing table if it is missing
    columns = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(land_records)"
        ).fetchall()
    ]

    if "status" not in columns:
        conn.execute("""
            ALTER TABLE land_records
            ADD COLUMN status TEXT DEFAULT 'Available'
        """)

    conn.commit()
    return conn


def get_all_land():
    conn = connect_db()

    records = conn.execute("""
        SELECT id, owner_name, phone, district, location,
               land_area, area_unit, price, land_type,
               description, status
        FROM land_records
        ORDER BY id DESC
    """).fetchall()

    conn.close()
    return records


def update_status(land_id, new_status):
    allowed_statuses = [
        "Available",
        "Under Review",
        "Approved",
        "Rejected"
    ]

    if new_status not in allowed_statuses:
        raise ValueError("Invalid land status")

    conn = connect_db()

    conn.execute("""
        UPDATE land_records
        SET status = ?
        WHERE id = ?
    """, (new_status, land_id))

    conn.commit()
    conn.close()
