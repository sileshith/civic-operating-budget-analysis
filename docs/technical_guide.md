# Technical guide

Repository note: source CSVs now live in `data/raw/`, the database and snapshot in `data/processed/`, analytical queries in `sql/queries/`, and validation evidence in `reports/validation/`. The workbook's original provenance note names `data/forecast_rates.csv`; that file is now `data/raw/forecast_rates.csv`. The workbook has no external connection, so this textual relocation does not affect formulas. The source workbook was preserved unchanged during repository organization.

**Excel + SQL portfolio project · Synthetic data · Prepared for budget analyst applications**

Start with [the Excel workbook](../excel/Budget_Analysis_Portfolio.xlsx), then read [the findings](../reports/findings.md). This project turns fictional monthly financial records into department expense comparisons, a five-year operating forecast, and a two-year spending proposal.

It is an independent, AI-assisted portfolio project inspired by the Excel reporting and SQL concepts demonstrated in ASU CIS 235, CIS 407 and CIS 409 coursework. It does not copy assignment solutions or represent a course submission. Review the formulas, SQL and assumptions before presenting the work in an interview.

## Question and audience

For a finance reviewer: Which departments and accounts are above budget? How does modeled operating expense compare with available funding over five years? What spending level does the selected scenario imply for a two-year planning period?

The scope mirrors analytical tasks in the supplied City of Alameda Part-Time Budget Analyst description: Excel analysis, reporting, comparisons across departments, forecasting, and budget preparation support. It uses no City of Alameda data, official policies or branding and does not imply work for the City.

## Model scope

- **360 monthly records:** 24 months × three fictional departments × five accounts.
- **Baseline:** full FY 2025-26; FY 2024-25 is also retained in the input data.
- **Five forecast years:** FY 2026-27 through FY 2030-31.
- **FY 2027-29 proposal:** FY 2027-28 plus FY 2028-29, rather than the first two forecast years.
- **Fiscal convention:** July 1–June 30; numeric fiscal years are labeled by ending year. This is an explicit simulation convention.
- **Currency:** integer USD cents in SQL and CSV source records; USD in Excel. Forecast calculations use integer cents and growth rates rounded to one part per million, with each annual account result rounded half up to cents before compounding the next year. This keeps SQL and Excel rounding consistent.
- **Scenarios:** Base and Constrained. One selected scenario feeds one forecast build.

Funding comprises assigned operating support and service fees. Assigned support is a funding allocation to this three-department scope, **not additional consolidated municipal revenue**. Funding less expense is an operating difference, not a cash balance, fund balance or reserve calculation.

## Excel review

Open `excel/Budget_Analysis_Portfolio.xlsx` in Excel.

1. **Summary:** matching-period budget versus actual, department expense variances, five-year outlook and FY 2027-29 proposal.
2. **Assumptions:** choose Base or Constrained in D4. Blue growth-rate inputs are editable. Active rows select the inputs used by the plan.
3. **Department plan:** the full-year baseline and five projected amounts for each department/account, followed by funding/expense totals. Each projection compounds the prior year at the applicable account growth rate. The two-year proposal sums only FY 2027-28 and FY 2028-29.
4. **Monthly data:** all 360 source records, with a filterable Excel Table. Source data is independent of scenario selection.
5. **Review:** original-source controls and a department-summary reconciliation. Forecasts and outputs do not depend on this sheet.

Positive variance is favorable: budget minus actual for expense; actual minus budget for funding. Percentages use matching budget denominators; a zero denominator is unavailable rather than a false 0%. Negative gaps mean modeled expense exceeds the assigned funding and fees in this scope.

The native line chart is linked to workbook results. This workbook uses formulas rather than a PivotTable so that its budget and forecast calculations remain easy to inspect. It does not claim a Power Query connection or an ERP integration.

## SQL and reproducibility

The included SQLite database is `data/processed/budget_analysis.sqlite`. Tables hold departments, accounts, monthly finances and scenario growth rates. Primary/foreign keys, amount checks, fiscal-period checks and an index support integrity and reporting.

The SQL files demonstrate:

- Joins, grouped financial summaries and zero-denominator handling.
- `DENSE_RANK()` for department overspend and `ROW_NUMBER()` for account review order.
- A recursive CTE that compounds one selected scenario through five forecast years.
- Views for annual account variance, department expense variance and monthly expense variance.

To regenerate the synthetic CSV files, SQLite database and SQL reports, run from this project folder:

```sh
python3 scripts/rebuild.py
python3 scripts/test_model.py
```

Python 3 and its standard library are sufficient. No cloud service, credentials or external packages are needed. The deterministic seed is 407409. Each successful run replaces the generated database after the new database passes validation.

To export the Constrained SQL forecast:

```sh
python3 scripts/rebuild.py --case Constrained
```

The selected export case is recorded in `data/manifest.json` and `reports/findings.md`. Run the default command again to restore the published Base exports. The query files use named parameters such as `:scenario` and `:fiscal_year`; the Python runner supplies them.

### Excel refresh boundary

**The workbook contains an embedded snapshot and does not automatically refresh from SQLite or the CSV files.** Rebuilding SQL exports does not alter Excel. Changing the Excel case or growth inputs updates Excel calculations only; it does not update SQLite.

For the same 360-record layout, the human-readable `data/raw/workbook_monthly_inputs.csv` matches the seven columns on Monthly data. After importing it into Excel with real dates and numeric amounts, replace only A2:G361 in a working copy, retaining the headers and table. The normalized `monthly_financials.csv` uses IDs and cents and must not be pasted directly into the USD workbook.

If growth definitions change in `scripts/rebuild.py`, update the corresponding case rates on Assumptions as well before comparing Excel with the regenerated SQL report. Rates in `forecast_rates.csv` are parts per million; divide by 1,000,000 for decimal growth rates. Recalculate and review the controls after any change. Adding months, departments or accounts requires extending the workbook ranges, model rows and SQL coverage rules; this release intentionally covers the fixed, complete 360-record scope.

## Validation performed

- SQL output was checked against independent Decimal calculations for all 75 department/account/year forecasts in both scenarios.
- Tests exercise duplicate keys, missing records/drivers, fiscal cutoffs, foreign keys, zero budget denominators, variance signs and the −100% growth boundary.
- Workbook forecasts were checked for both scenarios; historical actuals remained unchanged. A later-year driver edit and a blank active driver were tested and restored.
- Workbook source controls reconcile to the generated CSV totals. Every sheet's main view was rendered and inspected, and the saved workbook was scanned for formula errors and native chart bindings.

Detailed results are in `reports/validation/validation.md` and `reports/validation/workbook_validation.json`. Workbook tests use the authoring calculation engine; desktop Excel recalculation and interactive behavior were not independently certified.

## Limitations and truthful presentation

The data, account balances, growth assumptions and variances are fictional. The scenario deliberately makes expense growth exceed funding growth. It is an exercise in analysis and reporting, not an empirical finding about city operations. There is no actual staffing plan, position-control model, pension schedule, cash forecast, reserve policy, fund accounting, capital budget, encumbrance process or legal appropriation workflow.

No savings, service improvement or employment experience is claimed. The project establishes no Tyler Munis, OpenGov, TrueComp or other ERP experience. Do not describe the modeled budget as the City of Alameda's budget.

After reviewing and being able to explain the work, a suitable resume entry is:

> **Civic Operating Budget Analysis — Independent Portfolio Project (Synthetic Data)**  
> Built an Excel and SQLite planning model for 360 synthetic monthly financial records across three fictional departments, with budget-versus-actual reporting, a five-year operating forecast and a two-year spending proposal.  
> Used SQL joins, aggregate views, window functions and a recursive CTE to identify expense variances and reconcile forecast results with formula-driven Excel reports.

## Repository map

See the repository README for the current directory tree. Source inputs are in data/raw; generated data and the database are in data/processed; SQL is separated into schema and queries; CSV exports and validation evidence have dedicated report subfolders.
