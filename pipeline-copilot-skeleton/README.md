# Pipeline Copilot — repo skeleton (staged Oct 22, before kickoff)

Pre-kickoff groundwork for the Meta Global AI Developer Hackathon (Oct 26 – Nov 4).
This is the layout from the build spec; move these files into your fresh
`pipeline-copilot` GitHub repo on Day 1. Dataset symlink goes in `data/`.

```
pipeline-copilot/
├── app/
│   ├── __init__.py
│   ├── config.py      # env, model id, voice profile loader
│   ├── ingest.py      # Gmail → normalize → SQLite (or demo inbox file)
│   ├── store.py       # SQLite schema + helpers
│   ├── classify.py    # Muse Spark structured classification (see scripts/muse_spark_hello.py)
│   ├── extract.py     # budget / timeline / pain / decision-maker / next step / language
│   ├── draft.py       # voice-matched follow-up drafts
│   ├── server.py      # FastAPI + dashboard (approve / edit / reject)
│   └── eval.py        # run the 30-reply labeled set, report accuracy
├── scripts/
│   └── muse_spark_hello.py   # 1-call API smoke test on a demo reply
├── data/
│   └── demo-inbox.json       # symlink to pipeline-copilot-demo-dataset.json
├── .github/workflows/ingest.yml   # scheduled ingest cron (port your triage workflow)
├── requirements.txt
├── .env.example
└── .gitignore
```

Classes: `interested` · `meeting-ready` · `objection-price` · `objection-timing` ·
`objection-incumbent` · `not-now` · `wrong-person` · `out-of-office` ·
`unsubscribe` · `other`
