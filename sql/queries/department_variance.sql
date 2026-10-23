-- Matching full fiscal year. Positive = under budget; negative = overspend.
SELECT department_name, ROUND(budget_cents / 100.0, 2) AS budget_usd,
       ROUND(actual_cents / 100.0, 2) AS actual_usd,
       ROUND(favorable_variance_cents / 100.0, 2) AS favorable_variance_usd,
       favorable_variance_pct,
       DENSE_RANK() OVER (ORDER BY favorable_variance_cents) AS overspend_rank
FROM department_expense_variance
WHERE fiscal_year = :fiscal_year
ORDER BY overspend_rank, department_name;
