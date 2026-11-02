# Pipeline Copilot

Meta Global AI Developer Hackathon, Oct 26 – Nov 4, 2026. Indie track, solo build.
Submission deadline: Nov 4, 9:00 PM ET (6:00 PM PT).

## Impact (30%)

Inbound sales replies arrive in three languages, at volume, and the first hours
decide whether a deal moves. Pipeline Copilot gives every reply a fast, correct
next step: it triages Gmail sales replies into a funnel, classifies each one,
extracts budget / timeline / pain point / decision-maker / next step, and drafts
a voice-matched follow-up — in the reply's language, so no lead waits for a
translator. Nothing sends without a human approve / edit / reject decision.
Built for solo sellers and small teams who can't afford a RevOps hire.

Demo vertical: Northwind Robotics (fictional warehouse-automation seller,
sender persona Alex Rivera). Demo set: 30 hand-labeled replies — 18 English,
6 Spanish, 6 Chinese — across all 10 reply classes, including 3 edge cases.
100% synthetic; no real company data.

## Use of Meta AI Tooling (25%)

Muse Spark (muse-spark-1.3) does three jobs in sequence: (1) classify each
reply into one of 10 classes plus language and confidence, (2) extract budget,
timeline, pain point, decision-maker, and next step, (3) draft a short
follow-up in the seller's voice, matching the reply's language. Structured
output throughout, so classifications and extractions come back as reliable
data, not prose to parse.

## Eval — proven, plus one table still open

Proven (Oct 27 runs):
- 30-reply batch: **26/30 = 86.7% accuracy, 0 call errors**; all 30 extracted
  and drafted. Batch misses: R01 (meeting-ready → interested),
  R17 (objection-timing → not-now), R27 (objection-timing → not-now),
  R29 (other → interested).
- Approval gate proven on both the workspace server and a local Mac run
  (POST /api/drafts/{id}/decision: approved / edited / rejected).
- Lead Finder (added Oct 28): deterministic, explainable prospect scoring
  (industry +40, headcount in range +25, region +15, signal keywords +5
  each capped at +20; "not a buyer" prospects capped at 25 and excluded).
  Default ICP: warehouse automation / logistics / 3PL, 50–500 staff, US/CA.
  Top prospect: Cascade Fulfillment Co, 95.

Open-weights eval — to be completed before submission (runs on partner
credits via Baseten / Fireworks):

| Model | Accuracy (30 replies) | Avg latency |
|---|---|---|
| Muse Spark 1.3 | 26/30 = 86.7% | TBD |
| Open-weights model via Baseten / Fireworks | TBD | TBD |

## Demo (25%)

- Funnel dashboard: replies in, classification and extraction visible,
  approve/edit/reject on every draft, hot classes (interested, meeting-ready)
  flagged for Slack alerts.
- Walkthrough hits the three edge cases: the out-of-office reply with a
  delegate (Jordan Ellis), the incumbent objection with a referral (Symbotic,
  Rachel Nguyen), and the polite Chinese not-now.
- Demo video: recording Nov 3 — link TBD.

## Technical Depth & Execution (20%)

FastAPI + SQLite: ingest → classify → extract → draft → dashboard approval →
Slack alerts, wired end to end. Eval harness runs all 30 labeled replies and
reports accuracy. Graceful failure: if an API call fails, the dashboard says so
plainly instead of silently dropping a reply.

Code lives in the `pipeline-copilot-skeleton/` directory of this repo.
