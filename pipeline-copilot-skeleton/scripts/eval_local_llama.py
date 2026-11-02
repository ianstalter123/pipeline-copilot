"""Local open-weights eval for Pipeline Copilot.

Runs the same 30-reply labeled set through a local Ollama model using its
OpenAI-compatible endpoint, then reports accuracy and latency.

Default model: llama3.1:8b
Default endpoint: http://localhost:11434/v1

Usage, from pipeline-copilot-skeleton/:
    ollama pull llama3.1:8b
    python3 scripts/eval_local_llama.py

No real API key is used or printed; Ollama accepts a placeholder locally.
"""
import json
import os
import time
import urllib.request
from collections import Counter
from pathlib import Path

REPLY_CLASSES = [
    "interested", "meeting-ready", "objection-price", "objection-timing",
    "objection-incumbent", "not-now", "wrong-person", "out-of-office",
    "unsubscribe", "other",
]

CLASSIFY_SYSTEM = (
    "You classify B2B sales-email replies for a reply-intelligence agent. "
    "Return exactly one class from the enum, the reply's language (en/es/zh), "
    "and a confidence 0..1. Classify the reply's intent, not its politeness: "
    "a polite 'not this quarter' is not-now, a delegate/forward note is "
    "wrong-person even when polite. Allowed reply_class values, spelled "
    "exactly with hyphens: interested, meeting-ready, objection-price, "
    "objection-timing, objection-incumbent, not-now, wrong-person, "
    "out-of-office, unsubscribe, other. Return only JSON with keys "
    "reply_class, language, confidence."
)

BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
MODEL = os.environ.get("LOCAL_MODEL", "llama3.1:8b")


def find_dataset() -> Path:
    candidates = [
        Path.cwd() / "data" / "demo-inbox.json",
        Path(__file__).resolve().parent.parent / "data" / "demo-inbox.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find data/demo-inbox.json")


def load_dataset():
    path = find_dataset()
    data = json.loads(path.read_text(encoding="utf-8"))
    replies = data if isinstance(data, list) else data.get("replies", [])
    print(f"dataset={path} replies={len(replies)}")
    return replies


def body_of(reply: dict) -> str:
    return reply.get("body") or reply.get("text") or json.dumps(reply, ensure_ascii=False)


def expected_of(reply: dict):
    lbl = reply.get("label")
    expected = lbl.get("primary_class") if isinstance(lbl, dict) else lbl
    return expected or reply.get("expected_class") or reply.get("class")


def call_ollama(reply_body: str) -> dict:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": CLASSIFY_SYSTEM},
            {"role": "user", "content": reply_body[:2000]},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    cls = (parsed.get("reply_class") or parsed.get("class") or "").strip().lower().replace("_", "-")
    parsed["reply_class"] = cls
    if cls not in REPLY_CLASSES:
        raise ValueError(f"bad class from model: {cls!r}; raw={content[:200]!r}")
    return parsed


def main() -> int:
    replies = load_dataset()
    correct = 0
    total = 0
    latencies = []
    errors = Counter()
    print(f"model={MODEL} base_url={BASE_URL}\n")
    for i, reply in enumerate(replies):
        expected = expected_of(reply)
        if not expected:
            print(f"[{i}] no expected label - skipping")
            continue
        start = time.perf_counter()
        try:
            parsed = call_ollama(body_of(reply))
            got = parsed.get("reply_class") or parsed.get("class")
        except Exception as e:  # noqa: BLE001
            print(f"[{i}] CALL FAILED: {e}")
            errors["call_failed"] += 1
            continue
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)
        total += 1
        ok = got == expected
        correct += ok
        mark = "OK" if ok else "MISS"
        print(f"{mark} [{i}] expected={expected:20s} got={got:20s} {elapsed:.2f}s")
        if not ok:
            errors[f"{expected}->{got}"] += 1
    acc = (100.0 * correct / total) if total else 0.0
    avg = (sum(latencies) / len(latencies)) if latencies else 0.0
    print(f"\naccuracy: {correct}/{total} = {acc:.1f}%")
    print(f"avg latency: {avg:.2f}s over {len(latencies)} calls")
    if errors:
        print("misses/errors:", dict(errors.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
