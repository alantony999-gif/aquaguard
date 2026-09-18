import csv, io, sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
app = Flask(__name__)
app.secret_key = 'aquaguard-demo-key'
DB = 'aquaguard.db'

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def evaluate(ph, turbidity, oxygen):
    alerts=[]
    # Demonstration thresholds only; not drinking-water certification standards.
    if ph < 6.5 or ph > 8.5: alerts.append('pH outside demonstration range')
    if turbidity > 5: alerts.append('High turbidity')
    if oxygen < 5: alerts.append('Low dissolved oxygen')
    return ('CRITICAL' if alerts else 'SAFE'), ('; '.join(alerts) or 'No alerts')

def init_db():
    c=db(); c.execute('''CREATE TABLE IF NOT EXISTS readings(
        id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, recorded_at TEXT,
        ph REAL, turbidity REAL, dissolved_oxygen REAL, status TEXT, alerts TEXT)''')
    if c.execute('SELECT COUNT(*) FROM readings').fetchone()[0]==0:
        rows=[('Periyar River - Station 01','2026-09-15 09:00',7.2,3.1,7.0),('Vembanad Lake - Station 02','2026-09-15 10:00',8.9,7.4,4.2),('Coastal Area - Station 03','2026-09-15 11:00',7.5,2.8,6.1)]
        for location,dt,ph,turb,oxy in rows:
            status,alerts=evaluate(ph,turb,oxy)
            c.execute('INSERT INTO readings(location,recorded_at,ph,turbidity,dissolved_oxygen,status,alerts) VALUES(?,?,?,?,?,?,?)',(location,dt,ph,turb,oxy,status,alerts))
    c.commit(); c.close()

def save(location,dt,ph,turb,oxy,c):
    status,alerts=evaluate(ph,turb,oxy)
    c.execute('INSERT INTO readings(location,recorded_at,ph,turbidity,dissolved_oxygen,status,alerts) VALUES(?,?,?,?,?,?,?)',(location,dt,ph,turb,oxy,status,alerts))

@app.route('/')
def index():
    c=db(); readings=c.execute('SELECT * FROM readings ORDER BY recorded_at DESC,id DESC').fetchall(); chart=c.execute('SELECT location,recorded_at,ph,turbidity,dissolved_oxygen FROM readings ORDER BY recorded_at,id').fetchall(); c.close()
    return render_template('index.html',readings=readings,total=len(readings),critical=sum(r['status']=='CRITICAL' for r in readings),safe=sum(r['status']=='SAFE' for r in readings),chart_data=[dict(x) for x in chart])

@app.route('/add',methods=['GET','POST'])
def add():
    if request.method=='POST':
        try:
            location=request.form['location'].strip(); dt=request.form['recorded_at'].strip(); ph=float(request.form['ph']); turb=float(request.form['turbidity']); oxy=float(request.form['dissolved_oxygen'])
            if not location or not dt or min(ph,turb,oxy)<0: raise ValueError('Enter valid non-negative values.')
            c=db(); save(location,dt,ph,turb,oxy,c); c.commit(); c.close(); flash('Reading added successfully.','success'); return redirect(url_for('index'))
        except (KeyError,ValueError) as e: flash(f'Input error: {e}','error')
    return render_template('add.html')

@app.route('/upload',methods=['GET','POST'])
def upload():
    if request.method=='POST':
        f=request.files.get('csv_file')
        try:
            if not f or not f.filename: raise ValueError('Choose a CSV file.')
            reader=csv.DictReader(io.StringIO(f.read().decode('utf-8-sig')))
            required={'location','recorded_at','ph','turbidity','dissolved_oxygen'}
            if not reader.fieldnames or not required.issubset(reader.fieldnames): raise ValueError('Required columns: location, recorded_at, ph, turbidity, dissolved_oxygen')
            c=db(); n=0
            for row in reader:
                ph=float(row['ph']); turb=float(row['turbidity']); oxy=float(row['dissolved_oxygen'])
                if min(ph,turb,oxy)<0: raise ValueError('Negative value found.')
                save(row['location'].strip(),row['recorded_at'].strip(),ph,turb,oxy,c); n+=1
            c.commit(); c.close(); flash(f'{n} reading(s) imported.','success'); return redirect(url_for('index'))
        except (UnicodeDecodeError,ValueError,KeyError) as e: flash(f'Upload failed: {e}','error')
    return render_template('upload.html')

@app.route('/alerts')
def alerts():
    c=db(); rows=c.execute("SELECT * FROM readings WHERE status='CRITICAL' ORDER BY recorded_at DESC,id DESC").fetchall(); c.close(); return render_template('alerts.html',readings=rows)

@app.route('/sample.csv')
def sample():
    text='location,recorded_at,ph,turbidity,dissolved_oxygen\nPeriyar River - Station 01,2026-09-16 09:00,7.1,4.0,6.8\nVembanad Lake - Station 02,2026-09-16 10:00,8.7,8.1,4.4\n'
    return app.response_class(text,mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=sample_water_data.csv'})

if __name__=='__main__': init_db(); app.run(debug=True)
