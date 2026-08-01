"""Sealed suite for gc-424. Do NOT edit; the grader hash-checks work copies."""
import unittest

import ledgerlib as L

J = [
    {"account": "cash", "debit": 100.0, "credit": 0.0},
    {"account": "sales", "debit": 0.0, "credit": 100.0},
    {"account": "cash", "debit": 40.0, "credit": 0.0},
    {"account": "fees", "debit": 0.0, "credit": 15.0},
]


class TestLedger(unittest.TestCase):
    def test_validate_ok(self):
        e = L.validate_entry({"account": "cash", "debit": 5})
        self.assertEqual(e, {"account": "cash", "debit": 5.0, "credit": 0.0})

    def test_validate_rejects_zero_movement(self):
        with self.assertRaises(ValueError):
            L.validate_entry({"account": "cash"})

    def test_validate_rejects_negative(self):
        with self.assertRaises(ValueError):
            L.validate_entry({"account": "cash", "debit": -1})

    def test_validate_rejects_both_sides(self):
        with self.assertRaises(ValueError):
            L.validate_entry({"account": "cash", "debit": 1, "credit": 1})

    def test_post_appends_without_mutation(self):
        j2 = L.post(J, [{"account": "cash", "credit": 10}])
        self.assertEqual(len(j2), 5)
        self.assertEqual(len(J), 4)

    def test_account_balance(self):
        self.assertEqual(L.account_balance(J, "cash"), 140.0)
        self.assertEqual(L.account_balance(J, "sales"), -100.0)
        self.assertEqual(L.account_balance(J, "ghost"), 0.0)

    def test_trial_balance(self):
        self.assertEqual(L.trial_balance(J), 25.0)
        self.assertEqual(L.trial_balance([]), 0.0)

    def test_running_totals(self):
        self.assertEqual(L.running_totals(J), [100.0, 0.0, 40.0, 25.0])
        self.assertEqual(L.running_totals([]), [])

    def test_accounts_sorted_unique(self):
        self.assertEqual(L.accounts(J), ["cash", "fees", "sales"])

    def test_largest_movement(self):
        self.assertEqual(L.largest_movement(J)["account"], "cash")
        self.assertIsNone(L.largest_movement([]))

    def test_largest_movement_credit_side(self):
        j = [{"account": "a", "debit": 3.0, "credit": 0.0},
             {"account": "b", "debit": 0.0, "credit": 9.0}]
        self.assertEqual(L.largest_movement(j)["account"], "b")


if __name__ == "__main__":
    unittest.main()
