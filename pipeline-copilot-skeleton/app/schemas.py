"""Shared Pydantic schemas for Pipeline Copilot."""
from enum import Enum

from pydantic import BaseModel


class ReplyClass(str, Enum):
    INTERESTED = "interested"
    MEETING_READY = "meeting-ready"
    OBJECTION_PRICE = "objection-price"
    OBJECTION_TIMING = "objection-timing"
    OBJECTION_INCUMBENT = "objection-incumbent"
    NOT_NOW = "not-now"
    WRONG_PERSON = "wrong-person"
    OUT_OF_OFFICE = "out-of-office"
    UNSUBSCRIBE = "unsubscribe"
    OTHER = "other"


class Classification(BaseModel):
    reply_class: ReplyClass
    language: str            # en | es | zh
    confidence: float        # 0..1


class Extraction(BaseModel):
    budget_signal: str       # e.g. "mentioned $X budget", "no signal"
    timeline: str            # e.g. "this quarter", "unknown"
    pain_point: str          # what problem they mention, or "none stated"
    decision_maker: str      # "yes" | "no" | "unknown"
    next_step: str           # what the reply asks for next
    language: str            # en | es | zh


CLASSIFY_SYSTEM = (
    "You classify B2B sales-email replies for a reply-intelligence agent. "
    "Return exactly one class from the enum, the reply's language (en/es/zh), "
    "and a confidence 0..1. Classify the reply's intent, not its politeness: "
    "a polite 'not this quarter' is not-now, a delegate/forward note is "
    "wrong-person even when polite."
)

EXTRACT_SYSTEM = (
    "Extract structured sales-intelligence fields from a reply email. "
    "If a field is absent, write 'none stated' or 'unknown' — never invent."
)
