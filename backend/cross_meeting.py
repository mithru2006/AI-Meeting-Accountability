import json
from difflib import SequenceMatcher
from datetime import datetime

MEETING_01 = "data/meeting_01.json"
MEETING_02 = "data/meeting_02.json"
MEETING_03 = "data/meeting_03.json"
MEETING_04 = "data/meeting_04.json"


def load_meeting(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def similarity(text1, text2):
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def find_best_match(task, previous_tasks):
    best_match = None
    best_score = 0

    for previous in previous_tasks:
        score = similarity(task, previous["task"])

        if score > best_score:
            best_score = score
            best_match = previous

    return best_match, best_score


def is_overdue(deadline):
    try:
        due_date = datetime.strptime(deadline, "%B %d, %Y")
        today = datetime(2026, 9, 24)

        return due_date < today

    except ValueError:
        return False


def compare_meetings():

    meeting_01 = load_meeting(MEETING_01)
    meeting_02 = load_meeting(MEETING_02)
    meeting_03 = load_meeting(MEETING_03)
    meeting_04 = load_meeting(MEETING_04)

    previous_tasks = (
        meeting_01.get("action_items", [])
        + meeting_02.get("action_items", [])
        + meeting_03.get("action_items", [])
    )

    completed_tasks = meeting_03.get("completed_items", [])

    current_tasks = (
        meeting_03.get("action_items", [])
        + meeting_04.get("action_items", [])
    )

    print("\n===== CROSS-MEETING ACCOUNTABILITY =====\n")

    # COMPLETED ITEMS
    for completed in completed_tasks:

        match, score = find_best_match(
            completed["task"],
            previous_tasks
        )

        print(f"Task: {completed['task']}")
        print(f"Owner: {completed['owner']}")
        print("Status: COMPLETED")

        if score >= 0.50:
            print(f"Matched Previous Task: {match['task']}")
            print(f"Match Score: {score:.2f}")

        print(f"Evidence: {completed['evidence']}")
        print("-" * 50)

    # CURRENT ACTION ITEMS
    for current in current_tasks:

        match, score = find_best_match(
            current["task"],
            previous_tasks
        )

        # Check overdue first
        if is_overdue(current["deadline"]):
            status = "OVERDUE"

        elif score >= 0.60:
            status = "CARRIED OVER"

        else:
            status = "NEW"

        print(f"Task: {current['task']}")
        print(f"Owner: {current['owner']}")
        print(f"Deadline: {current['deadline']}")
        print(f"Status: {status}")
        print(f"Match Score: {score:.2f}")
        print(f"Evidence: {current['evidence']}")
        print("-" * 50)


if __name__ == "__main__":
    compare_meetings()