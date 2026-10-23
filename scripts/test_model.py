"""Independent financial and database checks. Run: python3 scripts/test_model.py"""
import copy
from decimal import Decimal, ROUND_HALF_UP
import sqlite3
import unittest
import rebuild

class BudgetModelTests(unittest.TestCase):
    def setUp(self):
        self.records, self.rates = rebuild.generate()
        self.db = rebuild.build_database(':memory:', self.records, self.rates)

    def tearDown(self):
        self.db.close()

    def test_reproducible_and_complete(self):
        self.assertEqual((self.records, self.rates), rebuild.generate())
        self.assertEqual(len(self.records), 360)
        self.assertEqual(len(self.rates), 50)
        self.assertEqual(self.db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_duplicate_missing_and_unknown_dimensions_rejected(self):
        for mutation in ['duplicate', 'missing', 'unknown']:
            records = copy.deepcopy(self.records)
            if mutation == 'duplicate': records[1] = records[0].copy()
            if mutation == 'missing': records.pop()
            if mutation == 'unknown': records[0]['department_id'] = 'UNKNOWN'
            with self.assertRaises(ValueError): rebuild.validate(records, self.rates)

    def test_date_cutoffs_and_database_constraints(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO monthly_financials VALUES ('2027-06-01',2026,'FIN','PAY',1,1)")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO monthly_financials VALUES ('2025-07-01',2026,'UNKNOWN','PAY',1,1)")
        self.db.rollback()

    def test_missing_driver_and_invalid_rate_rejected(self):
        with self.assertRaises(ValueError): rebuild.validate(self.records, self.rates[:-1])
        rates = copy.deepcopy(self.rates); rates[0]['rate_ppm'] = -1000001
        with self.assertRaises(ValueError): rebuild.validate(self.records, rates)

    def test_zero_budget_percentage_is_null(self):
        self.db.execute("UPDATE monthly_financials SET budget_cents=0 WHERE department_id='FIN' AND account_id='PAY'")
        pct = self.db.execute("SELECT favorable_variance_pct FROM annual_account_variance WHERE fiscal_year=2026 AND department_name='Finance' AND account_id='PAY'").fetchone()[0]
        self.assertIsNone(pct)

    def test_expense_sign_and_independent_control(self):
        rows = rebuild.query(self.db, 'department_variance.sql', fiscal_year=2026)
        self.assertEqual(rows[0]['department_name'], 'Public Works')
        self.assertEqual(rows[0]['favorable_variance_usd'], -174250)
        self.assertEqual(sum(r['budget_usd'] for r in rows), 7220000)
        self.assertEqual(sum(r['actual_usd'] for r in rows), 7545050)
        for r in rows:
            self.assertAlmostEqual(r['favorable_variance_usd'], r['budget_usd']-r['actual_usd'])

    def test_both_scenarios_against_decimal_compounding(self):
        original = self.db.execute('SELECT SUM(actual_cents) FROM monthly_financials').fetchone()[0]
        for scenario in ['Base', 'Constrained']:
            actual = rebuild.query(self.db, 'five_year_forecast.sql', scenario=scenario)
            self.assertEqual(len(actual), 75)
            by_key = {(r['fiscal_year'],r['department_name'],r['account_id']):r['amount_cents'] for r in actual}
            for did, name in rebuild.DEPARTMENTS:
                for aid, _, _ in rebuild.ACCOUNTS:
                    total = sum(r['actual_cents'] for r in self.records if r['fiscal_year']==2026 and r['department_id']==did and r['account_id']==aid)
                    for year in range(2027,2032):
                        rate = next(r['rate_ppm'] for r in self.rates if r['scenario']==scenario and r['account_id']==aid and r['fiscal_year']==year)
                        total = int((Decimal(total)*(1+Decimal(rate)/1000000)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
                        self.assertEqual(by_key[year,name,aid], total)
            self.assertEqual(self.db.execute('SELECT SUM(actual_cents) FROM monthly_financials').fetchone()[0], original)

    def test_proposal_uses_matching_two_year_period(self):
        rows = rebuild.query(self.db, 'five_year_forecast.sql', scenario='Base')
        proposal = sum(r['amount_cents'] for r in rows if r['fiscal_year'] in [2028,2029] and r['flow_type']=='Expense')
        self.assertEqual(proposal, 1672929339)

    def test_negative_one_hundred_percent_growth_boundary(self):
        self.db.execute("UPDATE forecast_rates SET rate_ppm=-1000000 WHERE scenario='Base' AND account_id='MATERIAL' AND fiscal_year=2027")
        rows = rebuild.query(self.db, 'five_year_forecast.sql', scenario='Base')
        self.assertTrue(all(r['amount_cents']==0 for r in rows if r['account_id']=='MATERIAL'))

if __name__ == '__main__': unittest.main(verbosity=2)
