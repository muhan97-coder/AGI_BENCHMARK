# gc-328 Interface Contract — PriceTrackerCollaborator (MARBLE coding task_id=4)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=4, at commit
`8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-328/solution.py`. Timestamps are ints.

## class PriceTracker()

- `register(user) -> None` — duplicate raises `ValueError`.
- `add_product(user, name, url) -> int` — ids start at 1. `url` must start with
  `"http://"` or `"https://"` else `ValueError`. Unknown user raises `KeyError`.
- `set_alert(user, product_id, threshold) -> None` — `threshold <= 0` raises
  `ValueError`; unknown product raises `KeyError`. A user may hold several thresholds
  for the same product.
- `record_price(product_id, retailer, price, ts) -> None` — `price <= 0` raises
  `ValueError`; unknown product raises `KeyError`. Appends to that product's history.
  Then, for every user holding at least one alert on this product with
  `price < threshold`, deliver exactly one notification
  `"price_drop:<product_id>:<retailer>:<price>"` per user for this event (even if
  several of their thresholds match).
- `history(product_id, retailer) -> list` — `(ts, price)` pairs in insertion order.
- `latest_prices(product_id) -> dict` — `{retailer: price}` using each retailer's
  highest-`ts` entry (on equal ts, the later-recorded entry wins).
- `best_offer(product_id) -> tuple` — `(retailer, price)` with the lowest latest
  price; ties broken by alphabetical retailer. Raises `RuntimeError` when the product
  has no recorded prices.
- `trend(product_id) -> dict` — `{"min": .., "max": .., "avg": ..}` over the entire
  history (all retailers); avg is a float. Raises `RuntimeError` when empty.
- `good_buy(product_id) -> bool` — True iff the best current offer price is <= the
  historical average from `trend`.
- `create_group(name) -> None` (duplicate raises `ValueError`);
  `join_group(user, name) -> None` (unknown group/user raises `KeyError`).
- `share_alert(user, group, product_id) -> None` — `user` must belong to the group
  else `PermissionError`. Copies all of `user`'s thresholds on that product to every
  other group member (as their own alerts) and delivers
  `"shared_alert:<product_id>:<user>"` to every other member.
- `notifications(user) -> list[str]` — delivery order; unknown user raises `KeyError`.
