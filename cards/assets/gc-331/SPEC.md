# gc-331 Interface Contract — DataFlowCoordinator (MARBLE coding task_id=87)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=87, at
commit `8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-331/solution.py`. The pipeline enforces strict stage order:
ingest -> validate -> transform -> export. Calling a stage before its predecessor has
completed raises `RuntimeError`.

## class DataFlowCoordinator()

- `ingest_csv(text) -> int` — parses a CSV string (first line = header, comma
  separated, no quoting needed). Returns the number of data rows. Empty text or
  header-only input raises `ValueError`. Re-ingesting replaces all data and resets
  the validated/transformed/exported flags.
- `stage_status() -> dict` — `{"ingested": bool, "validated": bool,
  "transformed": bool, "exported": bool}`.
- `validate(schema, required) -> dict`
  - `schema`: dict column -> `"int" | "float" | "str"`; `required`: list of columns.
  - Raises `RuntimeError` if nothing ingested. Raises `ValueError` if any `required`
    column is missing from the header.
  - A row is invalid if a required column is the empty string (reason `"missing"`)
    or a schema-typed cell fails conversion (reason `"type"`; `"str"` never fails;
    empty non-required cells are not type-checked).
  - Valid rows are kept with schema casts applied; invalid rows are quarantined.
  - Returns `{"valid": n, "invalid": m}`.
- `errors() -> list` — one `(row_index, column, reason)` triple per failing cell of
  every quarantined row; `row_index` is 0-based over the ingested data rows; ordered
  by row_index asc, then column position in the header.
- Transform operations (each raises `RuntimeError` unless validation has run; each
  marks the pipeline transformed):
  - `rename(old, new)` — unknown column raises `KeyError`.
  - `drop_column(col)` — unknown column raises `KeyError`.
  - `drop_duplicates()` — removes later exact-duplicate rows.
  - `merge(new_col, cols, sep)` — appends `new_col` built by joining `str(value)` of
    `cols` with `sep`; unknown source column raises `KeyError`; originals kept.
- `export_rows() -> list[dict]` — raises `RuntimeError` unless at least one transform
  ran. Returns deep copies (mutating the result must not affect the pipeline).
  Marks exported.
- `export_csv() -> str` — same gating. Header line with current columns in order
  (renames/merges reflected), then one line per row with `str(value)` cells, lines
  joined by `"\n"` with no trailing newline.
