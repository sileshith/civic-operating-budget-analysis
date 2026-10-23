# Interview guide

## Opening explanation

"I developed an AI-assisted Excel and SQLite portfolio project to practice budget analysis with synthetic data. It compares department budgets and actuals, projects funding and expense over five years, and summarizes a two-year spending proposal. I checked that the saved forecasts agree with SQL. This is an independent simulation, not work performed for a city."

Use this framing after reviewing and being able to explain the work yourself.

## Five-minute demonstration

1. **Monthly data:** explain one record's month/department/account grain and the composite key.
2. **Summary:** D10 uses SUMIFS to select fiscal year 2026 and Expense; E10 sums actuals. F10 is budget minus actual; G10 divides by budget and returns unavailable for a zero denominator.
3. **Department plan:** F9 sums Finance personnel's 12 monthly actuals ($730,800). G9 applies 4.5% growth, yielding $763,686. Subsequent years compound from the previous amount.
4. **Assumptions:** change D4 to Constrained. Forecasts change while actuals stay fixed. Restore Base.
5. **Review:** explain the zero differences between source controls and workbook outputs. This sheet observes results; forecasts do not read its checks.

## Explain SQL

- JOIN attaches descriptions using unique IDs.
- GROUP BY / SUM aggregates monthly records to annual results.
- CASE applies the appropriate funding/expense variance direction.
- NULLIF prevents a zero-budget division.
- DENSE_RANK gives tied overspends the same rank.
- ROW_NUMBER with PARTITION BY sequences exceptions inside each department.
- The recursive CTE starts with actuals, joins the next year's rate and repeats through fiscal year 2031.

## Questions to prepare for

**Accuracy:** discuss validation, matching periods, integer cents, independent Decimal calculations, scenario checks and 75 saved workbook-to-SQL comparisons.

**Funding gap:** expense assumptions grow faster than funding assumptions. This is a constructed scenario, not Alameda's deficit.

**Recommendations:** investigate timing, one-time items, contract rates, service volumes and classification before proposing changes.

**Refresh:** Excel is an embedded snapshot. It is not a live database connection.

**Experience:** the project demonstrates transferable skills, not municipal employment, actual savings or ERP experience.

**AI:** explain the assistance received and the work you personally reviewed, practiced or extended. Do not claim independent authorship of unfamiliar code.
