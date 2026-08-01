# percent_change() crashes on a zero baseline

Reported against `tinycalc` (demo instance repo).

```python
>>> from tinycalc import percent_change
>>> percent_change(0, 5)
Traceback (most recent call last):
  ...
ZeroDivisionError: float division by zero
```

Percent change from a baseline of zero is undefined, and the rest of this
package reports "undefined" as `None` -- `mean([])` already returns `None`
rather than raising. `percent_change()` should do the same: return `None`
when `old == 0`, for any `new`.

All existing behaviour (increases, decreases, negative baselines) must stay
exactly as it is.
