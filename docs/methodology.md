# Methodology

## Data and scope

One record represents one month, department and account. The 360 synthetic records cover fiscal years ending 2025 and 2026, three fictional departments and five accounts. Source controls, actual/budget factors and seasonality are explicit in `scripts/rebuild.py`; the seed is 407409. No actual municipal transactions or course answer files are included.

Assigned operating support and service fees are Funding; personnel, contracts and materials are Expense. Assigned support is a scope-level allocation, not additional consolidated city revenue. The model does not represent accounting funds, cash or reserves.

## Integrity and variance

Composite monthly keys prevent duplicate month/department/account records. Foreign keys validate dimensions. Database checks enforce fiscal-date alignment and nonnegative amounts; the Python validator also requires complete coverage and integer cents.

Expense favorable variance = budget minus actual. Funding favorable variance = actual minus budget. Department percentages use summed variance divided by summed budget, rather than averaged percentages. A zero denominator is unavailable (SQL NULL / Excel #N/A). Joins use unique dimension keys to avoid multiplying financial records.

## Forecast

Full FY 2025-26 actuals are compounded through fiscal years ending 2027-2031 using a selected scenario's account/year rates. SQL uses a recursive CTE; Excel uses one scenario selector and a single forecast build. Source actuals remain unchanged.

Both implementations use integer cents and rates rounded to one part per million. Each nonnegative annual account amount is rounded half up to cents before the next year compounds. This resolves a one-cent floating-point mismatch found during development.

The FY 2027-29 proposal sums fiscal years ending 2028 and 2029. It is a planning subtotal, not an adopted appropriation.

## Reporting and interpretation

The PDF builder reads SQLite in read-only/query-only mode and executes the saved queries for Base. It generates a four-page report and two vector charts. Its default publication date is October 23, 2026; use `--date YYYY-MM-DD` for another explicit date.

Excel is a separate embedded snapshot. SQL rebuilds do not refresh Excel; Excel edits do not update SQLite. See the technical guide for the manual refresh boundary.

Expense growth deliberately exceeds funding growth in the synthetic scenario. Results demonstrate planning and exception-review methods, not actual departmental inefficiency, staffing needs, forecast accuracy or achievable savings. Real use requires verified source records, accounting definitions, approved assumptions and operational context.
