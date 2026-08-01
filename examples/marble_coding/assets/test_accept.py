"""Sealed acceptance suite for ex-marble_coding (MeetingRoomBooker).

Loads the agent's solution from workspace/solution.py relative to the current
working directory. Graders run their own pinned copy of this file; do not
modify it. The solution is loaded in setUp, not at import time, so a missing
file surfaces as 14 failing tests rather than a collection crash.
"""
import importlib.util
import unittest
from pathlib import Path

SOLUTION = Path("workspace") / "solution.py"


def load_solution():
    if not SOLUTION.is_file():
        raise FileNotFoundError(
            "no solution at workspace/solution.py (run the grader from the "
            "workspace root)")
    spec = importlib.util.spec_from_file_location("ex_marble_solution", SOLUTION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BookerTest(unittest.TestCase):
    def setUp(self):
        self.booker = load_solution().MeetingRoomBooker()
        self.booker.add_room("aurora", 4)
        self.booker.add_room("borealis", 10)

    # --- rooms -----------------------------------------------------------
    def test_duplicate_room_rejected(self):
        with self.assertRaises(ValueError):
            self.booker.add_room("aurora", 6)

    def test_capacity_must_be_positive(self):
        with self.assertRaises(ValueError):
            self.booker.add_room("cygnus", 0)

    # --- booking validation ----------------------------------------------
    def test_unknown_room_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.booker.book("ida", "nowhere", "mon", 9, 10, 2)

    def test_end_must_follow_start(self):
        with self.assertRaises(ValueError):
            self.booker.book("ida", "aurora", "mon", 11, 11, 2)

    def test_hours_stay_within_the_day(self):
        with self.assertRaises(ValueError):
            self.booker.book("ida", "aurora", "mon", -1, 3, 2)
        with self.assertRaises(ValueError):
            self.booker.book("ida", "aurora", "mon", 22, 25, 2)

    def test_attendees_within_capacity(self):
        with self.assertRaises(ValueError):
            self.booker.book("ida", "aurora", "mon", 9, 10, 5)
        with self.assertRaises(ValueError):
            self.booker.book("ida", "aurora", "mon", 9, 10, 0)

    def test_booking_ids_increment_and_skip_rejections(self):
        first = self.booker.book("ida", "aurora", "mon", 9, 10, 2)
        with self.assertRaises(ValueError):
            self.booker.book("ida", "aurora", "mon", 9, 10, 99)
        second = self.booker.book("jo", "borealis", "mon", 9, 10, 2)
        self.assertEqual((first, second), (1, 2))

    def test_overlap_rejected_but_touching_allowed(self):
        self.booker.book("ida", "aurora", "mon", 9, 11, 2)
        with self.assertRaises(ValueError):
            self.booker.book("jo", "aurora", "mon", 10, 12, 2)
        self.assertEqual(self.booker.book("jo", "aurora", "mon", 11, 12, 2), 2)
        self.assertEqual(self.booker.book("jo", "aurora", "tue", 9, 11, 2), 3)

    # --- cancellation -----------------------------------------------------
    def test_cancel_requires_ownership(self):
        booking = self.booker.book("ida", "aurora", "mon", 9, 11, 2)
        with self.assertRaises(PermissionError):
            self.booker.cancel("jo", booking)

    def test_cancel_unknown_booking_raises(self):
        with self.assertRaises(KeyError):
            self.booker.cancel("ida", 404)

    def test_cancel_frees_the_slot(self):
        booking = self.booker.book("ida", "aurora", "mon", 9, 11, 2)
        self.booker.cancel("ida", booking)
        self.assertEqual(self.booker.book("jo", "aurora", "mon", 9, 11, 2), 2)
        self.assertEqual([r["booking_id"] for r in
                          self.booker.schedule("aurora", "mon")], [2])

    # --- views ------------------------------------------------------------
    def test_schedule_sorted_with_exact_keys(self):
        self.booker.book("ida", "aurora", "mon", 13, 14, 3)
        self.booker.book("jo", "aurora", "mon", 9, 10, 1)
        rows = self.booker.schedule("aurora", "mon")
        self.assertEqual([r["start"] for r in rows], [9, 13])
        self.assertEqual(set(rows[0]),
                         {"booking_id", "user", "start", "end", "attendees"})
        self.assertEqual(rows[0]["user"], "jo")

    def test_notifications_in_delivery_order(self):
        first = self.booker.book("ida", "aurora", "mon", 9, 10, 2)
        second = self.booker.book("ida", "borealis", "mon", 9, 10, 2)
        self.booker.cancel("ida", first)
        self.assertEqual(self.booker.notifications("ida"),
                         [f"booked:{first}", f"booked:{second}",
                          f"cancelled:{first}"])
        self.assertEqual(self.booker.notifications("nobody"), [])

    def test_utilization_and_busiest_room(self):
        self.assertEqual(self.booker.utilization("aurora", "mon"), 0.0)
        self.assertIsNone(self.booker.busiest_room("mon"))
        self.booker.book("ida", "aurora", "mon", 9, 11, 2)
        self.booker.book("jo", "borealis", "mon", 9, 11, 2)
        self.assertEqual(self.booker.utilization("aurora", "mon"), 0.25)
        # equal hours -> alphabetical tie-break
        self.assertEqual(self.booker.busiest_room("mon"), "aurora")
        self.booker.book("jo", "borealis", "mon", 11, 15, 2)
        self.assertEqual(self.booker.busiest_room("mon"), "borealis")
        with self.assertRaises(KeyError):
            self.booker.utilization("nowhere", "mon")


if __name__ == "__main__":
    unittest.main()
