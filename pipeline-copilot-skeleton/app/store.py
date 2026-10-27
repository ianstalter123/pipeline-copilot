"""SQLite store: replies, classifications, extractions, drafts, decisions."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "pipeline_copilot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY,
    external_id TEXT UNIQUE,
    sender TEXT, subject TEXT, body TEXT, received_at TEXT,
    language TEXT DEFAULT 'unknown'
);
CREATE TABLE IF NOT EXISTS classifications (
    reply_id INTEGER PRIMARY KEY REFERENCES replies(id),
    reply_class TEXT, confidence REAL, model TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS extractions (
    reply_id INTEGER PRIMARY KEY REFERENCES replies(id),
    budget_signal TEXT, timeline TEXT, pain_point TEXT,
    decision_maker TEXT, next_step TEXT
);
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY,
    reply_id INTEGER REFERENCES replies(id),
    draft_text TEXT, decision TEXT DEFAULT 'pending',  -- pending|approved|edited|rejected
    decided_at TEXT
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    return conn
