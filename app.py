import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "aquaguard-sc06-demo"

DB_NAME = "aquaguard_sc06.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def analyze_usage(flow_rate, duration):
    """
    Demonstration leak-detection logic for the prototype.
    It is not a certified plumbing diagnostic system.
    """
    consumption = round(flow_rate * duration, 2)
    reasons = []

    # Possible continuous leak: moderate flow continuing for a long time.
    if flow_rate >= 0.5 and duration >= 60:
        reasons.append("Continuous flow for 60+ minutes")

    # Possible high-use event: very high flow for an extended period.
    if flow_rate >= 10 and duration >= 20:
        reasons.append("High flow sustained for 20+ minutes")

    status = "LEAK RISK" if reasons else "NORMAL"

    # Demonstration estimate: potential avoidable water during a flagged event.
    estimated_wastage = round(consumption * 0.70, 2) if reasons else 0.0

    return consumption, status, reasons, estimated_wastage


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            flow_rate REAL NOT NULL,
            duration REAL NOT NULL,
            consumption REAL NOT NULL,
            status TEXT NOT NULL,
            reason TEXT NOT NULL,
            estimated_wastage REAL NOT NULL
        )
    """)

    count = conn.execute("SELECT COUNT(*) FROM usage_readings").fetchone()[0]
    if count == 0:
        sample_rows = [
            ("House A", "2026-09-18 07:30", 6.0, 8),
            ("House A", "2026-09-18 10:15", 0.8, 95),
            ("House B", "2026-09-18 12:00", 12.0, 25),
            ("House C", "2026-09-18 18:20", 5.0, 10),
        ]

        for household, recorded_at, flow_rate, duration in sample_rows:
            consumption, status, reasons, wastage = analyze_usage(flow_rate, duration)
            conn.execute("""
                INSERT INTO usage_readings
                (household, recorded_at, flow_rate, duration, consumption,
                 status, reason, estimated_wastage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                household, recorded_at, flow_rate, duration, consumption,
                status, "; ".join(reasons) if reasons else "No abnormal pattern",
                wastage
            ))

    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    readings = conn.execute("""
        SELECT * FROM usage_readings
        ORDER BY recorded_at DESC, id DESC
    """).fetchall()

    total_consumption = round(sum(row["consumption"] for row in readings), 2)
    leak_events = sum(1 for row in readings if row["status"] == "LEAK RISK")
    estimated_wastage = round(sum(row["estimated_wastage"] for row in readings), 2)

    chart_rows = conn.execute("""
        SELECT household, recorded_at, consumption, flow_rate, status
        FROM usage_readings
        ORDER BY recorded_at ASC, id ASC
    """).fetchall()
    conn.close()

    return render_template(
        "index.html",
        readings=readings,
        total_consumption=total_consumption,
        leak_events=leak_events,
        estimated_wastage=estimated_wastage,
        chart_data=[dict(row) for row in chart_rows]
    )


@app.route("/add", methods=["GET", "POST"])
def add_reading():
    if request.method == "POST":
        try:
            household = request.form["household"].strip()
            recorded_at = request.form["recorded_at"].strip()
            flow_rate = float(request.form["flow_rate"])
            duration = float(request.form["duration"])

            if not household or not recorded_at:
                raise ValueError("Household and date/time are required.")
            if flow_rate < 0 or duration <= 0:
                raise ValueError("Flow rate must be non-negative and duration must be above zero.")

            consumption, status, reasons, wastage = analyze_usage(flow_rate, duration)

            conn = get_db()
            conn.execute("""
                INSERT INTO usage_readings
                (household, recorded_at, flow_rate, duration, consumption,
                 status, reason, estimated_wastage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                household, recorded_at, flow_rate, duration, consumption,
                status, "; ".join(reasons) if reasons else "No abnormal pattern",
                wastage
            ))
            conn.commit()
            conn.close()

            if status == "LEAK RISK":
                flash("Reading saved. AquaGuard detected a possible leak pattern.", "warning")
            else:
                flash("Reading saved successfully.", "success")

            return redirect(url_for("index"))

        except (KeyError, ValueError) as error:
            flash(f"Please check your input: {error}", "error")

    return render_template("add_reading.html")


@app.route("/alerts")
def alerts():
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM usage_readings
        WHERE status = 'LEAK RISK'
        ORDER BY recorded_at DESC, id DESC
    """).fetchall()
    conn.close()
    return render_template("alerts.html", readings=rows)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
