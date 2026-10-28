"""Lead Finder: rank synthetic prospects against an ideal customer profile (ICP).

Proactive half of Pipeline Copilot: the reply pipeline triages inbound
interest; this module finds outbound targets. Scoring is deterministic and
explainable (every point has a reason string), so the demo can show its work.

Demo data is 100% synthetic (data/prospects.json) — no real companies, no
scraping, no purchased lists. A real search provider can replace
load_prospects() later without changing the scoring or draft flow.

Outreach drafts are DRAFTS: a human approves/edits/rejects them via the
same decision endpoint pattern as reply drafts before anything could send.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.config import VOICE_PROFILE

PROSPECTS_PATH = Path(__file__).resolve().parent.parent / "data" / "prospects.json"

OUTREACH_SYSTEM = """\
You are the drafting assistant for Pipeline Copilot, a reply-intelligence
agent for small B2B sales teams. Draft cold outreach emails in the seller's
voice.

Voice profile:
{profile}

Rules: reference the fit reasons given, in plain language — never invent a
fact about the prospect that is not in the brief. Keep it short (under 120
words). No hype, no jargon, no fake familiarity ("loved your recent post").
Sign exactly "— Alex". Propose a short call, never promise pricing, timelines,
or meetings the seller hasn't confirmed. Human approval is required before
anything sends; your output is always a DRAFT."""


def load_prospects() -> List[dict]:
    with open(PROSPECTS_PATH, encoding="utf-8") as fh:
        return json.load(fh)["prospects"]


def get_prospect(prospect_id: str) -> Optional[dict]:
    for prospect in load_prospects():
        if prospect["id"] == prospect_id:
            return prospect
    return None


def score_prospect(icp: dict, prospect: dict) -> Tuple[int, List[str]]:
    """Score 0-100 with a reason per component. Deterministic: same ICP +
    prospect always gives the same score and reasons."""
    score = 0
    reasons: List[str] = []

    industries = [i.lower() for i in icp.get("industries", [])]
    if prospect["industry"].lower() in industries:
        score += 40
        reasons.append(f"industry match: {prospect['industry']}")
    else:
        reasons.append(f"outside target industries: {prospect['industry']}")

    lo = icp.get("min_employees")
    hi = icp.get("max_employees")
    n = prospect["employees"]
    if (lo is None or n >= lo) and (hi is None or n <= hi):
        score += 25
        reasons.append(f"headcount {n} in target range")
    elif (lo is not None and lo // 2 <= n < lo) or (hi is not None and hi < n <= hi * 2):
        score += 10
        reasons.append(f"headcount {n} near target range")
    else:
        reasons.append(f"headcount {n} outside target range")

    regions = [r.upper() for r in icp.get("regions", [])]
    if prospect["region"].upper() in regions:
        score += 15
        reasons.append(f"region match: {prospect['region']}")
    else:
        reasons.append(f"region outside target: {prospect['region']}")

    keywords = [k.lower() for k in icp.get("keywords", [])]
    signal_text = " ".join(prospect.get("signals", [])).lower()
    hits = [k for k in keywords if k in signal_text]
    score += min(20, 5 * len(hits))
    for hit in hits[:4]:
        reasons.append(f"signal keyword: {hit}")

    # Exclusion trap: a prospect that looks right on firmographics but
    # is flagged as not-a-buyer (e.g. a vendor/partner) never ranks as
    # outreach-ready, no matter how high it scored above.
    if "not a prospect" in signal_text or "not a buyer" in signal_text:
        score = min(score, 25)
        reasons.append("flagged: not a buyer — excluded from outreach")

    return min(100, score), reasons


def rank_prospects(icp: dict, limit: int = 10) -> List[dict]:
    """Rank all prospects by score (ties broken by company name, so output
    is stable across runs)."""
    ranked = []
    for prospect in load_prospects():
        score, reasons = score_prospect(icp, prospect)
        ranked.append({**prospect, "score": score, "reasons": reasons})
    ranked.sort(key=lambda p: (-p["score"], p["company"]))
    return ranked[:limit]


def draft_outreach(prospect: dict, reasons: List[str],
                   model: Optional[str] = None) -> str:
    """One Muse Spark call: cold outreach draft grounded in the prospect
    brief + fit reasons. Mirrors app.draft.draft's client pattern. The
    client import stays lazy so the pure scoring functions never need
    the OpenAI SDK installed."""
    from app.classify import get_client

    client = get_client()
    brief = (
        f"Company: {prospect['company']} ({prospect['domain']})\n"
        f"Industry: {prospect['industry']}, employees: {prospect['employees']}, "
        f"region: {prospect['region']}\n"
        f"Contact: {prospect['contact']}, {prospect['contact_role']}\n"
        f"Known signals: {'; '.join(prospect.get('signals', []))}\n"
        f"Fit reasons: {'; '.join(reasons)}"
    )
    resp = client.chat.completions.create(
        model=model or os.environ.get("MODEL_ID", "muse-spark-1.3"),
        messages=[
            {"role": "system", "content": OUTREACH_SYSTEM.format(profile=VOICE_PROFILE)},
            {"role": "user", "content": f"Prospect brief:\n{brief}\n\nDraft the outreach email."},
        ],
        temperature=0.7,
        extra_body={"reasoning_effort": "low"},
    )
    return resp.choices[0].message.content.strip()