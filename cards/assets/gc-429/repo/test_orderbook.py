"""Sealed acceptance suite for the orderbook module. Do not modify."""
import unittest

import orderbook as ob


def build_two_sided():
    book = ob.new_book()
    ob.place(book, "bid", 99, 5, "b1")
    ob.place(book, "bid", 101, 3, "b2")
    ob.place(book, "bid", 100, 4, "b3")
    ob.place(book, "ask", 103, 6, "a1")
    ob.place(book, "ask", 102, 2, "a2")
    ob.place(book, "ask", 104, 1, "a3")
    return book


class TestPlacement(unittest.TestCase):
    def test_seq_numbers_are_sequential(self):
        book = ob.new_book()
        s0 = ob.place(book, "bid", 10, 1, "x0")
        s1 = ob.place(book, "ask", 20, 1, "x1")
        s2 = ob.place(book, "bid", 11, 1, "x2")
        self.assertEqual([s0, s1, s2], [0, 1, 2])

    def test_best_bid_is_highest_price(self):
        book = build_two_sided()
        self.assertEqual(ob.best_bid(book), 101)

    def test_best_ask_is_lowest_price(self):
        book = build_two_sided()
        self.assertEqual(ob.best_ask(book), 102)

    def test_bid_ladder_sorted_high_first(self):
        book = build_two_sided()
        self.assertEqual([o["price"] for o in book["bids"]], [101, 100, 99])

    def test_fifo_within_same_price(self):
        book = ob.new_book()
        ob.place(book, "bid", 50, 1, "first")
        ob.place(book, "bid", 50, 1, "second")
        self.assertEqual([o["id"] for o in book["bids"]], ["first", "second"])

    def test_validation_errors(self):
        book = ob.new_book()
        with self.assertRaises(ValueError):
            ob.place(book, "buy", 10, 1, "z1")
        with self.assertRaises(ValueError):
            ob.place(book, "bid", 0, 1, "z2")
        with self.assertRaises(ValueError):
            ob.place(book, "bid", 10, -1, "z3")
        ob.place(book, "bid", 10, 1, "dup")
        with self.assertRaises(ValueError):
            ob.place(book, "ask", 11, 1, "dup")


class TestCancel(unittest.TestCase):
    def test_cancel_removes_only_target(self):
        book = build_two_sided()
        self.assertTrue(ob.cancel(book, "b2"))
        self.assertNotIn("b2", [o["id"] for o in book["bids"]])
        self.assertEqual(len(book["bids"]), 2)
        self.assertEqual(ob.best_bid(book), 100)
        self.assertEqual(len(book["asks"]), 3)

    def test_cancel_missing_returns_false(self):
        book = build_two_sided()
        self.assertFalse(ob.cancel(book, "ghost"))
        self.assertEqual(len(book["bids"]) + len(book["asks"]), 6)


class TestMatching(unittest.TestCase):
    def test_no_match_when_not_crossed(self):
        book = build_two_sided()
        self.assertIsNone(ob.match_once(book))

    def test_trade_at_resting_ask_price(self):
        book = ob.new_book()
        ob.place(book, "ask", 100, 5, "a1")
        ob.place(book, "bid", 103, 2, "b1")
        trade = ob.match_once(book)
        self.assertEqual(trade["price"], 100)
        self.assertEqual(trade["qty"], 2)
        self.assertEqual(trade["bid_id"], "b1")
        self.assertEqual(trade["ask_id"], "a1")

    def test_partial_fill_leaves_remainder(self):
        book = ob.new_book()
        ob.place(book, "ask", 100, 5, "a1")
        ob.place(book, "bid", 101, 2, "b1")
        ob.match_once(book)
        self.assertEqual(book["bids"], [])
        self.assertEqual(book["asks"][0]["qty"], 3)

    def test_match_all_records_trades(self):
        book = ob.new_book()
        ob.place(book, "ask", 100, 2, "a1")
        ob.place(book, "ask", 101, 2, "a2")
        ob.place(book, "bid", 101, 3, "b1")
        n = ob.match_all(book)
        self.assertEqual(n, 2)
        self.assertEqual(len(book["trades"]), 2)
        self.assertEqual([t["qty"] for t in book["trades"]], [2, 1])
        self.assertEqual([t["price"] for t in book["trades"]], [100, 101])

    def test_match_at_equal_price_crosses(self):
        book = ob.new_book()
        ob.place(book, "ask", 100, 1, "a1")
        ob.place(book, "bid", 100, 1, "b1")
        trade = ob.match_once(book)
        self.assertIsNotNone(trade)
        self.assertEqual(trade["price"], 100)


class TestAnalytics(unittest.TestCase):
    def test_spread_and_midpoint(self):
        book = build_two_sided()
        self.assertEqual(ob.spread(book), 1)
        self.assertEqual(ob.midpoint(book), 101.5)
        self.assertIsNone(ob.spread(ob.new_book()))
        self.assertIsNone(ob.midpoint(ob.new_book()))

    def test_depth_aggregates_same_price(self):
        book = ob.new_book()
        ob.place(book, "ask", 100, 2, "a1")
        ob.place(book, "ask", 100, 3, "a2")
        ob.place(book, "ask", 101, 4, "a3")
        self.assertEqual(ob.depth(book, "ask", 2), [(100, 5), (101, 4)])

    def test_depth_respects_level_limit(self):
        book = build_two_sided()
        self.assertEqual(ob.depth(book, "bid", 2), [(101, 3), (100, 4)])
        with self.assertRaises(ValueError):
            ob.depth(book, "mid", 1)

    def test_vwap(self):
        book = ob.new_book()
        ob.place(book, "ask", 100, 2, "a1")
        ob.place(book, "ask", 104, 2, "a2")
        ob.place(book, "bid", 104, 4, "b1")
        ob.match_all(book)
        self.assertEqual(ob.vwap(book["trades"]), 102.0)
        self.assertIsNone(ob.vwap([]))

    def test_exposure(self):
        book = build_two_sided()
        self.assertEqual(ob.exposure(book), 12 - 9)
        self.assertEqual(ob.exposure(ob.new_book()), 0)


if __name__ == "__main__":
    unittest.main()
