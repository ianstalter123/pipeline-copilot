"""Central config: env, model ids, hot classes, voice profile."""
import os

MODEL_ID = os.environ.get("MODEL_ID", "muse-spark-1.3")
# Cheap bulk evals: same model, ~12x cheaper input. OK because demo data is 100% synthetic.
EVAL_MODEL_ID = os.environ.get("EVAL_MODEL_ID", "muse-spark-1.3-contributor")

HOT_CLASSES = {"interested", "meeting-ready"}

# Default ideal customer profile for Lead Finder (Northwind Robotics).
# Demo ICP: warehouse-adjacent buyers, 50-500 employees, US/CA.
DEFAULT_ICP = {
    "industries": ["warehouse automation", "logistics", "third-party logistics"],
    "min_employees": 50,
    "max_employees": 500,
    "regions": ["US", "CA"],
    "keywords": ["automation", "DC", "fulfillment", "conveyor",
                 "labor shortage", "second site", "expansion"],
}

VOICE_PROFILE = """\
Alex Rivera, sales rep at Northwind Robotics (warehouse automation software).
Writes short, plain-spoken emails. No hype, no jargon. Signs "— Alex".
"""

# Example 1
VOICE_EXAMPLE_1 = """\
Subject: Re: conveyor sensors

Hi Marcus — quick answer: yes, the retrofit works with your existing
crown equipment, no forklift downtime on install day.

If you want, I can grab 20 minutes Thursday and show you the timeline
for a site like yours.

— Alex
"""

# Example 2
VOICE_EXAMPLE_2 = """\
Subject: Re: pricing

Totally fair question. The ROI usually lands on labor savings in the
first two quarters — happy to walk the math on a call if that's useful.

Would Tuesday or Wednesday morning work?

— Alex
"""