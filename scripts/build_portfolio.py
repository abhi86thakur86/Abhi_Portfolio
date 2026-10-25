"""Rebuild synthetic datasets, run SQLite analyses and verify reconciliations.

Run from any directory: python scripts/build_portfolio.py
Optional chart rendering: python scripts/build_portfolio.py --charts
No employer data, credentials, or network calls are used.
"""
from pathlib import Path
import argparse
import csv
import json
import random
import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / 'projects'
ASOF = date(2025, 12, 31)

def write_csv(path, rows, headers=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=headers or list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')

def load(db, table, rows, schema):
    db.execute(f'CREATE TABLE {table} ({schema})')
    keys = list(rows[0])
    db.executemany(f'INSERT INTO {table} ({",".join(keys)}) VALUES ({",".join("?" for _ in keys)})',
                   [list(r.values()) for r in rows])

def query(db, sql):
    cur = db.execute(sql)
    keys = [d[0] for d in cur.description]
    return [dict(zip(keys, r)) for r in cur.fetchall()]

def workforce():
    p = PROJECTS / '01-workforce-reporting'
    departments = [dict(department_id=f'D{i+1:02}', department=n)
                   for i,n in enumerate(['Operations', 'Finance', 'People', 'Technology'])]
    positions = []
    employee_number = 0
    # Each tuple is approved positions, vacancies. Variation is intentional.
    for dept, (count, vacancies) in zip(departments, [(50,12),(20,3),(15,2),(35,7)]):
        for j in range(count):
            vacant = j >= count-vacancies
            if not vacant:
                employee_number += 1
            fte = [1.0,1.0,1.0,0.8,0.6][j%5]
            age = 20+((j*13+count)%105)
            positions.append(dict(position_id=f'P{len(positions)+1:03}',
                department_id=dept['department_id'],
                role_family=['Service delivery','Analysis','Coordination','Leadership'][j%4],
                status='Vacant' if vacant else 'Filled',
                employee_id='' if vacant else f'EMP{employee_number:03}', fte=fte,
                snapshot_date=ASOF.isoformat(),
                vacancy_open_date=(ASOF-timedelta(days=age)).isoformat() if vacant else ''))
    recruitment = []
    for i,r in enumerate(x for x in positions if x['status']=='Vacant'):
        recruitment.append(dict(requisition_id=f'REQ{i+1:03}', position_id=r['position_id'],
            stage=['Approved','Advertised','Interview','Offer'][i%4]))
    for n,rows in [('departments',departments),('positions',positions),('recruitment',recruitment)]:
        write_csv(p/'data'/f'{n}.csv',rows)
    db=sqlite3.connect(':memory:')
    load(db,'departments',departments,'department_id TEXT PRIMARY KEY, department TEXT')
    load(db,'positions',positions,'''position_id TEXT PRIMARY KEY,department_id TEXT,role_family TEXT,
        status TEXT,employee_id TEXT,fte REAL,snapshot_date TEXT,vacancy_open_date TEXT''')
    summary=query(db,(p/'analysis.sql').read_text())
    write_csv(p/'outputs'/'department_summary.csv',summary)
    metrics=dict(approved_positions=len(positions),headcount=employee_number,
        approved_fte=round(sum(x['fte'] for x in positions),2),
        filled_fte=round(sum(x['fte'] for x in positions if x['status']=='Filled'),2),
        vacant_positions=len(recruitment),
        vacant_fte=round(sum(x['fte'] for x in positions if x['status']=='Vacant'),2),
        vacancy_rate=len(recruitment)/len(positions),
        vacancies_over_60_days=sum(x['vacancies_over_60_days'] for x in summary))
    assert metrics['headcount']==96 and metrics['vacant_positions']==24
    assert len({x['employee_id'] for x in positions if x['employee_id']})==employee_number
    assert sum(x['approved_positions'] for x in summary)==len(positions)
    assert abs(metrics['filled_fte']+metrics['vacant_fte']-metrics['approved_fte'])<1e-8
    assert {x['position_id'] for x in recruitment}=={x['position_id'] for x in positions if x['status']=='Vacant'}
    write_json(p/'outputs'/'expected_metrics.json',metrics)
    p.joinpath('outputs','findings.md').write_text(f'''# Workforce findings

Synthetic organisation. Snapshot: 31 December 2025. This is a single-date position register.

- {metrics['approved_positions']} approved positions; {metrics['headcount']} filled positions and unique employees.
- Filled FTE is {metrics['filled_fte']:.1f}; vacant FTE is {metrics['vacant_fte']:.1f}.
- Position vacancy rate is {metrics['vacancy_rate']:.0%}; this uses positions, not FTE.
- {metrics['vacancies_over_60_days']} vacancies have been open for more than 60 calendar days.
- Operations has 12 vacancies out of 50 positions (24%), compared with Technology's 7 out of 35 (20%).

Suggested action: discuss long-open Operations vacancies with the hiring manager, then check
role criticality and recruitment stage before setting priorities. Age alone is insufficient.
No trend, attrition or time-to-hire conclusion can be drawn from a single snapshot.
''',encoding='utf-8')
    db.close()
    return metrics, summary

def data_quality():
    p=PROJECTS/'02-sql-data-quality'
    raw=[]
    aliases=[' ops ','FIN','hr','IT','Operations','Finance','People','Technology']
    for i in range(1,15):
        raw.append(dict(raw_id=i,employee_id=f'E{i:03}',department_raw=aliases[(i-1)%8],
            fte=[1.0,0.8,0.6][i%3],manager_id='' if i==1 else ('E001' if i==2 else 'E002'),
            start_date=f'2024-{(i%12)+1:02}-15',updated_at='2025-12-20T10:00:00'))
    raw[7]['manager_id']=''
    raw[8]['manager_id']='E999'
    raw[9]['manager_id']='E010'
    raw[10]['fte']=1.4
    raw[11]['department_raw']='Mystery team'
    raw[12]['start_date']='2026-01-05'
    # Older versions are retained in raw and excluded from the reporting snapshot.
    for raw_id, original in [(15,raw[2]),(16,raw[5])]:
        old=original.copy()
        old.update(raw_id=raw_id,updated_at='2025-11-01T10:00:00')
        old['fte']=1.7
        raw.append(old)
    write_csv(p/'data'/'raw_employees.csv',raw)
    db=sqlite3.connect(':memory:')
    load(db,'raw_employees',raw,'''raw_id INTEGER PRIMARY KEY,employee_id TEXT,department_raw TEXT,
        fte REAL,manager_id TEXT,start_date TEXT,updated_at TEXT''')
    db.executescript((p/'analysis.sql').read_text())
    for name,sql in [
        ('clean_employees','SELECT * FROM dq_clean ORDER BY employee_id'),
        ('quarantined_employees','SELECT * FROM dq_quarantine ORDER BY employee_id'),
        ('issue_log','SELECT * FROM dq_issues ORDER BY employee_id,rule_code'),
        ('superseded_records','SELECT * FROM dq_ranked WHERE version_rank>1 ORDER BY employee_id'),
        ('department_summary','SELECT department,COUNT(*) AS headcount,ROUND(SUM(fte),2) AS fte FROM dq_clean GROUP BY department ORDER BY department')]:
        rows=query(db,sql)
        write_csv(p/'outputs'/f'{name}.csv',rows)
    issues=query(db,'SELECT rule_code,COUNT(*) AS affected_records FROM dq_issues GROUP BY rule_code ORDER BY rule_code')
    write_csv(p/'outputs'/'quality_summary.csv',issues)
    counts=dict(raw_rows=len(raw),superseded_rows=2,unique_employees=14,
        accepted_employees=db.execute('SELECT COUNT(*) FROM dq_clean').fetchone()[0],
        quarantined_employees=db.execute('SELECT COUNT(*) FROM dq_quarantine').fetchone()[0],
        issue_flags=db.execute('SELECT COUNT(*) FROM dq_issues').fetchone()[0])
    assert counts['accepted_employees']==8 and counts['quarantined_employees']==6
    assert counts['raw_rows']==counts['superseded_rows']+counts['accepted_employees']+counts['quarantined_employees']
    assert not db.execute('SELECT employee_id FROM dq_clean INTERSECT SELECT employee_id FROM dq_quarantine').fetchall()
    assert db.execute('SELECT COUNT(*) FROM dq_clean WHERE fte<=0 OR fte>1 OR department IS NULL').fetchone()[0]==0
    assert db.execute('''SELECT COUNT(*) FROM dq_clean c LEFT JOIN dq_clean m
      ON c.manager_id=m.employee_id WHERE c.employee_id<>'E001' AND m.employee_id IS NULL''').fetchone()[0]==0
    write_json(p/'outputs'/'expected_metrics.json',counts)
    p.joinpath('outputs','findings.md').write_text('''# Data quality findings

Synthetic test fixture, reporting cutoff 31 December 2025.

16 raw records represent 14 employees. Two older versions are retained separately.
The latest-record checks accept 8 employees and quarantine 6. Each quarantined
employee has one issue in this fixture: missing manager, unknown manager,
self-reporting, invalid FTE, unmapped department, or start date after cutoff.

Reconciliation: 16 raw = 2 superseded + 8 accepted + 6 quarantined.
An issue count can exceed affected employees when a row breaks several rules.

Action: send the six exceptions to the source owner for confirmation, then rerun.
Do not guess a manager or silently clamp FTE to 1. The accepted dataset is incomplete
until exceptions are resolved; lower headcount after filtering is not a business reduction.
The fixture does not implement full organisation-cycle detection or production schema validation.
''',encoding='utf-8')
    db.close()
    return counts,issues

def hospitality():
    p=PROJECTS/'03-hospitality-profitability'
    rng=random.Random(42)
    rows=[]
    season=[1.15,1.1,1.02,.98,.9,.82,.8,.85,.95,1.03,1.1,1.2]
    for month in range(1,13):
        for channel,volume,fee in [('Dine-in',1.0,0.015),('Pickup',.65,0.015),('Delivery',.8,.28)]:
            for category,base,price,cost in [('Mains',420,24,8),('Sides',260,9,2.5),('Drinks',310,6,1.5),('Desserts',150,11,3.5)]:
                units=round(base*volume*season[month-1]*rng.uniform(.93,1.07))
                rows.append(dict(month=f'2025-{month:02}-01',channel=channel,category=category,
                    units=units,unit_price=price,unit_food_cost=cost,fee_rate=fee))
    overheads=[dict(month=f'2025-{m:02}-01',overhead=31000 if m in [11,12] else 29500) for m in range(1,13)]
    write_csv(p/'data'/'sales.csv',rows)
    write_csv(p/'data'/'overheads.csv',overheads)
    # JSON contains identical typed inputs for the optional Excel authoring workflow.
    write_json(p/'data'/'workbook_inputs.json',dict(sales=rows,overheads=overheads))
    db=sqlite3.connect(':memory:')
    load(db,'sales',rows,'month TEXT,channel TEXT,category TEXT,units INTEGER,unit_price REAL,unit_food_cost REAL,fee_rate REAL')
    load(db,'overheads',overheads,'month TEXT PRIMARY KEY,overhead REAL')
    monthly=query(db,(p/'analysis.sql').read_text())
    channels=query(db,'''SELECT channel,ROUND(SUM(units*unit_price),2) AS revenue,
      ROUND(SUM(units*unit_price-units*unit_food_cost-ROUND(units*unit_price*ROUND(fee_rate*10000,0)/100,0)/100),2) AS contribution,
      ROUND(SUM(units*unit_price-units*unit_food_cost-ROUND(units*unit_price*ROUND(fee_rate*10000,0)/100,0)/100)/SUM(units*unit_price),4) AS contribution_margin
      FROM sales GROUP BY channel ORDER BY contribution DESC''')
    write_csv(p/'outputs'/'monthly_summary.csv',monthly)
    write_csv(p/'outputs'/'channel_summary.csv',channels)
    totals={k:round(sum(r[k] for r in monthly),2) for k in ['revenue','food_cost','channel_fees','gross_profit','contribution','overhead','operating_surplus']}
    totals['contribution_margin']=totals['contribution']/totals['revenue']
    totals['sales_rows']=len(rows)
    assert len(rows)==144 and len(monthly)==12
    assert abs(totals['revenue']-sum(r['units']*r['unit_price'] for r in rows))<.01
    independent_fees=sum((Decimal(r['units'])*Decimal(r['unit_price'])*Decimal(str(r['fee_rate']))).quantize(
        Decimal('.01'),rounding=ROUND_HALF_UP) for r in rows)
    assert abs(totals['channel_fees']-float(independent_fees))<.001
    assert abs(totals['contribution']-sum(r['contribution'] for r in channels))<.02
    assert abs(totals['contribution']-totals['overhead']-totals['operating_surplus'])<.01
    write_json(p/'outputs'/'expected_metrics.json',totals)
    low=min(monthly,key=lambda x:x['operating_surplus'])
    high=max(monthly,key=lambda x:x['operating_surplus'])
    margins={x['channel']:x['contribution_margin'] for x in channels}
    p.joinpath('outputs','findings.md').write_text(f'''# Hospitality findings

Synthetic calendar year 2025. Amounts NZD, GST exclusive. No actual business performance is represented.

- Revenue: ${totals['revenue']:,.0f}. Food gross profit: ${totals['gross_profit']:,.0f}.
- Contribution after food cost and channel fees: ${totals['contribution']:,.0f} ({totals['contribution_margin']:.1%} of revenue).
- Operating surplus after assumed overhead: ${totals['operating_surplus']:,.0f}.
- Lowest operating-surplus month: {low['month'][:7]} (${low['operating_surplus']:,.0f}).
- Highest operating-surplus month: {high['month'][:7]} (${high['operating_surplus']:,.0f}).
- Delivery contribution margin is {margins['Delivery']:.1%}, compared with {margins['Pickup']:.1%} for pickup.

Suggested action: assess delivery pricing and customer retention before spending more to grow
delivery sales. Review winter staffing and opening hours, using demand and service requirements.
These are hypotheses for the fictional business, not measured improvements.

Overhead is an assumed aggregate of staff wages, rent, utilities and other operating expenses.
Owner remuneration, interest, depreciation, income tax, capex and working capital are excluded.
Operating surplus is not cash flow, net profit, or owner take-home pay. Fee rates and seasonality
are illustrative assumptions, not current supplier quotes or Auckland market benchmarks.
''',encoding='utf-8')
    db.close()
    return totals,monthly,channels

def render_charts(workforce_result, dq_result, hospitality_result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
        'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold',
        'axes.labelcolor':'#334155','text.color':'#0f172a','figure.facecolor':'#f8fafc',
        'axes.facecolor':'#f8fafc','svg.fonttype':'none'})
    navy,teal,amber='#1e3a5f','#0f766e','#d97706'
    m,rows=workforce_result
    fig=plt.figure(figsize=(13,7.2),layout='constrained')
    gs=fig.add_gridspec(2,2,height_ratios=[.65,2])
    top=fig.add_subplot(gs[0,:]);top.axis('off')
    top.text(0, .9,'WORKFORCE CAPACITY',fontsize=21,weight='bold')
    top.text(0,.58,'Synthetic organisation | Snapshot 31 December 2025 | SQL-verified preview',color='#64748b')
    for x,label,value in zip([0,.25,.5,.75],['Filled headcount','Filled FTE','Vacancy rate','Vacancies >60 days'],
                            [m['headcount'],m['filled_fte'],f"{m['vacancy_rate']:.0%}",m['vacancies_over_60_days']]):
        top.text(x,.1,str(value),fontsize=23,weight='bold',color=navy)
        top.text(x,-.13,label,fontsize=10,color='#64748b')
    ax=fig.add_subplot(gs[1,0]); names=[r['department'] for r in rows]
    ax.barh(names,[r['headcount'] for r in rows],color=navy,label='Filled')
    ax.barh(names,[r['vacant_positions'] for r in rows],left=[r['headcount'] for r in rows],color=amber,label='Vacant')
    ax.invert_yaxis();ax.set_title('Approved positions by department',loc='left',pad=16)
    ax.set_xlabel('Positions');ax.legend(frameon=False,loc='lower right')
    ax=fig.add_subplot(gs[1,1]); ax.barh(names,[100*r['vacancy_rate'] for r in rows],color=teal)
    ax.invert_yaxis();ax.set_xlim(0,30);ax.set_xlabel('Vacant positions / approved positions (%)')
    ax.set_title('Position vacancy rate',loc='left',pad=16)
    for i,r in enumerate(rows):ax.text(100*r['vacancy_rate']+.4,i,f"{r['vacancy_rate']:.1%}",va='center')
    fig.savefig(PROJECTS/'01-workforce-reporting'/'outputs'/'dashboard.png',dpi=150);plt.close(fig)
    counts,issues=dq_result
    fig,axs=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
    fig.suptitle('SQL data quality investigation\nSynthetic fixture | Latest records assessed at 31 December 2025',fontsize=17,weight='bold')
    axs[0].bar(['Accepted','Quarantined','Superseded'],[8,6,2],color=[teal,amber,'#94a3b8'])
    axs[0].set_ylabel('Records');axs[0].set_title('16 raw records reconciled',loc='left')
    labels=[x['rule_code'].replace('_',' ').title() for x in issues]
    axs[1].barh(labels,[x['affected_records'] for x in issues],color=navy)
    axs[1].set_xlabel('Issue flags on latest records');axs[1].set_xlim(0,2)
    axs[1].set_xticks([0,1,2]);axs[1].set_title('Exceptions for source-owner review',loc='left')
    fig.savefig(PROJECTS/'02-sql-data-quality'/'outputs'/'quality.png',dpi=150);plt.close(fig)
    totals,monthly,channels=hospitality_result
    fig,axs=plt.subplots(1,2,figsize=(13,5.5),layout='constrained')
    fig.suptitle('Hospitality profitability\nSynthetic CY2025 | NZD, GST exclusive',fontsize=18,weight='bold')
    months=[date.fromisoformat(x['month']).strftime('%b') for x in monthly]
    axs[0].plot(months,[r['contribution'] for r in monthly],color=teal,marker='o',label='Contribution')
    axs[0].plot(months,[r['overhead'] for r in monthly],color=amber,linestyle='--',label='Assumed overhead')
    axs[0].set_ylim(bottom=0);axs[0].yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'${v/1000:,.0f}k'))
    axs[0].set_title('Contribution versus overhead',loc='left');axs[0].legend(frameon=False)
    axs[1].barh([r['channel'] for r in channels],[100*r['contribution_margin'] for r in channels],color=navy)
    axs[1].set_xlim(0,80);axs[1].set_xlabel('Contribution / revenue (%)')
    axs[1].set_title('Delivery fees reduce contribution margin',loc='left')
    fig.savefig(PROJECTS/'03-hospitality-profitability'/'outputs'/'profitability.png',dpi=150);plt.close(fig)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--charts',action='store_true')
    args=parser.parse_args()
    wf=workforce();dq=data_quality();sales=hospitality()
    if args.charts:render_charts(wf,dq,sales)
    print(json.dumps({'workforce':wf[0],'data_quality':dq[0],'hospitality':sales[0]},indent=2))
    print('PASS: SQL outputs, unique keys, population reconciliation, manager references and financial totals.')

if __name__=='__main__':main()
