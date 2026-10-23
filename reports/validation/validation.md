# Validation record

Prepared October 23, 2026 for the published Base snapshot.

## Financial and SQL checks

Nine independent Python/SQLite tests passed:

1. Deterministic generation, complete 360-record coverage, database integrity and foreign keys.
2. Duplicate records, missing records and unknown dimensions rejected.
3. Fiscal-date mismatches and invalid foreign keys rejected by database constraints.
4. Missing forecast drivers and growth below −100% rejected.
5. Zero budget produces a NULL variance percentage rather than 0%.
6. Expense variance signs and independent baseline controls agree.
7. All 75 account/year forecasts in each of two scenarios match independent Decimal compounding; source actuals remain unchanged.
8. The modeled two-year proposal includes only fiscal years ending 2028 and 2029.
9. The −100% growth boundary reduces the selected account to zero without creating a negative amount.

The first verification found a one-cent floating-point rounding difference. The final SQL and workbook use consistent integer-cent arithmetic with growth rates expressed at one-part-per-million precision. This was corrected before release and both scenario tests pass.

## Workbook checks

- Five worksheets, 227 formula cells and one native Excel line chart.
- All 75 forecast cells match the corresponding SQL Base results in the saved XLSX file.
- Both Base and Constrained cases were verified in the authoring calculation engine, covering 150 account/year results.
- Switching cases leaves baseline actuals unchanged.
- Editing the final-year personnel growth assumption changes the relevant forecast.
- Clearing an active funding growth input propagates an unavailable result; it does not silently become zero.
- Temporary input edits were restored. The published workbook case is Base.
- All eight source/reporting reconciliation differences equal 0.00.
- The saved XLSX contains no cached formula errors.
- The native chart's categories and two series reference Summary worksheet cells, and the saved line colors match the intended series colors.
- The main view on every sheet was rendered and visually inspected. Revised summary headers, source alignment and review differences were rechecked after formatting corrections.

## Published reference values

| Measure | Value |
|---|---:|
| FY 2025-26 expense budget | $7,220,000.00 |
| FY 2025-26 synthetic actual expense | $7,545,050.00 |
| Favorable expense variance | −$325,050.00 |
| FY 2027-29 modeled expense | $16,729,293.39 |
| FY 2027-29 funding less expense | −$786,462.85 |

These are fictional model values, not actual City of Alameda results. Source-control sums across Funding and Expense are separate from a net position; the model does not interpret their combined gross total as revenue or expenditure.

## Verification limits

Workbook calculation and scenario tests used the authoring engine. Desktop Excel recalculation, import behavior, printing and interactive chart behavior were not independently certified. The project has no live SQL-to-Excel refresh connection. The full fixed 360-record scope is supported; adding records or new departments/accounts requires extending the workbook and validation coverage.

The SQLite tests and SQL queries ran locally without using or contacting a live government, employer or course database. No course submissions or existing portfolio projects were modified.

## GitHub publication preparation

The repository was reorganized into raw/processed data, schema/query SQL, exports and validation evidence. All nine model tests passed again after the path changes. Local documentation links and the 75 saved workbook-to-SQL forecast comparisons passed. The four-page employer report was rendered and every page visually reviewed. Charts are vector graphics generated from read-only SQLite.

The GitHub Actions workflow is included but has not been run on GitHub. The Excel workbook was preserved byte-for-byte; its original provenance note uses the pre-organization growth CSV path, now documented as data/raw/forecast_rates.csv in the technical guide.
