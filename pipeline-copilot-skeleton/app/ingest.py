"""Ingest: load demo inbox (or Gmail threads later) and normalize into the store."""
import json
from pathlib import Path

from app.store import connect

HERE = Path(__file__).resolve().parent.parent


def ingest_demo(path: Path | None = None) -> int:
    inbox = path or (HERE / "data" / "demo-inbox.json")
    data = json.loads(inbox.read_text(encoding="utf-8"))
    replies = data if isinstance(data, list) else data.get("replies", [])
    conn = connect()
    n = 0
    for i, r in enumerate(replies):
        conn.execute(
            "INSERT OR IGNORE INTO replies "
            "(external_id, sender, subject, body, language) VALUES (?,?,?,?,?)",
            (
                r.get("id", f"demo-{i}"),
                (r.get("from_name") or r.get("sender") or "unknown"),
                r.get("subject", ""),
                r.get("body") or r.get("text", ""),
                r.get("language", "unknown"),
            ),
        )
        n += conn.total_changes > 0
    conn.commit()
    conn.close()
    return n


if __name__ == "__main__":
    print(f"ingested {ingest_demo()} replies")
