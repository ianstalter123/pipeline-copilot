"""Eval harness: run the 30-reply labeled set through classify(), report accuracy."""
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.classify import classify

HERE = Path(__file__).resolve().parent.parent


def load_dataset():
    path = HERE / "data" / "demo-inbox.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("replies", [])


def body_of(reply: dict) -> str:
    return reply.get("body") or reply.get("text") or json.dumps(reply, ensure_ascii=False)


def main() -> int:
    model = os.environ.get("MODEL_ID", "muse-spark-1.3")
    dataset = load_dataset()
    correct = 0
    total = 0
    errors = Counter()
    print(f"model={model} · replies={len(dataset)}\n")
    for i, reply in enumerate(dataset):
        lbl = reply.get("label")
        expected = lbl.get("primary_class") if isinstance(lbl, dict) else lbl
        expected = expected or reply.get("expected_class") or reply.get("class")
        if not expected:
            print(f"[{i}] no expected label on reply — skipping")
            continue
        try:
            got = classify(body_of(reply), model=model)["class"]
        except Exception as e:  # noqa: BLE001 — hackathon: log and keep going
            print(f"[{i}] CALL FAILED: {e}")
            errors["call_failed"] += 1
            continue
        ok = got == expected
        total += 1
        correct += ok
        mark = "✓" if ok else "✗"
        print(f"{mark} [{i}] expected={expected:20s} got={got}")
        if not ok:
            errors[f"{expected}→{got}"] += 1

    acc = (100.0 * correct / total) if total else 0.0
    print(f"\naccuracy: {correct}/{total} = {acc:.1f}%")
    if errors:
        print("misses:", dict(errors.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
