from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

load_dotenv()


# --------------------------------------------------
# Load JSON file
# --------------------------------------------------

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# --------------------------------------------------
# Home
# --------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "message": "AI Meeting-to-Accountability API is running"
    })


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy"
    })


# --------------------------------------------------
# Meeting 4 demo data
# --------------------------------------------------

@app.route("/api/meeting/4")
def meeting_4():

    data = load_json("data/meeting_04.json")

    return jsonify(data)


# --------------------------------------------------
# Analyze meeting
# --------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
def analyze_meeting():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data received"
        }), 400

    title = data.get("title", "")
    transcript = data.get("transcript", "")

    if not transcript.strip():
        return jsonify({
            "error": "Transcript is required"
        }), 400

    # ------------------------------------------------
    # Temporary extraction layer
    #
    # Gemini will be connected here.
    # For now we return a safe demo response.
    # ------------------------------------------------

    result = {
        "meeting_title": title,

        "action_items": [
            {
                "task": "Complete the API integration",
                "owner": "Not specified",
                "deadline": "Not specified",
                "confidence": "Medium",
                "evidence": transcript[:200]
            }
        ],

        "completed_items": [],

        "decisions": [],

        "unresolved_issues": []
    }

    return jsonify(result)


# --------------------------------------------------
# Run server
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )