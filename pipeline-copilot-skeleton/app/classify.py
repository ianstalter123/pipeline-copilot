"""Classification client: one Muse Spark call per reply, structured output.

Usage from Day 2:
    from app.classify import classify
    result = classify(reply_body)  # -> dict with class, language, confidence
"""
import os

from openai import OpenAI

from app.schemas import Classification, CLASSIFY_SYSTEM


def get_client() -> OpenAI:
    api_key = os.environ.get("MODEL_API_KEY")
    if not api_key:
        raise RuntimeError("MODEL_API_KEY is not set")
    return OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key)


def classify(reply_body: str, model: str | None = None,
             reasoning_effort: str = "minimal") -> dict:
    client = get_client()
    resp = client.beta.chat.completions.parse(
        model=model or os.environ.get("MODEL_ID", "muse-spark-1.3"),
        messages=[
            {"role": "system", "content": CLASSIFY_SYSTEM},
            {"role": "user", "content": reply_body[:2000]},
        ],
        response_format=Classification,
        temperature=0,
        extra_body={"reasoning_effort": reasoning_effort},
    )
    parsed = resp.choices[0].message.parsed
    return {
        "class": parsed.reply_class.value,
        "language": parsed.language,
        "confidence": parsed.confidence,
        "usage": resp.usage.model_dump() if resp.usage else None,
    }
