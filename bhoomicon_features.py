
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd


# Use the same database as App.py
DB_PATH = Path(__file__).resolve().parent / "landlink.db"

DOCUMENT_STATUSES = [
    "Not Submitted",
    "Pending Review",
    "Verified",
    "Rejected",
]


def get_connection():
    return sqlite3.connect(str(DB_PATH))


def prepare_feature_columns():
    """Add only the new document-verification columns if needed."""
    with get_connection() as conn:
        table = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'land_records'
            """
        ).fetchone()

        if table is None:
            raise RuntimeError(
                "The land_records table was not found. "
                "Check that landlink.db is in your project folder."
            )

        existing_columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(land_records)"
            ).fetchall()
        }

        additions = {
            "document_status": (
                "TEXT NOT NULL DEFAULT 'Not Submitted'"
            ),
            "document_review_note": "TEXT DEFAULT ''",
            "document_reviewed_at": "TEXT DEFAULT ''",
        }

        for column, definition in additions.items():
            if column not in existing_columns:
                conn.execute(
                    f"ALTER TABLE land_records "
                    f"ADD COLUMN {column} {definition}"
                )


def get_document_records():
    """Return land listings and their document-review information."""
    prepare_feature_columns()

    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                id,
                owner_name,
                phone,
                district,
                location,
                land_area,
                area_unit,
                price,
                land_type,
                status,
                document_status,
                document_review_note,
                document_reviewed_at
            FROM land_records
            ORDER BY id DESC
            """,
            conn,
        )


def update_document_status(land_id, new_status, review_note=""):
    """Save a document status and the officer's review note."""
    if new_status not in DOCUMENT_STATUSES:
        raise ValueError("Invalid document verification status.")

    prepare_feature_columns()

    reviewed_at = (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if new_status != "Not Submitted"
        else ""
    )

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE land_records
            SET document_status = ?,
                document_review_note = ?,
                document_reviewed_at = ?
            WHERE id = ?
            """,
            (
                new_status,
                review_note.strip(),
                reviewed_at,
                int(land_id),
            ),
        )

        return cursor.rowcount > 0


def find_matching_land(
    district,
    minimum_area,
    area_unit,
    maximum_price,
    land_type,
):
    """
    Find available land matching the officer's requirements.

    Area is compared after conversion to acres.
    The function does not select or purchase land.
    """

    prepare_feature_columns()

    def to_acres(area, unit):
        unit = str(unit).strip().lower()

        conversions = {
            "acre": 1.0,
            "acres": 1.0,
            "cent": 0.01,
            "cents": 0.01,
            "square feet": 1 / 43560,
            "square foot": 1 / 43560,
            "sq ft": 1 / 43560,
            "sq.ft": 1 / 43560,
            "sqft": 1 / 43560,
            "square metres": 1 / 4046.8564224,
            "square meters": 1 / 4046.8564224,
            "sq m": 1 / 4046.8564224,
            "sqm": 1 / 4046.8564224,
            "hectare": 2.47105381,
            "hectares": 2.47105381,
        }

        return float(area) * conversions.get(unit, 0.0)

    required_acres = to_acres(minimum_area, area_unit)

    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                owner_name,
                district,
                location,
                land_area,
                area_unit,
                price,
                land_type,
                status
            FROM land_records
            WHERE TRIM(status) = 'Available'
            """,
            conn,
        )

    if df.empty:
        return df

    df["price"] = pd.to_numeric(
        df["price"], errors="coerce"
    ).fillna(0)

    df["land_area"] = pd.to_numeric(
        df["land_area"], errors="coerce"
    ).fillna(0)

    df["area_in_acres"] = df.apply(
        lambda row: to_acres(
            row["land_area"], row["area_unit"]
        ),
        axis=1,
    )

    df = df[df["area_in_acres"] >= required_acres]
    df = df[df["price"] <= float(maximum_price)]

    if district != "All districts":
        df = df[
            df["district"].fillna("").str.casefold()
            == district.casefold()
        ]

    if land_type != "All types":
        df = df[
            df["land_type"].fillna("").str.casefold()
            == land_type.casefold()
        ]

    return df.sort_values(
        by=["area_in_acres", "price"],
        ascending=[False, True],
    ).reset_index(drop=True)
