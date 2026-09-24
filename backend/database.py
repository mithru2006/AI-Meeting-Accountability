import sqlite3
import json

DATABASE_PATH = "data/commitments.db"
JSON_PATH = "data/meeting_01.json"


def create_database():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commitments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            owner TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'NEW',
            confidence TEXT,
            evidence TEXT,
            meeting_id TEXT
        )
    """)

    connection.commit()
    connection.close()


def save_commitments():
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    for item in data["action_items"]:

        # Check whether this commitment already exists
        cursor.execute("""
            SELECT id FROM commitments
            WHERE task = ? AND owner = ? AND meeting_id = ?
        """, (
            item["task"],
            item["owner"],
            "meeting_01"
        ))

        existing = cursor.fetchone()

        if existing:
            print(f"⚠️ Already exists: {item['task']}")
            continue

        cursor.execute("""
            INSERT INTO commitments
            (task, owner, deadline, status, confidence, evidence, meeting_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item["task"],
            item["owner"],
            item["deadline"],
            "NEW",
            item["confidence"],
            item["evidence"],
            "meeting_01"
        ))

    connection.commit()
    connection.close()

    print("✅ Action items saved to Commitment Memory.")


if __name__ == "__main__":
    create_database()
    save_commitments()

    # Verify saved commitments
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM commitments")
    rows = cursor.fetchall()

    print("\n===== COMMITMENT MEMORY =====\n")

    for row in rows:
        print(row)

    connection.close()