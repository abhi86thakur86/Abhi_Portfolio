"""Check exported controls, SQL edge cases and local Markdown links.

Run after build_portfolio.py: python scripts/verify_portfolio.py
These tests use disposable in-memory databases and never change source CSV files.
"""
from pathlib import Path
from datetime import date, timedelta
import csv
import json
import re
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
PROJECTS=ROOT/'projects'

def quality_db():
    db=sqlite3.connect(':memory:')
    db.execute('''CREATE TABLE raw_employees(raw_id INTEGER PRIMARY KEY,employee_id TEXT,
      department_raw TEXT,fte REAL,manager_id TEXT,start_date TEXT,updated_at TEXT)''')
    with (PROJECTS/'02-sql-data-quality/data/raw_employees.csv').open() as f:
        rows=list(csv.DictReader(f))
    db.executemany('INSERT INTO raw_employees VALUES(?,?,?,?,?,?,?)',
      [[r[k] for k in ['raw_id','employee_id','department_raw','fte','manager_id','start_date','updated_at']] for r in rows])
    db.executescript((PROJECTS/'02-sql-data-quality/analysis.sql').read_text())
    return db

def main():
    db=quality_db()
    assert db.execute("SELECT fte FROM dq_clean WHERE employee_id='E003'").fetchone()==(1.0,)
    # Two failures on one employee must produce two issue flags but one quarantine row.
    db.execute("UPDATE raw_employees SET fte=0, manager_id='' WHERE employee_id='E014'")
    assert db.execute('SELECT COUNT(*) FROM dq_quarantine').fetchone()[0]==7
    assert db.execute('SELECT COUNT(*) FROM dq_issues').fetchone()[0]==8
    assert db.execute('SELECT COUNT(*) FROM dq_clean').fetchone()[0]==7
    db.close()

    db=quality_db()
    # Same timestamp: the greater raw_id must win deterministically.
    db.execute("INSERT INTO raw_employees VALUES(99,'E003','IT',0.5,'E002','2024-01-01','2025-12-20T10:00:00')")
    assert db.execute("SELECT raw_id,fte FROM dq_clean WHERE employee_id='E003'").fetchone()==(99,.5)
    db.close()

    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE departments(department_id TEXT,department TEXT)')
    db.execute("INSERT INTO departments VALUES('D01','Test')")
    db.execute('''CREATE TABLE positions(position_id TEXT,department_id TEXT,status TEXT,
        fte REAL,snapshot_date TEXT,vacancy_open_date TEXT)''')
    snap=date(2025,12,31)
    db.executemany('INSERT INTO positions VALUES(?,?,?,?,?,?)',[
        ('P1','D01','Vacant',1,snap.isoformat(),(snap-timedelta(days=60)).isoformat()),
        ('P2','D01','Vacant',.6,snap.isoformat(),(snap-timedelta(days=61)).isoformat())])
    cur=db.execute((PROJECTS/'01-workforce-reporting/analysis.sql').read_text())
    record=dict(zip([d[0] for d in cur.description],cur.fetchone()))
    assert record['vacancies_over_60_days']==1 and record['vacancy_rate']==1
    assert record['headcount']==0 and record['filled_fte']==0
    db.close()

    # Check baseline financial headline values and monthly controls agree to cents.
    project=PROJECTS/'03-hospitality-profitability'
    expected=json.loads((project/'outputs/expected_metrics.json').read_text())
    with (project/'outputs/monthly_summary.csv').open() as f:months=list(csv.DictReader(f))
    for key in ['revenue','contribution','overhead','operating_surplus']:
        assert abs(sum(float(m[key]) for m in months)-expected[key])<.01,key

    broken=[]
    for md in ROOT.rglob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',md.read_text()):
            if re.match(r'https?://|mailto:|#',link):continue
            if not (md.parent/link.split('#')[0]).exists():broken.append((str(md.relative_to(ROOT)),link))
    assert not broken,broken
    print('PASS: latest-version tie-break, multiple-issue quarantine, 60-day boundary, all-vacant department, financial exports and local links.')

if __name__=='__main__':main()
