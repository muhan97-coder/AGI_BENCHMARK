# slugmini 0.3.1

A miniature slug builder. This is a **demo package invented for
`examples/oss_repair/`** -- it is not published anywhere and it stands in for
the real, network-cloned upstream project that the scored `oss_repair` cards
pin at a git SHA.

```python
>>> from slugmini import slugify
>>> slugify("Creme Brulee, 2024!")
'creme-brulee-2024'
>>> slugify("hello world", separator="_")
'hello_world'
```

The snapshot in this directory is the pinned base state: treat it as
read-only upstream code, copy it into the workspace, and repair the copy.
