# AquaGuard v2

Features: dashboard, manual reading entry, CSV upload, trend chart, explainable alerts and sample CSV.

Run on Windows:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

CSV columns: `location, recorded_at, ph, turbidity, dissolved_oxygen`

Thresholds are demonstration values only and must not be used to certify drinking-water safety. The final hackathon project must be rebuilt after the sealed problem and supplied dataset are revealed.
