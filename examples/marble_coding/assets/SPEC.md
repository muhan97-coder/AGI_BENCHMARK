# ex-marble_coding — interface contract: `MeetingRoomBooker`

A MARBLE-flavoured single-file coding task, sized down to one class. Implement
`workspace/solution.py` (relative to the workspace root) exposing exactly this
API. The sealed suite `assets/test_accept.py` is the only grader; it loads your
file by path, so the module needs no packaging and imports nothing outside the
standard library.

Days are opaque strings (`"mon"`, `"2030-01-07"`, …); hours are integers on a
0–24 clock. A booking occupies the half-open interval `[start, end)`, so
`(9, 11)` and `(11, 12)` do **not** collide.

## `class MeetingRoomBooker()`

- `add_room(name: str, capacity: int) -> None`
  - duplicate `name` raises `ValueError`; `capacity < 1` raises `ValueError`.

- `book(user: str, room: str, day: str, start: int, end: int, attendees: int) -> int`
  - unknown `room` raises `KeyError`;
  - `end <= start` raises `ValueError`;
  - `start < 0` or `end > 24` raises `ValueError`;
  - `attendees < 1` or `attendees > capacity` raises `ValueError`;
  - an overlap with an active booking of the same room **and** day raises
    `ValueError`; touching endpoints are legal;
  - returns integer booking ids starting at 1 and incrementing by 1. **A
    rejected attempt must not consume an id.**
  - on success appends `"booked:<id>"` to `user`'s notifications.

- `cancel(user: str, booking_id: int) -> None`
  - unknown `booking_id` raises `KeyError`;
  - a non-owner raises `PermissionError`;
  - appends `"cancelled:<id>"` to `user`'s notifications;
  - the freed interval becomes bookable again.

- `schedule(room: str, day: str) -> list[dict]`
  - unknown `room` raises `KeyError`;
  - active bookings for that room/day, sorted by `start` ascending, each a dict
    with exactly the keys `booking_id, user, start, end, attendees`.

- `notifications(user: str) -> list[str]`
  - in delivery order; `[]` for a user who has never been notified.

- `utilization(room: str, day: str) -> float`
  - booked hours divided by an 8-hour working day, rounded to 4 decimals;
    `0.0` when nothing is booked. Unknown `room` raises `KeyError`.

- `busiest_room(day: str) -> str | None`
  - the room with the most booked hours on `day`; ties broken alphabetically;
    `None` when nothing is booked that day.

## Grading

```
python3 assets/run_accept.py      # metric: tests_passed, regex ^(\d+) passed, need 14
```

`run_accept.py` is sealed. It prints a pytest-style summary line; the card
extracts the count from it with `^(\d+) passed`. When any test fails the line
reads `N failed, M passed` (or `N failed`), which that regex does **not**
match at position 0 of a line — so a partially working solution grades as
`EXTRACT_FAIL`, not as partial credit. That is deliberate and is exactly how
the scored MARBLE cards behave.
