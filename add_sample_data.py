
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "landlink.db"

# These are real district names, but every sample property location
# and owner below is fictional.
DISTRICTS = [
    "Chengalpattu", "Kanchipuram", "Chennai", "Tiruvallur",
    "Vellore", "Ranipet", "Tirupathur", "Villupuram",
    "Kallakurichi", "Tiruvannamalai", "Salem", "Namakkal",
    "Erode", "Coimbatore", "Tiruppur", "Karur",
    "Tiruchirappalli", "Thanjavur", "Madurai", "Dindigul",
]

LAND_TYPES = [
    "Residential",
    "Agricultural",
    "Commercial",
    "Industrial",
    "Mixed Use",
]

DESCRIPTIONS = [
    "Fictional site for testing a public housing project.",
    "Fictional agricultural property for sample searches.",
    "Sample commercial site for a public service centre.",
    "Fictional industrial property for matching tests.",
    "Sample land for a school or community facility.",
    "Fictional open land for infrastructure planning.",
    "Sample property for budget comparison.",
    "Fictional site for district analytics.",
    "Sample land for testing area requirements.",
    "Fictional property for a public transport project.",
]


def create_samples():
    if not DB_PATH.exists():
        print("Database not found:", DB_PATH)
        print("Run your seller app once to create the database.")
        return

    conn = sqlite3.connect(DB_PATH)

    try:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(land_records)")
        }

        required = {
            "owner_name", "phone", "district", "location",
            "land_area", "area_unit", "price", "land_type",
            "description", "status",
        }

        if not required.issubset(columns):
            print("The land_records table does not have all required columns.")
            print("Check your database structure before continuing.")
            return

        added = 0
        skipped = 0

        for i in range(100):
            number = i + 1

            district = DISTRICTS[i % len(DISTRICTS)]
            zone = (i // len(DISTRICTS)) + 1

            # Different area values from 0.75 to 10.00 acres.
            land_area = round(0.75 + ((i * 13) % 38) * 0.25, 2)

            # Different prices, varying by listing.
            price = 750000 + ((i * 673921) % 14500000)

            land_type = LAND_TYPES[(i * 3 + i // 4) % len(LAND_TYPES)]
            description = DESCRIPTIONS[i % len(DESCRIPTIONS)]

            owner_name = f"Demo Owner {number:03d}"
            phone = f"DEMO-CONTACT-{number:03d}"
            location = f"Fictional Zone {zone:02d}, Site {number:03d}"

            # Mark all examples clearly as fictional demo records.
            demo_description = f"[DEMO DATA] {description}"

            # Avoid inserting the same sample a second time.
            exists = conn.execute(
                """
                SELECT 1
                FROM land_records
                WHERE phone = ?
                  AND description = ?
                LIMIT 1
                """,
                (phone, demo_description),
            ).fetchone()

            if exists:
                skipped += 1
                continue

            conn.execute(
                """
                INSERT INTO land_records (
                    owner_name,
                    phone,
                    district,
                    location,
                    land_area,
                    area_unit,
                    price,
                    land_type,
                    description,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    owner_name,
                    phone,
                    district,
                    location,
                    land_area,
                    "Acres",
                    price,
                    land_type,
                    demo_description,
                    "Available",
                ),
            )

            added += 1

        conn.commit()

        total = conn.execute(
            "SELECT COUNT(*) FROM land_records"
        ).fetchone()[0]

        demo_total = conn.execute(
            """
            SELECT COUNT(*)
            FROM land_records
            WHERE description LIKE '[DEMO DATA]%'
            """
        ).fetchone()[0]

        print("\n===================================")
        print("     BHOOMICON SAMPLE DATA")
        print("===================================")
        print(f"New examples added:       {added}")
        print(f"Existing examples skipped:{skipped}")
        print(f"Total demo examples:      {demo_total}")
        print(f"Total database records:   {total}")
        print("All examples are fictional.")
        print("===================================")

    except sqlite3.Error as error:
        conn.rollback()
        print("Database error:", error)

    finally:
        conn.close()


if __name__ == "__main__":
    create_samples()
