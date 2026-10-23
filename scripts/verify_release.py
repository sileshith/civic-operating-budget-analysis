"""Check local documentation links and reconcile saved Excel forecasts with SQL.

Standard library only; reads the workbook without changing it.
"""
from pathlib import Path
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def main():
    broken=[]
    for path in ROOT.rglob('*.md'):
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text()):
            link=link.split('#')[0]
            if not link or '://' in link or link.startswith('mailto:'):continue
            if not (path.parent/link).exists():broken.append((str(path.relative_to(ROOT)),link))
    if broken:raise AssertionError(f'Broken local links: {broken}')
    z=zipfile.ZipFile(ROOT/'excel/Budget_Analysis_Portfolio.xlsx')
    rels={x.get('Id'):x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheets={};formulas=0;errors=[]
    for s in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets',NS):
        target=rels[s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')]
        target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        sheets[s.get('name')]=ET.fromstring(z.read(target))
    for name,sh in sheets.items():
        for cell in sh.findall('.//m:c',NS):
            formulas+=cell.find('m:f',NS) is not None
            if cell.get('t')=='e':errors.append((name,cell.get('r')))
    if errors:raise AssertionError(f'Cached Excel formula errors: {errors}')
    values={c.get('r'):float(c.find('m:v',NS).text) for c in sheets['Department plan'].findall('.//m:c',NS)
            if c.get('t') not in ['s','str','inlineStr'] and c.find('m:v',NS) is not None}
    db=sqlite3.connect('file:'+(ROOT/'data/processed/budget_analysis.sqlite').as_posix()+'?mode=ro',uri=True)
    rows=db.execute((ROOT/'sql/queries/five_year_forecast.sql').read_text(),{'scenario':'Base'}).fetchall()
    departments=[r[0] for r in db.execute("SELECT department_name FROM departments ORDER BY CASE department_id WHEN 'FIN' THEN 1 WHEN 'PW' THEN 2 ELSE 3 END")]
    accounts=['ALLOC','FEES','PAY','CONTRACT','MATERIAL'];row_number=7;checked=0
    for department in departments:
        for account in accounts:
            matches=[r for r in rows if r[1]==department and r[2]==account]
            if len(matches)!=5:raise AssertionError('Incomplete forecast output')
            for fy,dn,aid,an,flow,cents in matches:
                address=chr(71+fy-2027)+str(row_number)
                if abs(values[address]*100-cents)>.001:raise AssertionError(f'Saved workbook differs from SQL at {address}')
                checked+=1
            row_number+=1
    db.close()
    charts=[n for n in z.namelist() if '/charts/' in n and n.endswith('.xml')]
    if len(charts)!=1:raise AssertionError('Expected one native chart')
    chart=z.read(charts[0]).decode().upper()
    if '27747E' not in chart or 'C56538' not in chart:raise AssertionError('Chart color mismatch')
    result={'local_documentation_links':'passed','saved_workbook_forecasts_compared_to_sql':checked,
            'saved_formula_cells':formulas,'cached_formula_errors':errors,'worksheets':len(sheets),
            'native_charts':len(charts),'workbook_case_checked':'Base',
            'desktop_excel_recalculation_tested':False}
    path=ROOT/'reports/validation/release_checks.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
