from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import re
import json
import sqlite3
from datetime import datetime
import os

app = FastAPI(title="Regulatory Report Assistant")

#Allows any frontend to make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "reports.db")

#The backend saves all reports here.
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_text TEXT,
            drug TEXT,
            adverse_events TEXT,
            severity TEXT,
            outcome TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

class ReportIn(BaseModel):
    report: str

class TranslateIn(BaseModel):
    text: str
    lang: str

#These are used to detect adverse events in the report text.
SYMPTOMS_LIST = [
    "nausea","headache","fever","dizziness","rash","vomiting",
    "cough","fatigue","pain","diarrhea","shortness of breath",
    "nauseated","vomited"
]

@app.post("/process-report")
def process_report(data: ReportIn):
    text = data.report or ""
    lower = text.lower()

    # Drug extraction heuristics
    drug = None
    m = re.search(r"[Dd]rug\s+([A-Za-z0-9\-]+)", text)
    if m:
        drug = m.group(1)
    else:
        m2 = re.search(r"(?:taking|took)\s+([A-Z][A-Za-z0-9\-]+)", text)
        if m2:
            drug = m2.group(1)
        else:
            m3 = re.search(r"([A-Z][a-zA-Z0-9]+)\s+(?:tablet|capsule|syrup)", text)
            if m3:
                drug = m3.group(1)
    if not drug:
        drug = "Unknown"

    # Adverse events detection (simple lexicon match)
    adverse_events = []
    for s in SYMPTOMS_LIST:
        if re.search(r"\b" + re.escape(s) + r"\b", lower):
            adverse_events.append(s)
    adverse_events = list(dict.fromkeys(adverse_events))

    # Severity detection (rule-based)
    if "severe" in lower or "intense" in lower or "severely" in lower:
        severity = "severe"
    elif "moderate" in lower or "moderately" in lower:
        severity = "moderate"
    elif "mild" in lower or "mildly" in lower:
        severity = "mild"
    else:
        severity = "unknown"

    # Outcome detection
    if "recovered" in lower or "recovery" in lower or "resolved" in lower:
        outcome = "recovered"
    elif "fatal" in lower or "died" in lower or "death" in lower or "dead" in lower:
        outcome = "fatal"
    elif "ongoing" in lower or "still" in lower or "continues" in lower or "persistent" in lower:
        outcome = "ongoing"
    else:
        outcome = "unknown"

    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO reports (report_text, drug, adverse_events, severity, outcome, created_at) VALUES (?,?,?,?,?,?)",
        (text, drug, json.dumps(adverse_events), severity, outcome, datetime.utcnow().isoformat())
    )
    conn.commit()
    report_id = c.lastrowid
    conn.close()

    return {"id": report_id, "drug": drug, "adverse_events": adverse_events, "severity": severity, "outcome": outcome}

@app.get("/reports")
def get_reports():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, report_text, drug, adverse_events, severity, outcome, created_at FROM reports ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "report": r[1],
            "drug": r[2],
            "adverse_events": json.loads(r[3]) if r[3] else [],
            "severity": r[4],
            "outcome": r[5],
            "created_at": r[6]
        })
    return results

TRANSLATIONS = {
    "fr": {"recovered":"rétabli", "ongoing":"en cours", "fatal":"mort", "unknown":"inconnu"},
    "sw": {"recovered":"amepona","ongoing":"inaendelea","fatal":"amekufa","unknown":"haijulikani"}
}

@app.post("/translate")
def translate_text(data: TranslateIn):
    text = (data.text or "").lower()
    lang = (data.lang or "").lower()
    key = "unknown"
    if "recover" in text:
        key = "recovered"
    elif "fatal" in text or "die" in text or "death" in text:
        key = "fatal"
    elif "ongoing" in text or "still" in text or "persistent" in text:
        key = "ongoing"
    else:
        if text in ["recovered","ongoing","fatal","unknown"]:
            key = text
    translation = TRANSLATIONS.get(lang, {}).get(key, text)
    return {"original": data.text, "lang": lang, "translation": translation}