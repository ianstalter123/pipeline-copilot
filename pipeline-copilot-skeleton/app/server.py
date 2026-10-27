"""Dashboard + API: approve / edit / reject drafts, funnel view.

Run: uvicorn app.server:app --reload
Pages: /           inbox with class badges
       /funnel     replies by class, approval stats
Endpoints: POST /api/run            full pipeline over demo inbox (Day 5)
           POST /api/drafts/{id}/decision  {decision: approved|edited|rejected, text?}
"""
import json
import os
import urllib.request
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import HTMLResponse

from app.classify import classify
from app.config import HOT_CLASSES
from app.draft import draft
from app.extract import extract
from app.ingest import ingest_demo
from app.store import connect

app = FastAPI(title="Pipeline Copilot")

INBOX_HTML = """\
<html><body style="font-family:sans-serif;max-width:900px;margin:2em auto">
<h1>Pipeline Copilot — inbox</h1>
<p><a href="/funnel">funnel view</a> · <form action="/api/run" method="post"
style="display:inline"><button>run pipeline</button></form></p>
{rows}
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def inbox():
    conn = connect()
    rows = conn.execute(
        "SELECT r.id, r.sender, r.subject, c.reply_class, c.confidence, d.draft_text, d.decision "
        "FROM replies r LEFT JOIN classifications c ON c.reply_id = r.id "
        "LEFT JOIN drafts d ON d.reply_id = r.id ORDER BY r.id").fetchall()
    conn.close()
    html_rows = "".join(
        f"<div style='border:1px solid #ccc;padding:0.8em;margin:0.5em 0'>"
        f"<b>{sender}</b> — {subject} "
        f"<span style='background:#eef;padding:2px 6px;border-radius:4px'>{cls or 'unclassified'}</span> "
        f"{conf if conf is not None else ''}<br>"
        f"<pre>{(draft_text or '')[:400]}</pre>"
        f"<i>decision: {decision}</i></div>"
        for (_, sender, subject, cls, conf, draft_text, decision) in rows
    )
    return INBOX_HTML.format(rows=html_rows or "<p>No replies yet — run the pipeline.</p>")


@app.get("/funnel", response_class=HTMLResponse)
def funnel():
    conn = connect()
    classes = conn.execute(
        "SELECT reply_class, COUNT(*) FROM classifications GROUP BY reply_class").fetchall()
    decisions = conn.execute(
        "SELECT decision, COUNT(*) FROM drafts GROUP BY decision").fetchall()
    conn.close()
    return ("<html><body style='font-family:sans-serif;max-width:700px;margin:2em auto'>"
            "<h1>Funnel</h1><h2>Replies by class</h2><ul>"
            + "".join(f"<li>{c}: {n}</li>" for c, n in classes)
            + "</ul><h2>Draft decisions</h2><ul>"
            + "".join(f"<li>{d}: {n}</li>" for d, n in decisions)
            + "</ul><p><a href='/'>back to inbox</a></p></body></html>")


@app.post("/api/run")
def run_pipeline():
    ingest_demo()
    conn = connect()
    rows = conn.execute(
        "SELECT id, sender, subject, body FROM replies "
        "WHERE id NOT IN (SELECT reply_id FROM classifications)").fetchall()
    hot = 0
    for reply_id, sender, subject, body in rows:
        cls = classify(body)
        conn.execute(
            "INSERT INTO classifications (reply_id, reply_class, confidence, model, created_at) "
            "VALUES (?,?,?,?,?)",
            (reply_id, cls["class"], cls["confidence"],
             "muse-spark-1.3", datetime.now(timezone.utc).isoformat()))
        ext = extract(body)
        conn.execute(
            "INSERT INTO extractions (reply_id, budget_signal, timeline, pain_point, "
            "decision_maker, next_step) VALUES (?,?,?,?,?,?)",
            (reply_id, ext["budget_signal"], ext["timeline"], ext["pain_point"],
             ext["decision_maker"], ext["next_step"]))
        text = draft(body, cls["class"], cls["language"])
        conn.execute(
            "INSERT INTO drafts (reply_id, draft_text) VALUES (?,?)", (reply_id, text))
        if cls["class"] in HOT_CLASSES:
            hot += 1
            post_slack_alert(reply_id, sender, subject,
                             cls["class"], cls["confidence"], text)
    conn.commit()
    conn.close()
    return {"processed": len(rows), "hot": hot}


def post_slack_alert(reply_id, sender, subject, reply_class, confidence, draft_text):
    """Post a hot-reply alert to Slack, or log it when no webhook is set."""
    url = os.environ.get("SLACK_WEBHOOK_URL", "")
    text = (f"Pipeline Copilot hot reply: {sender} — {subject} "
            f"[{reply_class}] (confidence {confidence})\n"
            f"Draft preview: {(draft_text or '')[:300]}")
    if not url:
        print(f"[slack] no webhook configured; alert not sent for reply {reply_id} ({reply_class})", flush=True)
        return False
    try:
        req = urllib.request.Request(
            url, data=json.dumps({"text": text}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[slack] alert sent for reply {reply_id}: HTTP {resp.status}", flush=True)
        return True
    except Exception as exc:  # noqa: BLE001 - an alert must never break the pipeline
        print(f"[slack] alert failed for reply {reply_id}: {exc}", flush=True)
        return False


class Decision(BaseModel):
    decision: str
    text: Optional[str] = None


@app.post("/api/drafts/{draft_id}/decision")
def decide_draft(draft_id: int, payload: Decision):
    if payload.decision not in ("approved", "edited", "rejected"):
        raise HTTPException(status_code=400, detail="decision must be approved, edited or rejected")
    conn = connect()
    row = conn.execute("SELECT id FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="draft not found")
    if payload.text is not None:
        conn.execute(
            "UPDATE drafts SET decision = ?, draft_text = ?, decided_at = ? WHERE id = ?",
            (payload.decision, payload.text, datetime.now(timezone.utc).isoformat(), draft_id))
    else:
        conn.execute(
            "UPDATE drafts SET decision = ?, decided_at = ? WHERE id = ?",
            (payload.decision, datetime.now(timezone.utc).isoformat(), draft_id))
    conn.commit()
    conn.close()
    return {"draft_id": draft_id, "decision": payload.decision}
