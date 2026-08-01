# kvlog — crash-tolerant append-only key-value store CLI (spec v1)

Implement a command-line tool at `workspace/gc-407/kvlog.py` (relative to the
benchmark repo root). Standard library only. Invocation:

    python3 workspace/gc-407/kvlog.py DBFILE COMMAND [ARGS...]

`DBFILE` is a path to the store's single log file. Every invocation prints
exactly ONE compact JSON line to stdout and exits with the code given below.

## Log file format (normative — tests inspect raw bytes)
UTF-8 text. One record per line, LF (`\n`) terminated:

    S<TAB>KEY<TAB>VALUE     a set record
    D<TAB>KEY               a delete record (tombstone)

The current value of a key is decided by the LAST record for that key
(last-writer-wins). A key whose last record is a `D` tombstone is absent.
A missing DBFILE and an empty DBFILE both mean an empty store.

- KEY: 1+ chars matching `[A-Za-z0-9_.-]` only.
- VALUE: any string (may be empty, may contain spaces and non-ASCII) except
  it must not contain TAB, LF, or CR.

## Commands
- `set KEY VALUE` — append an `S` record. Output `{"ok": true}`, exit 0.
- `get KEY` — output `{"key": KEY, "value": VALUE}`, exit 0; if absent,
  output `{"error": "notfound"}`, exit 3.
- `del KEY` — if the key is present, append a `D` tombstone and output
  `{"ok": true}`, exit 0. If ABSENT: output `{"error": "notfound"}`, exit 3,
  and append NOTHING (the file's bytes must be unchanged).
- `keys` — output `{"keys": [...]}` (present keys, sorted ascending), exit 0.
- `stats` — output `{"records": R, "live": L, "dead": D}` where R = number of
  COMPLETE records in the log, L = number of present keys, D = R - L. Exit 0.
- `compact` — rewrite DBFILE so it contains exactly one `S` record per
  present key, sorted by key ascending, each LF-terminated; tombstones,
  overwritten records, and any torn tail (below) are discarded. Output
  `{"ok": true, "live": L, "dropped": X}` where X = R_before - L. Exit 0.
  Compacting a missing DBFILE creates it empty (live 0, dropped 0).

## Deliberately tricky edge cases (all tested — read carefully)
1. **Torn tail vs. corruption.** A crash can leave a PARTIAL final line: the
   file does not end with `\n`. Every command must IGNORE the torn tail (it
   is not a record, it never contributes to reads, `records`, or `dropped`).
   `set` and `del` must first TRUNCATE the torn tail, then append, so the
   log never contains a merged/garbled line. `compact` also discards it.
2. **Interior corruption is fatal.** Any COMPLETE line (i.e. `\n`-terminated)
   that is not a valid `S`/`D` record (wrong field count, empty, bad opcode,
   invalid KEY) makes the whole store corrupt: EVERY command must output
   `{"error": "corrupt", "line": N}` (N = 1-based index of the first bad
   complete line) and exit 4, writing nothing.
3. **del-then-set revives.** `set` after `del` makes the key present again
   with the new value. `del` on a key whose last record is already a
   tombstone is a `notfound` and appends nothing.
4. **Empty value is a real value.** `set k ""` stores the empty string;
   `get k` returns `{"key": "k", "value": ""}`, and the record line is
   `S<TAB>k<TAB>` followed by LF.
5. **Usage errors never touch the file.** Unknown command, wrong argument
   count, invalid KEY, or a VALUE containing TAB/LF/CR: output
   `{"error": "usage"}`, exit 2, file bytes unchanged. Usage errors are
   checked BEFORE the corruption check.

## Exit codes
0 success · 2 usage · 3 notfound · 4 corrupt.

## Acceptance
Sealed suite: `assets/gc-407/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
