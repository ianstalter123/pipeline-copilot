"""Field extraction: budget / timeline / pain / decision-maker / next step."""
import os

from openai import OpenAI

from app.classify import get_client
from app.schemas import Extraction, EXTRACT_SYSTEM


def extract(reply_body: str, model: str | None = None) -> dict:
    client = get_client()
    resp = client.beta.chat.completions.parse(
        model=model or os.environ.get("MODEL_ID", "muse-spark-1.3"),
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": reply_body[:2000]},
        ],
        response_format=Extraction,
        temperature=0,
        extra_body={"reasoning_effort": "minimal"},
    )
    return resp.choices[0].message.parsed.model_dump()
