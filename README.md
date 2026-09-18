# AquaGuard — SC-06

**Challenge:** SC-06 — Household water use and leak detection  
**Track:** Water and Coast

A beginner-friendly Flask prototype that records household water-flow events,
calculates water consumption, and flags suspicious continuous-use patterns.

## Features

- Household water-use dashboard
- Flow rate + duration input
- Automatic water-consumption calculation
- Explainable possible-leak alerts
- Estimated potential wastage
- Consumption trend chart
- Public-deployment ready with Gunicorn

## Run locally

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Demonstration logic

- Leak risk when flow is at least 0.5 L/min for 60+ minutes.
- High-use leak risk when flow is at least 10 L/min for 20+ minutes.

These are **prototype demonstration rules**, not certified plumbing thresholds.
A production system should use validated sensor data and calibrated rules.
