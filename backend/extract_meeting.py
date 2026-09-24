import os
import json
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
		raise ValueError("GEMINI_API_KEY not found in .env")

# Connect to Gemini
client = genai.Client(api_key=api_key)

# Read meeting transcript
with open("data/meeting_04.txt", "r", encoding="utf-8") as file:
		transcript = file.read()

# Prompt
prompt = f"""
You are an AI Meeting-to-Accountability Assistant.

Analyze the meeting transcript below.

Extract ONLY information explicitly mentioned in the transcript.

Return ONLY valid JSON.
Do not include Markdown.
Do not include explanations outside the JSON.

Use exactly this structure:

{{
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

Rules:

1. Never invent information.
2. If the owner is not mentioned, use "Not specified".
3. If the deadline is not mentioned, use "Not specified".
4. If the information is ambiguous, use "Needs review".
5. Confidence must be "High", "Medium", or "Low".
6. Evidence must contain the relevant sentence from the transcript.
7. Keep the wording faithful to the transcript.
8. If a task was assigned and its deadline has already passed, but the transcript explicitly says it is still not completed, put it in "action_items".
9. A statement such as "was due on [date], but is still not completed" is an action item, not an unresolved issue.
10. For overdue action items, extract the original deadline exactly as stated.
11. Do not put an overdue task into "completed_items".
12. Use the evidence sentence from the transcript.

Meeting transcript:

{transcript}
"""

# Ask Gemini to extract structured information
import time

# Try Gemini up to 3 times if the server is temporarily unavailable
for attempt in range(3):
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        break

    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")

        if attempt < 2:
            print("Waiting 5 seconds before trying again...")
            time.sleep(5)
        else:
            raise

# Get AI response
result = response.text.strip()

# Convert response into Python JSON
try:
    data = json.loads(result)

    # Save structured data to JSON file
    with open("data/meeting_04.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print("\n===== STRUCTURED MEETING DATA =====\n")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    print("\n✅ Meeting data saved to data/meeting_04.json")

except json.JSONDecodeError:
    print("\nGemini did not return valid JSON.")
    print("\nRaw response:")
    print(result)
