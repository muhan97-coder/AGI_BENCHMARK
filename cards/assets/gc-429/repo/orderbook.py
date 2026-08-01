"""Deterministic in-memory limit order book (teaching-scale).

Prices are integer ticks, quantities positive integers. Bids sort
high-price-first, asks sort low-price-first; ties keep time priority (FIFO).
Matching crosses the book one trade at a time at the resting ask price.
"""


def new_book():
    return {"bids": [], "asks": [], "trades": [], "next_seq": 0}


def _insert(levels, order, descending):
    i = 0
    while i < len(levels):
        p = levels[i]["price"]
        if (p < order["price"]) if descending else (p > order["price"]):
            break
        i += 1
    levels.insert(i, order)


def place(book, side, price, qty, oid):
    """Insert a resting order; returns its sequence number."""
    if side not in ("bid", "ask"):
        raise ValueError("side must be 'bid' or 'ask'")
    if price <= 0 or qty <= 0:
        raise ValueError("price and qty must be positive")
    if any(o["id"] == oid for o in book["bids"] + book["asks"]):
        raise ValueError("duplicate order id")
    order = {"id": oid, "price": price, "qty": qty, "seq": book["next_seq"]}
    book["next_seq"] += 1
    if side == "bid":
        _insert(book["bids"], order, descending=True)
    else:
        _insert(book["asks"], order, descending=False)
    return order["seq"]


def cancel(book, oid):
    """Remove a resting order by id; True if found."""
    for levels in (book["bids"], book["asks"]):
        for i, o in enumerate(levels):
            if o["id"] == oid:
                del levels[i]
                return True
    return False


def best_bid(book):
    return book["bids"][0]["price"] if book["bids"] else None


def best_ask(book):
    return book["asks"][0]["price"] if book["asks"] else None


def spread(book):
    b, a = best_bid(book), best_ask(book)
    if b is None or a is None:
        return None
    return a - b


def midpoint(book):
    b, a = best_bid(book), best_ask(book)
    if b is None or a is None:
        return None
    return (a + b) / 2


def match_once(book):
    """Cross the book once; returns the trade dict or None."""
    b, a = best_bid(book), best_ask(book)
    if b is None or a is None or b < a:
        return None
    bid, ask = book["bids"][0], book["asks"][0]
    qty = min(bid["qty"], ask["qty"])
    trade = {"price": ask["price"], "qty": qty,
             "bid_id": bid["id"], "ask_id": ask["id"]}
    bid["qty"] -= qty
    ask["qty"] -= qty
    if bid["qty"] == 0:
        book["bids"].pop(0)
    if ask["qty"] == 0:
        book["asks"].pop(0)
    book["trades"].append(trade)
    return trade


def match_all(book):
    """Cross until the book no longer crosses; returns trade count."""
    n = 0
    while match_once(book) is not None:
        n += 1
    return n


def depth(book, side, levels_n):
    """Aggregate resting qty per price for the top levels_n price levels."""
    if side == "bid":
        levels = book["bids"]
    elif side == "ask":
        levels = book["asks"]
    else:
        raise ValueError("side must be 'bid' or 'ask'")
    rows = []
    for o in levels:
        if rows and rows[-1][0] == o["price"]:
            rows[-1][1] += o["qty"]
        else:
            if len(rows) == levels_n:
                break
            rows.append([o["price"], o["qty"]])
    return [tuple(r) for r in rows]


def vwap(trades):
    """Volume-weighted average price of a trade list, or None if empty."""
    total_qty = sum(t["qty"] for t in trades)
    if total_qty == 0:
        return None
    return sum(t["price"] * t["qty"] for t in trades) / total_qty


def exposure(book):
    """Net resting quantity: total bid qty minus total ask qty."""
    return sum(o["qty"] for o in book["bids"]) - sum(o["qty"] for o in book["asks"])
