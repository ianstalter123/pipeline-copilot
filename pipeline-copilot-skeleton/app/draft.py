"""Drafting: voice-matched follow-up drafts. Human approves before anything sends."""
import os
from typing import Optional

from openai import OpenAI

from app.classify import get_client
from app.config import VOICE_PROFILE, VOICE_EXAMPLE_1, VOICE_EXAMPLE_2

DRAFT_SYSTEM = """\
You are the drafting assistant for Pipeline Copilot, a reply-intelligence
agent for small B2B sales teams. Draft follow-up emails in the seller's voice.

Voice profile:
{profile}

Two examples of the voice:
---
{ex1}
---
{ex2}
---
Rules: match the reply's language (EN/ES/ZH). Keep it short. No hype, no
jargon. Sign exactly "— Alex". Never promise pricing, timelines, or meetings
the seller hasn't confirmed — propose, don't commit. Human approval is
required before anything sends; your output is always a DRAFT."""


def draft(reply_body: str, reply_class: str, language: str,
          model: Optional[str] = None) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model=model or os.environ.get("MODEL_ID", "muse-spark-1.3"),
        messages=[
            {"role": "system", "content": DRAFT_SYSTEM.format(
                profile=VOICE_PROFILE, ex1=VOICE_EXAMPLE_1, ex2=VOICE_EXAMPLE_2)},
            {"role": "user", "content": (
                f"Classification: {reply_class}\nLanguage: {language}\n\n"
                f"Reply to answer:\n{reply_body[:2000]}\n\nDraft the follow-up email.")},
        ],
        temperature=0.7,
        extra_body={"reasoning_effort": "low"},
    )
    return resp.choices[0].message.content.strip()
