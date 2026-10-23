# Data dictionary

All values are synthetic. Fiscal years use July-June and are labeled by ending year.

## `data/raw/`

| File | Grain / purpose |
|---|---|
| monthly_financials.csv | 360 month/department/account records; IDs and integer cents |
| departments.csv | Three department IDs and names |
| accounts.csv | Five account IDs, names and Funding/Expense types |
| forecast_rates.csv | 50 rates: two scenarios x five years x five accounts |
| workbook_monthly_inputs.csv | Same 360 records using readable names, dates and USD |

### Financial fields

| Field | Definition |
|---|---|
| month_start | ISO date; first calendar day of the reporting month |
| fiscal_year | Ending year, 2025 or 2026 |
| department_id | FIN, PW or PR; department foreign key |
| account_id | ALLOC, FEES, PAY, CONTRACT or MATERIAL; account foreign key |
| budget_cents | Nonnegative monthly budget in integer USD cents |
| actual_cents | Nonnegative synthetic monthly actual in integer USD cents |

### Growth fields

| Field | Definition |
|---|---|
| scenario | Base or Constrained |
| fiscal_year | Forecast ending year, 2027-2031 |
| account_id | Account receiving the assumption |
| rate_ppm | Decimal annual growth x 1,000,000; 45,000 means 4.5% |

Growth is shared across departments for the same account/year. Rates are assumptions, not fitted estimates.

## `data/processed/`

`budget_analysis.sqlite` contains four tables and three reporting views. `model_snapshot.json` records generated inputs and selected-scenario results for traceability; it is not an additional authoritative input.

| View | Grain |
|---|---|
| annual_account_variance | Fiscal year / department / account |
| department_expense_variance | Fiscal year / department; expenses only |
| monthly_expense_variance | Month / department; expenses only |

## `reports/exports/`

`department_variance.csv` contains annual expense comparisons and overspend rankings. `account_exceptions.csv` contains overspent accounts and within-department review order. `forecast_detail.csv` contains 75 selected-scenario projections in cents.

The export scenario and source hashes are recorded in `data/manifest.json`. The PDF always reports Base explicitly. The workbook requires manual alignment after source or assumption changes.
