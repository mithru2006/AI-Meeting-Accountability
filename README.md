# AI Meeting-to-Accountability System

An AI-powered system that converts meeting transcripts into structured action items and tracks their progress across multiple meetings.

## 🚀 Problem

Important commitments made during meetings are often forgotten or lost in long transcripts.

For example:

> "Mithru will complete the frontend by Friday."

Our system identifies:

- What needs to be done
- Who is responsible
- When it is due
- Evidence from the original transcript
- Whether the task is new, carried over, completed, or overdue

## 💡 Solution

The AI Meeting-to-Accountability System transforms meeting conversations into an accountability tracker.

### Workflow

Meeting Transcript  
↓  
AI Extraction  
↓  
Action Items + Owners + Deadlines  
↓  
Commitment Memory  
↓  
Cross-Meeting Matching  
↓  
Accountability Status  
↓  
Dashboard

## ✨ Key Features

- 🤖 AI-based action item extraction
- 👤 Automatic owner identification
- 📅 Deadline extraction
- 🔄 Cross-meeting commitment tracking
- 🆕 New task detection
- ↪️ Carried-over task detection
- ✅ Completed task detection
- ⚠️ Overdue task detection
- 🔎 Evidence/audit trail
- 🛡️ Hallucination-aware extraction
- 📊 Accountability dashboard

## 🧠 Example

### Meeting 1

> "Mithru: I will complete the project report by Friday."

The system creates:

| Task | Owner | Deadline | Status |
|---|---|---|---|
| Complete the project report | Mithru | Friday | NEW |

### Meeting 2

If the report is still pending:

| Task | Owner | Deadline | Status |
|---|---|---|---|
| Complete the project report | Mithru | Monday | CARRIED OVER |

### Meeting 3

If the transcript says:

> "The project report is completed and submitted."

The system marks it:

| Task | Owner | Status |
|---|---|---|
| Complete the project report | Mithru | COMPLETED |

### Meeting 4

If a task passes its deadline and remains incomplete:

| Task | Owner | Status |
|---|---|---|
| Complete the final demo video | Mohan | OVERDUE |

## 🏗️ Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask
- Flask-CORS

### AI
- Google Gemini API
- Natural language processing

### Database
- SQLite

### Development Tools
- VS Code
- Git
- GitHub

## 📁 Project Structure

```text
AI-Meeting-Accountability/
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── cross_meeting.py
│   ├── extract_meeting.py
│   └── gemini_test.py
│
├── data/
│   ├── meeting_01.txt
│   ├── meeting_01.json
│   ├── meeting_02.txt
│   ├── meeting_02.json
│   ├── meeting_03.txt
│   ├── meeting_03.json
│   ├── meeting_04.txt
│   └── meeting_04.json
│
├── frontend/
│   └── index.html
│
├── prompts/
│
├── tests/
│
├── .gitignore
└── README.md