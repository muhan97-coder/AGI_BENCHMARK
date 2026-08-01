# format_duration(0) returns an empty string

Reported against `tinydate` (demo instance repo).

```python
>>> from tinydate import format_duration
>>> format_duration(0)
''
>>> format_duration(0.4)
''
```

An empty string is not a duration. A zero (or sub-second) duration should
render as `'0s'` -- that is what every caller assumes when it concatenates
the result into a log line.

Non-zero durations already render correctly (`3600 -> '1h'`,
`5400 -> '1h 30m'`, `61 -> '1m 1s'`) and must not change, and a negative
input must keep raising `ValueError`.
