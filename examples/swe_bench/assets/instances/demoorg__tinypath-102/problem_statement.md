# normalize() lets absolute paths escape the root

Reported against `tinypath` (demo instance repo).

```python
>>> from tinypath import normalize
>>> normalize("/a/../../b")
'/../b'
>>> normalize("/../x")
'/../x'
```

There is nothing above `/`. On an absolute path, a `..` segment that would
pop past the root must be discarded, so the two calls above should return
`'/b'` and `'/x'`.

Relative paths are different and must not change: `normalize("../a/b")`
still has to return `'../a/b'`, because the leading `..` there is meaningful.
