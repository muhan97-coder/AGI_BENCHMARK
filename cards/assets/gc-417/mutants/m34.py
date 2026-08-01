"""tblops: tiny TSV table utilities (pure stdlib). Sealed mutation target."""


def parse_tsv(text):
    """Parse TSV text into a list of rows (lists of strings). Final newline ignored."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [line.split("\t") for line in lines]


def format_tsv(rows):
    """Inverse of parse_tsv: newline-terminated TSV text; '' for no rows."""
    if not rows:
        return ""
    return "\n".join("\t".join(row) for row in rows) + "\n"


def sort_rows(rows, col, numeric=False, reverse=False):
    """Stable sort by column col; numeric=True compares int(cell)."""
    if numeric:
        return sorted(rows, key=lambda r: int(r[col]), reverse=reverse)
    return sorted(rows, key=lambda r: r[col], reverse=reverse)


def unique_rows(rows):
    """Rows with exact duplicates removed, keeping first occurrences."""
    seen = set()
    out = []
    for row in rows:
        key = tuple(row)
        if key not in seen:
            out.append(row)
    return out


def sum_column(rows, col):
    """Sum of int(cell) over column col; 0 for no rows."""
    return sum(int(row[col]) for row in rows)


def max_column(rows, col):
    """Max of int(cell) over column col; ValueError for no rows."""
    if not rows:
        raise ValueError("no rows")
    return max(int(row[col]) for row in rows)


def transpose(rows):
    """Transpose a rectangular table; ValueError if rows are ragged."""
    if not rows:
        return []
    width = len(rows[0])
    for row in rows:
        if len(row) != width:
            raise ValueError("ragged table")
    return [[row[i] for row in rows] for i in range(width)]


def filter_eq(rows, col, value):
    """Rows whose column col equals value exactly."""
    return [row for row in rows if row[col] == value]
