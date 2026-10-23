"""Build the employer-facing PDF and GitHub chart assets from read-only SQLite.

Install requirements-report.txt, then run: python3 scripts/build_report.py
"""
from pathlib import Path
import argparse
import datetime as dt
import json
import sqlite3
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.shapes import Drawing, String, Line, Rect, Circle, PolyLine
from reportlab.graphics import renderSVG
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
NAVY = colors.HexColor('#16344D')
TEAL = colors.HexColor('#167B82')
RUST = colors.HexColor('#B85E3B')
INK = colors.HexColor('#243B4D')
MUTED = colors.HexColor('#5C6E7B')
PALE = colors.HexColor('#EDF3F6')
RULE = colors.HexColor('#D9E2E8')
W = 528
STYLES = {
 'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=29, leading=33, textColor=NAVY, spaceAfter=12),
 'h1': ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=21, leading=25, textColor=NAVY, spaceAfter=10),
 'h2': ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=NAVY, spaceBefore=12, spaceAfter=6),
 'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10, leading=14.3, textColor=INK, spaceAfter=8),
 'small': ParagraphStyle('small', fontName='Helvetica', fontSize=8, leading=11, textColor=MUTED, spaceAfter=7),
 'kicker': ParagraphStyle('kicker', fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=TEAL, spaceAfter=8),
 'cell': ParagraphStyle('cell', fontName='Helvetica', fontSize=9.3, leading=12.5, textColor=INK),
 'white': ParagraphStyle('white', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.white),
}

def p(text, style='body'):
    return Paragraph(text, STYLES[style])

def dollars(cents, whole=False):
    v=cents/100
    s=f'${(abs(cents)+50)//100:,.0f}' if whole else f'${abs(v):,.2f}'
    return '('+s+')' if v<0 else s

def tab(headers, rows, widths, right=None):
    data=[[p(escape(str(v)),'white') for v in headers]]
    data += [[p(escape(str(v)),'cell') for v in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
    commands=[('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
              ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
              ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
              ('LINEBELOW',(0,0),(-1,0),.6,NAVY)]
    for i in range(1,len(data)):
        if i%2:commands.append(('BACKGROUND',(0,i),(-1,i),PALE))
    t.setStyle(TableStyle(commands))
    return t

def cards(items):
    cells=[]
    for value,label in items:
        cells.append(Paragraph('<font size="20" color="#16344D"><b>'+escape(value)+'</b></font><br/><br/><font size="8.5" color="#5C6E7B">'+escape(label)+'</font>',ParagraphStyle('card',fontName='Helvetica',fontSize=10,leading=12)))
    t=Table([cells],colWidths=[W/len(items)]*len(items))
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('TOPPADDING',(0,0),(-1,-1),15),('BOTTOMPADDING',(0,0),(-1,-1),15),('LEFTPADDING',(0,0),(-1,-1),12),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBEFORE',(1,0),(-1,-1),1,colors.white)]))
    return t

def trend_chart(annual):
    d=Drawing(W,178);left,bottom,width,height=48,31,458,120
    lo,hi=7,10
    def yy(cents):return bottom+(cents/100000000-lo)/(hi-lo)*height
    for n in range(lo,hi+1):
        y=bottom+(n-lo)/(hi-lo)*height
        d.add(Line(left,y,left+width,y,strokeColor=RULE,strokeWidth=.55))
        d.add(String(left-9,y-3,f'${n:.0f}M',fontName='Helvetica',fontSize=8,textAnchor='end',fillColor=MUTED))
    for i,r in enumerate(annual):
        x=left+i*width/4
        d.add(String(x,12,f"FY {r['fiscal_year']-1}-{str(r['fiscal_year'])[-2:]}",fontName='Helvetica',fontSize=8,textAnchor='middle',fillColor=MUTED))
    for key,col in [('funding_cents',TEAL),('expense_cents',RUST)]:
        pts=[(left+i*width/4,yy(r[key])) for i,r in enumerate(annual)]
        d.add(PolyLine([n for xy in pts for n in xy],strokeColor=col,strokeWidth=2.1))
        for x,y in pts:d.add(Circle(x,y,2.5,fillColor=col,strokeColor=colors.white,strokeWidth=.6))
    for x,label,col in [(291,'Funding',TEAL),(394,'Expense',RUST)]:
        d.add(Line(x,169,x+17,169,strokeColor=col,strokeWidth=2))
        d.add(String(x+23,166,label,fontName='Helvetica',fontSize=8.5,fillColor=INK))
    d.add(String(0,165,'Base scenario | USD millions',fontName='Helvetica',fontSize=8.5,fillColor=MUTED))
    return d

def variance_chart(variance):
    d=Drawing(W,145);left,width=133,354
    for n in [0,50,100,150,200]:
        x=left+n/200*width;d.add(Line(x,29,x,129,strokeColor=RULE,strokeWidth=.5));d.add(String(x,14,str(n),fontSize=8,fontName='Helvetica',textAnchor='middle',fillColor=MUTED))
    for i,r in enumerate(variance):
        y=112-i*34;value=-r['favorable_variance_usd']/1000
        d.add(String(left-10,y+4,r['department_name'],fontName='Helvetica',fontSize=8.5,textAnchor='end',fillColor=INK))
        d.add(Rect(left,y,width*value/200,18,fillColor=RUST,strokeColor=None))
        d.add(String(left+width*value/200+5,y+5,f'{value:,.2f}',fontName='Helvetica-Bold',fontSize=8,fillColor=INK))
    return d

def workflow():
    d=Drawing(W,98)
    boxes=[(0,58,148,'Synthetic CSV inputs'),(188,58,148,'SQLite + SQL queries'),(376,58,152,'Exports + PDF report'),
           (0,4,148,'Same input snapshot'),(188,4,340,'Excel formulas + editable scenario assumptions')]
    for x,y,w,label in boxes:
        d.add(Rect(x,y,w,31,fillColor=PALE,strokeColor=RULE,strokeWidth=.5))
        d.add(String(x+w/2,y+12,label,fontName='Helvetica',fontSize=8.5,textAnchor='middle',fillColor=NAVY))
    for x,y in [(151,73),(339,73),(151,19)]:
        d.add(Line(x,y,x+30,y,strokeColor=TEAL,strokeWidth=1))
        d.add(Line(x+30,y,x+26,y+3,strokeColor=TEAL,strokeWidth=1));d.add(Line(x+30,y,x+26,y-3,strokeColor=TEAL,strokeWidth=1))
    return d

def get_results():
    path=ROOT/'data/processed/budget_analysis.sqlite'
    c=sqlite3.connect('file:'+path.as_posix()+'?mode=ro',uri=True)
    c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON')
    q=lambda name,params: [dict(r) for r in c.execute((ROOT/'sql/queries'/name).read_text(),params)]
    variance=q('department_variance.sql',{'fiscal_year':2026})
    forecast=q('five_year_forecast.sql',{'scenario':'Base'})
    exceptions=q('account_exceptions.sql',{'fiscal_year':2026})
    annual=[]
    for fy in range(2027,2032):
        funding=sum(r['amount_cents'] for r in forecast if r['fiscal_year']==fy and r['flow_type']=='Funding')
        expense=sum(r['amount_cents'] for r in forecast if r['fiscal_year']==fy and r['flow_type']=='Expense')
        annual.append(dict(fiscal_year=fy,funding_cents=funding,expense_cents=expense,gap_cents=funding-expense))
    rates=[dict(r) for r in c.execute("SELECT a.account_name, r.scenario, r.rate_ppm FROM forecast_rates r JOIN accounts a USING(account_id) WHERE r.fiscal_year=2027 ORDER BY a.flow_type DESC,a.account_id")]
    count=c.execute('SELECT COUNT(*) FROM monthly_financials').fetchone()[0]
    c.close()
    return variance,annual,exceptions,rates,count

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date',default='2026-10-23',help='Report publication date, YYYY-MM-DD')
    args=parser.parse_args();date=dt.date.fromisoformat(args.date).strftime('%B %d, %Y').replace(' 0',' ')
    variance,annual,exceptions,rates,count=get_results()
    assert count==360 and len(annual)==5
    proposal=[r for r in annual if r['fiscal_year'] in [2028,2029]]
    expense=sum(r['expense_cents'] for r in proposal);gap=sum(r['gap_cents'] for r in proposal)
    overspend=-sum(r['favorable_variance_usd'] for r in variance)
    figure_dir=ROOT/'assets/figures';figure_dir.mkdir(parents=True,exist_ok=True)
    renderSVG.drawToFile(trend_chart(annual),str(figure_dir/'forecast_outlook.svg'))
    renderSVG.drawToFile(variance_chart(variance),str(figure_dir/'expense_variance.svg'))
    dest=ROOT/'reports/Civic_Operating_Budget_Analysis_Report.pdf'
    story=[]
    story += [p('INDEPENDENT PORTFOLIO PROJECT | SYNTHETIC DATA','kicker'),p('Civic Operating<br/>Budget Analysis','title'),
              p('Excel reporting, SQL analysis and scenario-based operating planning.'),
              p(f'<b>Sileshi Hirpa</b> | {date} | Base scenario','small'),Spacer(1,5),
              cards([(f'${overspend:,.0f}','FY 2025-26 expense above budget'),(f'${expense/100/1e6:.2f}M','FY 2027-29 proposed expense'),(f'${-gap/100:,.0f}','FY 2027-29 modeled funding gap')]),Spacer(1,12),
              p('Purpose','h2'),
              p('Translate monthly financial records into a clear budget review: identify expense variances, compare departments, project funding and expense over five years, and summarize a two-year spending proposal.'),
              trend_chart(annual),
              p('Three findings for a finance reviewer','h2'),
              p('<b>Expense review:</b> Public Works has the largest synthetic department overspend, led by personnel. Account-level review helps focus follow-up questions.'),
              p('<b>Planning outlook:</b> Assumed expense growth exceeds funding growth. The modeled annual shortfall widens from $193,747 to $768,671 over the forecast horizon.'),
              p('<b>Two-year proposal:</b> The FY 2027-29 proposal includes FY 2027-28 and FY 2028-29. It is a planning estimate, not an adopted appropriation.'),
              p('Scope: 360 monthly records, three fictional departments and five accounts. No City of Alameda financial records, employment relationship or ERP experience is represented.','small')]
    story += [PageBreak(),p('01 | Budget performance','kicker'),p('Where spending differs<br/>from the plan','h1'),
              p('Full FY 2025-26. Favorable expense variance equals budget minus actual. A negative value means expense exceeded budget.'),
              tab(['Department','Budget','Actual','Favorable variance'],[[r['department_name'],f"${r['budget_usd']:,.0f}",f"${r['actual_usd']:,.0f}",f"(${abs(r['favorable_variance_usd']):,.0f})"] for r in variance],[151,116,116,145]),
              p('Expense above budget | USD thousands','h2'),variance_chart(variance),
              p('Largest account exceptions','h2'),
              tab(['Department / account','Overspend','Above budget'],[[r['department_name']+' / '+r['account_name'],f"${r['overspend_usd']:,.0f}",f"{r['overspend_pct']:.1%}"] for r in sorted(exceptions,key=lambda r:r['overspend_usd'],reverse=True)[:4]],[312,111,105]),
              p('How to use this review','h2'),
              p('Confirm the accounting period and classification first. Then investigate whether each variance reflects timing, a one-time item, a recurring price change, or a service-volume change. Obtain operational explanations before proposing a budget adjustment.'),
              p('The synthetic differences were deliberately generated. They demonstrate an exception-review process and do not establish actual departmental inefficiency, staffing needs or achievable savings.','small'),
              p('Source: sql/queries/department_variance.sql and account_exceptions.sql; reports/exports contains the corresponding CSV outputs.','small')]
    story += [PageBreak(),p('02 | Operating outlook','kicker'),p('Five years of projections.<br/>One two-year proposal.','h1'),
              p('The model compounds each department/account baseline using editable annual growth assumptions. Dollar amounts are rounded to cents before projecting the next year.'),
              tab(['Fiscal year','Funding','Operating expense','Funding less expense'],[[f"{r['fiscal_year']-1}-{str(r['fiscal_year'])[-2:]}",dollars(r['funding_cents'],True),dollars(r['expense_cents'],True),dollars(r['gap_cents'],True)] for r in annual],[94,140,147,147]),
              p('FY 2027-29 proposal | Base scenario','h2'),
              tab(['Measure','Two-year amount'],[['Assigned support + service fees',dollars(sum(r['funding_cents'] for r in proposal))],['Operating expense',dollars(expense)],['Funding less expense',dollars(gap)]],[340,188]),
              p('Growth assumptions | Annual rates','h2')]
    mapping={r['account_name']:{x['scenario']:x['rate_ppm']/1e6 for x in rates if x['account_name']==r['account_name']} for r in rates}
    story += [tab(['Driver','Base','Constrained'],[[name,f"{m['Base']:.1%}",f"{m['Constrained']:.1%}"] for name,m in mapping.items()],[306,111,111]),
              p('The same illustrative rates apply in each of the five forecast years in the published snapshot. Constrained assumptions are provided for workbook exploration; the reported amounts above use Base. These are judgmental inputs, not statistically estimated predictions.','small'),
              p('Assigned support is funding allocated to this three-department scope. It is not additional consolidated municipal revenue. A funding gap is not a cash, reserve or fund-balance calculation.','small'),
              p('Source: sql/queries/five_year_forecast.sql and data/raw/forecast_rates.csv. FY labels use a July-June convention and the ending year.','small')]
    story += [PageBreak(),p('03 | Methods and confidence','kicker'),p('Traceable calculations.<br/>Clear practical limits.','h1'),workflow(),
              p('Methods used','h2'),
              tab(['Area','Implementation'],[
                ['Data integrity','Composite monthly keys, reference-table joins, fiscal-period checks and validated integer-cent amounts.'],
                ['SQL analysis','Grouped views, conditional variance signs, DENSE_RANK and ROW_NUMBER for exception review, and a recursive forecast CTE.'],
                ['Excel planning','SUMIFS and COUNTIFS, one scenario selector, linked growth assumptions, formula-based forecasts and a native chart.'],
                ['Reconciliation','Compare source controls, department totals and saved forecast values against independent SQL results.']],[110,418]),
              p('Validation evidence','h2'),
              p('<b>Nine model tests passed.</b> Tests cover duplicates, missing records/drivers, foreign keys, fiscal cutoffs, zero denominators, variance direction and the -100% growth boundary.'),
              p('<b>150 SQL forecast results checked:</b> 75 account/year amounts in each of two scenarios matched independent Decimal calculations. All 75 saved Base workbook forecast amounts also matched SQL. Historical actuals stayed unchanged in workbook scenario checks.'),
              p('Refresh and verification limits','h2'),
              p('Excel contains an embedded snapshot. SQL rebuilds do not automatically refresh Excel, and edits in Excel do not update SQLite. Desktop Excel recalculation was not independently certified. The forecast is an operating model, without detailed position control, capital planning, fund accounting, cash flow or reserve schedules.'),
              p('Authorship and evidence','h2'),
              p('Prepared by Sileshi Hirpa with AI assistance, drawing on Excel and SQL coursework concepts. Synthetic data and assumptions are disclosed throughout. The project demonstrates analytical work and its verification; it claims no actual municipal savings, employer outcomes or ERP implementation.'),
              p('Review the workbook in excel/, SQL in sql/, the methodology in docs/, and the test and validation evidence in reports/validation/. The repository provides the underlying files for inspection and reproduction.','small')]
    def decorate(c,doc):
        c.saveState();c.setStrokeColor(RULE);c.setLineWidth(.5);c.line(42,755,570,755)
        c.setFont('Helvetica-Bold',7.5);c.setFillColor(NAVY);c.drawString(42,766,'SILESHI HIRPA | ANALYTICS PORTFOLIO')
        c.setFont('Helvetica',7);c.setFillColor(MUTED);c.drawRightString(570,766,'CIVIC OPERATING BUDGET ANALYSIS')
        c.line(42,37,570,37);c.drawString(42,25,'Synthetic portfolio simulation | Base scenario | '+dt.date.fromisoformat(args.date).strftime('%B %Y'))
        c.drawRightString(570,25,f'{doc.page} / 4');c.restoreState()
    doc=SimpleDocTemplate(str(dest),pagesize=(612,792),leftMargin=42,rightMargin=42,topMargin=52,bottomMargin=49,
                          title='Civic Operating Budget Analysis - Portfolio Report',author='Sileshi Hirpa',subject='Synthetic Excel and SQL budget analysis portfolio')
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
    pdf=PdfReader(dest);assert len(pdf.pages)==4,f'Unexpected page count: {len(pdf.pages)}'
    expected=['Civic Operating','Budget performance','Operating outlook','Methods and confidence']
    for page,text in zip(pdf.pages,expected):assert text in page.extract_text(),text
    (ROOT/'reports/validation/report_validation.json').write_text(json.dumps({'report':dest.name,'pages':4,'scenario':'Base','source_monthly_records':count,'generated_from':'read-only SQLite','date':args.date},indent=2)+'\n')
    print(f'Created {dest} (4 pages) and two SVG figures.')

if __name__=='__main__':main()
