-- All overspent FY account lines, ranked within their department.
SELECT department_name, account_name,
       -favorable_variance_cents / 100.0 AS overspend_usd,
       -favorable_variance_pct AS overspend_pct,
       ROW_NUMBER() OVER (
           PARTITION BY department_name ORDER BY favorable_variance_cents, account_id
       ) AS review_order
FROM annual_account_variance
WHERE fiscal_year = :fiscal_year AND flow_type = 'Expense'
  AND favorable_variance_cents < 0
ORDER BY department_name, review_order;
