-- Synthetic operating plan. Currency is stored as integer US cents.
PRAGMA foreign_keys = ON;
CREATE TABLE departments (
    department_id TEXT PRIMARY KEY,
    department_name TEXT NOT NULL UNIQUE
);
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL UNIQUE,
    flow_type TEXT NOT NULL CHECK (flow_type IN ('Funding', 'Expense'))
);
CREATE TABLE monthly_financials (
    month_start TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL CHECK (fiscal_year BETWEEN 2025 AND 2026),
    department_id TEXT NOT NULL REFERENCES departments(department_id),
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    budget_cents INTEGER NOT NULL CHECK (budget_cents >= 0),
    actual_cents INTEGER NOT NULL CHECK (actual_cents >= 0),
    PRIMARY KEY (month_start, department_id, account_id),
    CHECK (date(month_start) IS NOT NULL AND strftime('%d', month_start) = '01'),
    CHECK (fiscal_year = CAST(strftime('%Y', month_start) AS INTEGER)
          + CASE WHEN CAST(strftime('%m', month_start) AS INTEGER) >= 7 THEN 1 ELSE 0 END)
);
CREATE TABLE forecast_rates (
    scenario TEXT NOT NULL CHECK (scenario IN ('Base', 'Constrained')),
    fiscal_year INTEGER NOT NULL CHECK (fiscal_year BETWEEN 2027 AND 2031),
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    rate_ppm INTEGER NOT NULL CHECK (rate_ppm >= -1000000),
    PRIMARY KEY (scenario, fiscal_year, account_id)
);
CREATE INDEX financials_fy_department ON monthly_financials(fiscal_year, department_id);

CREATE VIEW annual_account_variance AS
SELECT f.fiscal_year, d.department_name, a.account_id, a.account_name, a.flow_type,
       SUM(f.budget_cents) AS budget_cents,
       SUM(f.actual_cents) AS actual_cents,
       CASE WHEN a.flow_type = 'Expense'
            THEN SUM(f.budget_cents) - SUM(f.actual_cents)
            ELSE SUM(f.actual_cents) - SUM(f.budget_cents) END AS favorable_variance_cents,
       CASE WHEN SUM(f.budget_cents) = 0 THEN NULL
            ELSE (CASE WHEN a.flow_type = 'Expense'
                       THEN SUM(f.budget_cents) - SUM(f.actual_cents)
                       ELSE SUM(f.actual_cents) - SUM(f.budget_cents) END)
                 * 1.0 / SUM(f.budget_cents) END AS favorable_variance_pct
FROM monthly_financials f
JOIN departments d ON d.department_id = f.department_id
JOIN accounts a ON a.account_id = f.account_id
GROUP BY f.fiscal_year, d.department_name, a.account_id, a.account_name, a.flow_type;

CREATE VIEW department_expense_variance AS
SELECT fiscal_year, department_name,
       SUM(budget_cents) AS budget_cents, SUM(actual_cents) AS actual_cents,
       SUM(favorable_variance_cents) AS favorable_variance_cents,
       SUM(favorable_variance_cents) * 1.0 / NULLIF(SUM(budget_cents), 0) AS favorable_variance_pct
FROM annual_account_variance WHERE flow_type = 'Expense'
GROUP BY fiscal_year, department_name;

CREATE VIEW monthly_expense_variance AS
SELECT f.month_start, f.fiscal_year, d.department_name,
       SUM(f.budget_cents) AS budget_cents, SUM(f.actual_cents) AS actual_cents,
       SUM(f.budget_cents) - SUM(f.actual_cents) AS favorable_variance_cents
FROM monthly_financials f
JOIN departments d ON d.department_id = f.department_id
JOIN accounts a ON a.account_id = f.account_id
WHERE a.flow_type = 'Expense'
GROUP BY f.month_start, f.fiscal_year, d.department_name;
