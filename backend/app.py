from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import re
import sqlite3
from datetime import datetime, date, timedelta
from difflib import SequenceMatcher

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# APP SETUP
# ============================================================

app = Flask(__name__)
CORS(app)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "accountability.db")

os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commitments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            owner TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'NEW',
            confidence TEXT,
            evidence TEXT,
            meeting_id TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            transcript TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("SQLite database initialized.")


init_database()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "message": "AI Meeting-to-Accountability API is running"
    })


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "healthy"
    })


# ============================================================
# LOAD JSON
# ============================================================

def load_json(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# MEETING 4 DEMO DATA
# ============================================================

@app.route("/api/meeting/4")
def meeting_4():

    file_path = os.path.join(DATA_DIR, "meeting_04.json")

    if not os.path.exists(file_path):

        return jsonify({
            "error": "Meeting 4 JSON file not found"
        }), 404

    data = load_json(file_path)

    return jsonify(data)


# ============================================================
# LOCAL FALLBACK EXTRACTION
# ============================================================

def fallback_extract_action_items(transcript, title):

    action_items = []
    completed_items = []

    lines = transcript.splitlines()

    for line in lines:

        line = line.strip()

        if not line or ":" not in line:
            continue

        speaker, statement = line.split(":", 1)

        speaker = speaker.strip()
        statement = statement.strip()

        # ----------------------------------------------------
        # COMPLETED TASK
        # ----------------------------------------------------

        if any(word in statement.lower() for word in [
            "completed",
            "finished",
            "submitted",
            "already done"
        ]):

            completed_items.append({
                "task": statement,
                "owner": speaker,
                "evidence": line
            })

            continue

        # ----------------------------------------------------
        # COMMITMENT
        # ----------------------------------------------------

        commitment = re.search(
            r"(?:I will|I'll|I can)\s+(.+?)(?:\s+by\s+(.+))?$",
            statement,
            re.IGNORECASE
        )

        if commitment:

            task = commitment.group(1).strip()

            deadline = (
                commitment.group(2).strip()
                if commitment.group(2)
                else "Not specified"
            )

            action_items.append({

                "task": task,

                "owner": speaker,

                "deadline": deadline,

                "confidence": "High",

                "evidence": line
            })

    return {

        "meeting_title": title,

        "action_items": action_items,

        "completed_items": completed_items,

        "decisions": [],

        "unresolved_issues": []
    }


# ============================================================
# GEMINI EXTRACTION
# ============================================================

def extract_action_items(transcript, title):

    if client is None:

        print("Gemini API key is not configured.")
        print("Using local fallback extraction...")

        result = fallback_extract_action_items(
            transcript,
            title
        )

        result["error"] = (
            "Gemini API key is not configured. "
            "Used safe local fallback."
        )

        return result

    prompt = f"""
You are an enterprise meeting accountability assistant.

Analyze the following meeting transcript.

Extract ONLY information explicitly supported by the transcript.

Rules:

1. Never invent an owner.
2. Never invent a deadline.
3. Never invent a task.
4. If owner is unknown, use "Not specified".
5. If deadline is unknown, use "Not specified".
6. If responsibility is ambiguous, use "Needs review".
7. Keep evidence as the exact relevant sentence from the transcript.
8. If a task is explicitly completed, put it in completed_items.
9. Do not put completed tasks in action_items.
10. Return ONLY valid JSON.

Required JSON structure:

{{
    "meeting_title": "{title}",
    "action_items": [
        {{
            "task": "",
            "owner": "",
            "deadline": "",
            "confidence": "",
            "evidence": ""
        }}
    ],
    "completed_items": [
        {{
            "task": "",
            "owner": "",
            "evidence": ""
        }}
    ],
    "decisions": [],
    "unresolved_issues": []
}}

Meeting transcript:

{transcript}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0
            )
        )

        text = response.text.strip()

        if text.startswith("```json"):
            text = text[7:]

        if text.endswith("```"):
            text = text[:-3]

        result = json.loads(text.strip())

        return result

    except Exception as error:

        print("Gemini error:", error)
        print("Using local fallback extraction...")

        result = fallback_extract_action_items(
            transcript,
            title
        )

        result["error"] = (
            "Gemini unavailable. "
            "Used safe local fallback."
        )

        return result


# ============================================================
# TEXT SIMILARITY
# ============================================================

def similarity(text1, text2):

    if not text1 or not text2:
        return 0

    return SequenceMatcher(
        None,
        text1.lower().strip(),
        text2.lower().strip()
    ).ratio()


# ============================================================
# FIND MATCHING COMMITMENT
# ============================================================

def find_matching_commitment(task):

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM commitments
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    best_match = None
    best_score = 0

    for row in rows:

        score = similarity(
            task,
            row["task"]
        )

        if score > best_score:

            best_score = score
            best_match = row

    if best_score >= 0.60:

        return best_match, best_score

    return None, best_score


# ============================================================
# INSERT COMMITMENT
# ============================================================

def insert_commitment(
    task,
    owner,
    deadline,
    status,
    confidence,
    evidence,
    meeting_id
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO commitments
        (
            task,
            owner,
            deadline,
            status,
            confidence,
            evidence,
            meeting_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        task,

        owner,

        deadline,

        status,

        confidence,

        evidence,

        meeting_id,

        datetime.now().isoformat()
    ))

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return new_id


# ============================================================
# MARK PREVIOUS COMMITMENT AS CARRIED OVER
# ============================================================

def mark_carried_over(commitment_id):

    conn = get_db()

    conn.execute("""
        UPDATE commitments
        SET status = 'CARRIED OVER'
        WHERE id = ?
    """, (commitment_id,))

    conn.commit()
    conn.close()


# ============================================================
# MARK COMMITMENT COMPLETED
# ============================================================

def mark_completed(commitment_id):

    conn = get_db()

    conn.execute("""
        UPDATE commitments
        SET status = 'COMPLETED'
        WHERE id = ?
    """, (commitment_id,))

    conn.commit()
    conn.close()


# ============================================================
# PROCESS NEW MEETING
# ============================================================

def save_meeting_to_database(title, transcript, result):

    meeting_id = f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    conn = get_db()

    conn.execute("""
        INSERT INTO meetings
        (
            title,
            transcript,
            created_at
        )
        VALUES (?, ?, ?)
    """, (
        title,
        transcript,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    # --------------------------------------------------------
    # ACTION ITEMS
    # --------------------------------------------------------

    for item in result.get("action_items", []):

        task = item.get("task", "Not specified")
        owner = item.get("owner", "Not specified")
        deadline = item.get("deadline", "Not specified")
        confidence = item.get("confidence", "Medium")
        evidence = item.get("evidence", "")

        previous, score = find_matching_commitment(task)

        if previous:

            # Existing unfinished task
            if previous["status"] != "COMPLETED":

                mark_carried_over(previous["id"])

                status = "CARRIED OVER"

            # Previously completed task → new commitment
            else:

                status = "NEW"

        else:

            status = "NEW"

        insert_commitment(
            task=task,
            owner=owner,
            deadline=deadline,
            status=status,
            confidence=confidence,
            evidence=evidence,
            meeting_id=meeting_id
        )

    # --------------------------------------------------------
    # COMPLETED ITEMS
    # --------------------------------------------------------

    for item in result.get("completed_items", []):

        task = item.get("task", "Not specified")
        owner = item.get("owner", "Not specified")
        evidence = item.get("evidence", "")

        previous, score = find_matching_commitment(task)

        if previous and previous["status"] != "COMPLETED":

            # Change the existing commitment itself
            # to COMPLETED.
            conn = get_db()

            conn.execute("""
                UPDATE commitments
                SET
                    status = 'COMPLETED',
                    owner = ?,
                    evidence = ?,
                    meeting_id = ?
                WHERE id = ?
            """, (
                owner,
                evidence,
                meeting_id,
                previous["id"]
            ))

            conn.commit()
            conn.close()

        else:

            # No previous commitment found.
            # Store it as a new completed record.
            insert_commitment(
                task=task,
                owner=owner,
                deadline="Not specified",
                status="COMPLETED",
                confidence="High",
                evidence=evidence,
                meeting_id=meeting_id
            )

# ============================================================
# DATE PARSER
# ============================================================

def parse_deadline(deadline):

    if not deadline:
        return None

    deadline = deadline.strip().lower()

    today = date.today()

    # --------------------------------------------------------
    # EXPLICIT DATE
    # Example: September 21, 2026
    # --------------------------------------------------------

    formats = [
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y"
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                deadline,
                fmt
            ).date()

        except ValueError:
            continue

    # --------------------------------------------------------
    # RELATIVE DEADLINES
    # --------------------------------------------------------

    if deadline == "today":
        return today

    if deadline == "tomorrow":
        from datetime import timedelta
        return today + timedelta(days=1)

    # --------------------------------------------------------
    # WEEKDAY DEADLINES
    # Example: Friday
    # --------------------------------------------------------

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    if deadline in weekdays:

        target_day = weekdays[deadline]
        current_day = today.weekday()

        days_ahead = (target_day - current_day) % 7

        return today + timedelta(days=days_ahead)

    return None


# ============================================================
# GET ALL COMMITMENTS
# ============================================================


@app.route("/api/commitments")
def get_commitments():

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM commitments
        ORDER BY id ASC
    """).fetchall()

    conn.close()

    commitments = []

    today = date.today()

    for row in rows:

        item = dict(row)

        status = item["status"]

        # ----------------------------------------------------
        # AUTOMATIC OVERDUE DETECTION
        # ----------------------------------------------------

        if status != "COMPLETED":

            deadline_date = parse_deadline(
                item["deadline"]
            )

            if deadline_date and deadline_date < today:
                status = "OVERDUE"

        item["status"] = status

        commitments.append(item)

    # IMPORTANT:
    # return must be OUTSIDE the for loop

    return jsonify({
        "commitments": commitments
    })

# ============================================================
# GET MEETINGS
# ============================================================

@app.route("/api/meetings")
def get_meetings():

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM meetings
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify({

        "meetings": [
            dict(row)
            for row in rows
        ]
    })


# ============================================================
# GET DATABASE SUMMARY
# ============================================================

@app.route("/api/dashboard")
def dashboard():

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM commitments
        ORDER BY id ASC
    """).fetchall()

    conn.close()

    today = date.today()

    commitments = []

    for row in rows:

        item = dict(row)

        status = item["status"]

        if status != "COMPLETED":

            deadline_date = parse_deadline(
                item["deadline"]
            )

            if deadline_date and deadline_date < today:

                status = "OVERDUE"

        item["status"] = status

        commitments.append(item)


    total = len(commitments)

    completed = sum(
        1
        for item in commitments
        if item["status"] == "COMPLETED"
    )

    carried_over = sum(
        1
        for item in commitments
        if item["status"] == "CARRIED OVER"
    )

    overdue = sum(
        1
        for item in commitments
        if item["status"] == "OVERDUE"
    )

    new_items = sum(
        1
        for item in commitments
        if item["status"] == "NEW"
    )


    return jsonify({

        "total": total,

        "completed": completed,

        "carried_over": carried_over,

        "overdue": overdue,

        "new": new_items,

        "commitments": commitments
    })


# ============================================================
# ANALYZE MEETING
# ============================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_meeting():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "No data received"
        }), 400


    title = data.get(
        "title",
        ""
    )

    transcript = data.get(
        "transcript",
        ""
    )


    if not transcript.strip():

        return jsonify({
            "error": "Transcript is required"
        }), 400


    # --------------------------------------------------------
    # AI EXTRACTION
    # --------------------------------------------------------

    result = extract_action_items(
        transcript,
        title
    )


    # --------------------------------------------------------
    # SAVE TO SQLITE
    # --------------------------------------------------------

    save_meeting_to_database(
        title,
        transcript,
        result
    )


    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return jsonify(result)


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )