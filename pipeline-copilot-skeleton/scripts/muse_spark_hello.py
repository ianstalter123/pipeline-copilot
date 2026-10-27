"""Day-0 smoke test: one structured Muse Spark call against a real demo reply.

Usage:
    export MODEL_API_KEY=LLM_...        # from https://dev.meta.ai/api-keys
    python scripts/muse_spark_hello.py

Runs ONE classification (one call, a few cents) on the first demo reply and
prints the parsed result. If this works, the API path is green for the build.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI

from app.schemas import Classification, CLASSIFY_SYSTEM


def load_first_demo_reply() -> str:
    here = Path(__file__).resolve().parent.parent
    dataset_path = here / "data" / "demo-inbox.json"
    if not dataset_path.exists():
        # fallback: goal workspace copy
        dataset_path = Path.home() / (
            "workspace/goals/meta-ai-developer-hackathon-pipeline-copilot-build"
            "/files/pipeline-copilot-demo-dataset.json"
        )
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    replies = data if isinstance(data, list) else data.get("replies", [])
    first = replies[0]
    body = first.get("body") or first.get("text") or json.dumps(first, ensure_ascii=False)
    return body[:2000]


def main() -> int:
    api_key = os.environ.get("MODEL_API_KEY")
    if not api_key:
        print("MODEL_API_KEY is not set. Get a key at https://dev.meta.ai/api-keys "
              "and run: export MODEL_API_KEY=LLM_...", file=sys.stderr)
        return 2

    model = os.environ.get("MODEL_ID", "muse-spark-1.3")
    client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key)

    reply = load_first_demo_reply()
    print(f"model={model}\nreply preview: {reply[:140]}...\n")

    # reasoning_effort="minimal" keeps single-reply classification fast/cheap;
    # raise it only for hard edge cases.
    resp = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": CLASSIFY_SYSTEM},
            {"role": "user", "content": reply},
        ],
        response_format=Classification,
        temperature=0,
        extra_body={"reasoning_effort": "minimal"},
    )
    parsed = resp.choices[0].message.parsed
    print("parsed:", parsed.model_dump_json(indent=2))
    print("usage:", resp.usage.model_dump() if resp.usage else "n/a")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
