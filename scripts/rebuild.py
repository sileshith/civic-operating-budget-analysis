"""Regenerate synthetic inputs, SQLite database, SQL exports and findings.

Python 3 standard library only. Does not refresh or alter the Excel workbook.
"""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import argparse
import csv
import datetime as dt
import hashlib
import json
import random
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEPARTMENTS = [('FIN', 'Finance'), ('PW', 'Public Works'), ('PR', 'Parks and Recreation')]
ACCOUNTS = [('ALLOC', 'Assigned operating support', 'Funding'),
            ('FEES', 'Service fees', 'Funding'),
            ('PAY', 'Personnel', 'Expense'),
            ('CONTRACT', 'Contract services', 'Expense'),
            ('MATERIAL', 'Materials', 'Expense')]
ANNUAL_BUDGET = {
    'FIN': {'ALLOC': 950000, 'FEES': 150000, 'PAY': 720000, 'CONTRACT': 180000, 'MATERIAL': 70000},
    'PW': {'ALLOC': 3100000, 'FEES': 650000, 'PAY': 2200000, 'CONTRACT': 1050000, 'MATERIAL': 400000},
    'PR': {'ALLOC': 1800000, 'FEES': 900000, 'PAY': 1700000, 'CONTRACT': 550000, 'MATERIAL': 350000}}
ACTUAL_FACTORS = {
    'FIN': {'ALLOC': .99, 'FEES': 1.03, 'PAY': 1.015, 'CONTRACT': 1.12, 'MATERIAL': .97},
    'PW': {'ALLOC': .99, 'FEES': 1.02, 'PAY': 1.06, 'CONTRACT': 1.025, 'MATERIAL': 1.04},
    'PR': {'ALLOC': .99, 'FEES': .96, 'PAY': 1.025, 'CONTRACT': 1.04, 'MATERIAL': 1.16}}
RATES = {'Base': {'ALLOC': .025, 'FEES': .03, 'PAY': .045, 'CONTRACT': .04, 'MATERIAL': .03},
         'Constrained': {'ALLOC': .005, 'FEES': .01, 'PAY': .055, 'CONTRACT': .06, 'MATERIAL': .05}}

def rounded(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def allocate(total, weights):
    amounts = [rounded(Decimal(total) * Decimal(str(x)) / sum(map(lambda v: Decimal(str(v)), weights))) for x in weights]
    amounts[-1] += total - sum(amounts)
    return amounts

def write_csv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or list(rows[0])
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def generate():
    rng = random.Random(407409)
    records = []
    for fy in [2025, 2026]:
        months = [dt.date(fy-1 if i < 6 else fy, ((6+i) % 12)+1, 1).isoformat() for i in range(12)]
        for did, _ in DEPARTMENTS:
            for aid, _, _ in ACCOUNTS:
                budget = rounded(Decimal(ANNUAL_BUDGET[did][aid]) * 100 * (Decimal('.96') if fy == 2025 else 1))
                factor = Decimal(str(ACTUAL_FACTORS[did][aid])) if fy == 2026 else Decimal('1.005')
                actual = rounded(budget * factor)
                seasonal = [1.0] * 12
                if aid in ['FEES', 'MATERIAL']:
                    seasonal = [1.3, 1.3, 1.1, .9, .85, .8, .8, .85, .95, 1., 1.05, 1.1]
                budgets = allocate(budget, seasonal)
                actuals = allocate(actual, [x * rng.uniform(.96, 1.04) for x in seasonal])
                for month, b, a in zip(months, budgets, actuals):
                    records.append(dict(month_start=month, fiscal_year=fy, department_id=did,
                                        account_id=aid, budget_cents=b, actual_cents=a))
    rates = [dict(scenario=sc, fiscal_year=fy, account_id=aid, rate_ppm=rounded(rate*1000000))
             for sc, mapping in RATES.items() for fy in range(2027, 2032) for aid, rate in mapping.items()]
    return records, rates

def validate(records, rates):
    keys = [(r['month_start'], r['department_id'], r['account_id']) for r in records]
    if len(set(keys)) != len(keys): raise ValueError('Duplicate month/department/account key')
    if len(records) != 360: raise ValueError('Expected 360 complete monthly financial records')
    for r in records:
        date = dt.date.fromisoformat(r['month_start'])
        if date.day != 1 or date.year + (date.month >= 7) != r['fiscal_year']: raise ValueError('Fiscal period mismatch')
        if r['department_id'] not in dict(DEPARTMENTS) or r['account_id'] not in {a[0] for a in ACCOUNTS}: raise ValueError('Unknown dimension key')
        if any(type(r[k]) is not int or r[k] < 0 for k in ['budget_cents', 'actual_cents']): raise ValueError('Amounts require nonnegative integer cents')
    for fy in [2025, 2026]:
        for did, _ in DEPARTMENTS:
            for aid, _, _ in ACCOUNTS:
                if sum(r['fiscal_year']==fy and r['department_id']==did and r['account_id']==aid for r in records) != 12: raise ValueError('Missing fiscal month')
    expected = {(sc, fy, aid) for sc in RATES for fy in range(2027,2032) for aid,_,_ in ACCOUNTS}
    if {(r['scenario'],r['fiscal_year'],r['account_id']) for r in rates} != expected or len(rates)!=50: raise ValueError('Missing/duplicate forecast driver')
    if any(type(r['rate_ppm']) is not int or r['rate_ppm'] < -1000000 for r in rates): raise ValueError('Invalid growth driver')

def build_database(path, records, rates):
    validate(records, rates)
    c = sqlite3.connect(path)
    c.executescript((ROOT/'sql/schema/001_create_schema.sql').read_text())
    c.executemany('INSERT INTO departments VALUES (?,?)', DEPARTMENTS)
    c.executemany('INSERT INTO accounts VALUES (?,?,?)', ACCOUNTS)
    c.executemany('INSERT INTO monthly_financials VALUES (:month_start,:fiscal_year,:department_id,:account_id,:budget_cents,:actual_cents)', records)
    c.executemany('INSERT INTO forecast_rates VALUES (:scenario,:fiscal_year,:account_id,:rate_ppm)', rates)
    c.commit()
    if c.execute('PRAGMA foreign_key_check').fetchall(): raise ValueError('Foreign key check failed')
    return c

def query(c, filename, **params):
    cur = c.execute((ROOT/'sql/queries'/filename).read_text(), params)
    return [dict(zip([x[0] for x in cur.description], row)) for row in cur.fetchall()]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=list(RATES), default='Base')
    args = parser.parse_args()
    (ROOT/'data/raw').mkdir(parents=True, exist_ok=True)
    (ROOT/'data/processed').mkdir(parents=True, exist_ok=True)
    (ROOT/'reports/exports').mkdir(parents=True, exist_ok=True)
    records, rates = generate()
    validate(records, rates)
    write_csv(ROOT/'data/raw/monthly_financials.csv', records)
    names = dict(DEPARTMENTS)
    account_names = {a[0]: (a[1], a[2]) for a in ACCOUNTS}
    write_csv(ROOT/'data/raw/workbook_monthly_inputs.csv', [
        {'Month start': r['month_start'], 'FY ending': r['fiscal_year'],
         'Department': names[r['department_id']], 'Account': account_names[r['account_id']][0],
         'Type': account_names[r['account_id']][1], 'Budget (USD)': r['budget_cents']/100,
         'Actual (USD)': r['actual_cents']/100} for r in records])
    write_csv(ROOT/'data/raw/forecast_rates.csv', rates)
    write_csv(ROOT/'data/raw/departments.csv', [dict(department_id=a,department_name=b) for a,b in DEPARTMENTS])
    write_csv(ROOT/'data/raw/accounts.csv', [dict(account_id=a,account_name=b,flow_type=c) for a,b,c in ACCOUNTS])
    path = ROOT/'data/processed/budget_analysis.sqlite'
    with tempfile.TemporaryDirectory(dir=ROOT/'data/processed') as td:
        temporary = Path(td)/'budget.sqlite'
        c = build_database(temporary, records, rates)
        variance = query(c, 'department_variance.sql', fiscal_year=2026)
        forecast = query(c, 'five_year_forecast.sql', scenario=args.case)
        exceptions = query(c, 'account_exceptions.sql', fiscal_year=2026)
        write_csv(ROOT/'reports/exports/department_variance.csv', variance)
        write_csv(ROOT/'reports/exports/forecast_detail.csv', forecast)
        write_csv(ROOT/'reports/exports/account_exceptions.csv', exceptions)
        annual = []
        for fy in range(2027,2032):
            funding = sum(r['amount_cents'] for r in forecast if r['fiscal_year']==fy and r['flow_type']=='Funding')
            expense = sum(r['amount_cents'] for r in forecast if r['fiscal_year']==fy and r['flow_type']=='Expense')
            annual.append(dict(fiscal_year=fy, funding_cents=funding, expense_cents=expense, gap_cents=funding-expense))
        c.close(); temporary.replace(path)
    payload = dict(records=records, rates=rates, departments=DEPARTMENTS, accounts=ACCOUNTS,
                   variance=variance, forecast=forecast, annual=annual, scenario=args.case)
    (ROOT/'data/processed/model_snapshot.json').write_text(json.dumps(payload, indent=2))
    summary = ['# Budget analysis findings', '', '**Synthetic portfolio simulation — no City of Alameda records.**', '',
               f'SQL export scenario: **{args.case}**. Baseline: full FY 2025-26. Forecast: FY 2026-27 through FY 2030-31.', '',
               '## Expense variance by department', '', '| Department | Budget | Actual | Favorable variance |', '|---|---:|---:|---:|']
    for r in variance: summary.append(f"| {r['department_name']} | ${r['budget_usd']:,.2f} | ${r['actual_usd']:,.2f} | ${r['favorable_variance_usd']:,.2f} |")
    summary += ['', 'Positive variance is under budget; negative is overspend. Differences were deliberately built into the fictional data and are not findings about real departments.', '', '## Five-year outlook', '', '| Fiscal year | Assigned funding + fees | Operating expense | Funding less expense |', '|---|---:|---:|---:|']
    for r in annual: summary.append(f"| FY {r['fiscal_year']-1}-{str(r['fiscal_year'])[-2:]} | ${r['funding_cents']/100:,.2f} | ${r['expense_cents']/100:,.2f} | ${r['gap_cents']/100:,.2f} |")
    proposal = [r for r in annual if r['fiscal_year'] in [2028,2029]]
    summary += ['', '## FY 2027-29 proposal', '',
                f"Two-year modeled operating expense: **${sum(r['expense_cents'] for r in proposal)/100:,.2f}**. Modeled funding gap/surplus: **${sum(r['gap_cents'] for r in proposal)/100:,.2f}**.", '',
                'This is an illustrative spending proposal based on selected growth assumptions, not an adopted budget. Assigned support represents funding allocated to the three-department scope; it is not additional consolidated municipal revenue. Gaps do not imply cash balances or reserves.', '',
                '## Questions for a budget review', '',
                '- Investigate the largest expense variances at account level and determine whether they recur before proposing changes.',
                '- Compare personnel and contract growth assumptions with documented staffing plans, agreements and cost drivers when real data becomes available.',
                '- Assess funding assumptions and service implications before considering reductions. A modeled deficit does not establish a staffing or service recommendation.', '',
                'The Excel workbook is a separate embedded snapshot. Rebuilding SQL exports does not automatically refresh Excel; see README for the refresh boundary.']
    (ROOT/'reports/findings.md').write_text('\n'.join(summary)+'\n')
    manifest = dict(generator_seed=407409, synthetic=True, monthly_records=len(records),
                    fiscal_calendar='July 1–June 30; fiscal year labeled by ending year',
                    export_scenario=args.case, sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data/raw').glob('*.csv'))})
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(records=len(records), forecast_rows=len(forecast), annual=annual, variance=variance),indent=2))

if __name__ == '__main__': main()
