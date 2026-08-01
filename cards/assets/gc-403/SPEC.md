# calcfrac — exact rational expression evaluator (spec v1)

Implement a pure-Python module at `workspace/gc-403/calcfrac.py` (relative to
the benchmark repo root). Standard library only (`fractions` is allowed).

## Library API: `evaluate(expr: str) -> str`
Evaluates an infix arithmetic expression with EXACT rational arithmetic
(no floating point anywhere in the visible behavior).

### Tokens
- Integer literals: `\d+`
- Decimal literals: `\d+\.\d+`, converted EXACTLY (`0.1` is 1/10, so
  `0.1 + 0.2` is exactly `3/10`).
- Operators: `+  -  *  /  ^`, parentheses `(  )`.
- Unary `+` and `-`.
- Whitespace (spaces, tabs) may appear between any tokens and is ignored.
- Any other character is a syntax error.

### Grammar and precedence (loosest to tightest)
1. binary `+`, `-` (left-associative)
2. `*`, `/` (left-associative)
3. unary `+`, `-` (prefix, may repeat: `--3` is 3)
4. `^` (RIGHT-associative, binds tighter than unary minus:
   `-2^2` = `-(2^2)` = -4, while `(-2)^2` = 4)
5. atoms: literals and parenthesized expressions
The exponent itself may carry unary operators: `2^-2` is 1/4.

### `^` rules
- The exponent must evaluate to an INTEGER rational (denominator 1 after
  reduction); otherwise raise `ValueError` (e.g. `2^(1/2)`).
- Negative exponents take the reciprocal: `2^-2` = 1/4.
- `0^0` = 1. `0^k` for k > 0 is 0. `0^k` for k < 0 raises
  `ZeroDivisionError`.
- The base may be any rational: `(2/3)^2` = 4/9.

### Errors
- Division by zero (`1/0`, `1/(2-2)`, `0^-1`): raise `ZeroDivisionError`.
- Any syntax problem (empty input, dangling operator, unbalanced parens,
  adjacent literals like `1 2`, invalid characters, `.5`, `5.`):
  raise `ValueError`.

### Result format
Reduce to lowest terms. Denominator 1 -> plain integer string (`"7"`,
`"-3"`, `"0"`). Otherwise `"p/q"` with q > 0 and the sign on the numerator
(`"-1/3"`, never `"1/-3"`).

## CLI
    python3 workspace/gc-403/calcfrac.py "EXPR"
- Success: print `{"result": "<string from evaluate>"}` and exit 0.
- `ValueError` from a non-integer exponent: print `{"error": "domain"}`,
  exit 4.
- Other `ValueError` (syntax): print `{"error": "syntax"}`, exit 2.
- `ZeroDivisionError`: print `{"error": "division"}`, exit 3.
- Wrong number of arguments: print `{"error": "usage"}`, exit 5.
All output is a single compact JSON line on stdout.

Note: to distinguish the two ValueError cases in the CLI, `evaluate` must
raise the non-integer-exponent error with a message containing the word
`exponent`.

## Acceptance
Sealed suite: `assets/gc-403/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
