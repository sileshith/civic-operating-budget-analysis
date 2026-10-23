-- One selected scenario, one recursive build. No approved appropriations implied.
-- Each annual account projection is rounded to cents before the following year.
WITH RECURSIVE plan(fiscal_year, department_id, account_id, amount_cents) AS (
    SELECT 2026, department_id, account_id, SUM(actual_cents)
    FROM monthly_financials WHERE fiscal_year = 2026
    GROUP BY department_id, account_id
    UNION ALL
    SELECT p.fiscal_year + 1, p.department_id, p.account_id,
           CAST((p.amount_cents * (1000000 + r.rate_ppm) + 500000)
                / 1000000 AS INTEGER)
    FROM plan p
    JOIN forecast_rates r ON r.account_id = p.account_id
                         AND r.fiscal_year = p.fiscal_year + 1
                         AND r.scenario = :scenario
    WHERE p.fiscal_year < 2031
)
SELECT p.fiscal_year, d.department_name, a.account_id, a.account_name,
       a.flow_type, p.amount_cents
FROM plan p
JOIN departments d ON p.department_id = d.department_id
JOIN accounts a ON p.account_id = a.account_id
WHERE p.fiscal_year > 2026
ORDER BY p.fiscal_year, d.department_name, a.account_id;
