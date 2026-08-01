# Mile conversions are off by ~0.02%

Reported against `tinyunits` (demo instance repo).

```python
>>> from tinyunits import convert
>>> convert(1, "mi", "km")
1.609
>>> convert(1, "mi", "ft")
5278.871391076116
```

The international mile is exactly 1609.344 m, so those should be
`1.609344` and `5280.0`. Our survey exports are drifting by about 20 cm per
kilometre because of this.

Everything else in the module -- the metric conversions, the inch/foot
relation, the round trips, the error for an unknown unit, `parse_quantity()`
-- is correct today and must stay correct.
