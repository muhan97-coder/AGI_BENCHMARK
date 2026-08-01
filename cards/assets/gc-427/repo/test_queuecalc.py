"""Sealed suite for gc-427. Do NOT edit; the grader hash-checks work copies."""
import unittest

import queuecalc as Q

JOBS = [
    {"id": "a", "priority": 2, "submitted": 0, "duration": 3},
    {"id": "b", "priority": 1, "submitted": 0, "duration": 2},
    {"id": "c", "priority": 1, "submitted": 4, "duration": 1},
    {"id": "d", "priority": 3, "submitted": 1, "duration": 2},
]


class TestQueueCalc(unittest.TestCase):
    def test_validate_rejects_bad_duration(self):
        with self.assertRaises(ValueError):
            Q.validate_job({"id": "x", "priority": 1, "submitted": 0, "duration": 0})

    def test_validate_rejects_missing_id(self):
        with self.assertRaises(ValueError):
            Q.validate_job({"priority": 1, "submitted": 0, "duration": 1})

    def test_pop_order_priority_first(self):
        self.assertEqual(Q.pop_order(JOBS), ["b", "c", "a", "d"])

    def test_pop_order_tie_breaks(self):
        jobs = [
            {"id": "z", "priority": 1, "submitted": 0, "duration": 1},
            {"id": "y", "priority": 1, "submitted": 0, "duration": 1},
        ]
        self.assertEqual(Q.pop_order(jobs), ["y", "z"])

    def test_completion_times(self):
        done = Q.completion_times(JOBS)
        self.assertEqual(done["b"], 2)
        self.assertEqual(done["c"], 5)
        self.assertEqual(done["a"], 8)
        self.assertEqual(done["d"], 10)

    def test_average_wait(self):
        # waits: b=0, c=0, a=5, d=7 -> mean 3.0
        self.assertAlmostEqual(Q.average_wait(JOBS), 3.0)

    def test_average_wait_empty(self):
        self.assertEqual(Q.average_wait([]), 0.0)

    def test_throughput(self):
        self.assertEqual(Q.throughput(JOBS, 5), 2)
        self.assertEqual(Q.throughput(JOBS, 10), 4)
        self.assertEqual(Q.throughput(JOBS, 1), 0)


if __name__ == "__main__":
    unittest.main()
