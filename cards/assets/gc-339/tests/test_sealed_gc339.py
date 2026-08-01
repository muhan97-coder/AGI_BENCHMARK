# Sealed acceptance tests for gc-339 (tabulate: SEPARATING_LINE support).
# Do not edit: the grader overwrites the copy in the workspace with this file.


def test_separating_line_importable():
    from tabulate import SEPARATING_LINE  # noqa: F401


def test_separating_line_simple_format():
    from tabulate import tabulate, SEPARATING_LINE

    table = [["spam", 41], SEPARATING_LINE, ["eggs", 42]]
    expected = "----  --\nspam  41\n----  --\neggs  42\n----  --"
    assert tabulate(table, tablefmt="simple") == expected


def test_separating_line_simple_format_with_headers():
    from tabulate import tabulate, SEPARATING_LINE

    table = [["spam", 41], SEPARATING_LINE, ["eggs", 42]]
    expected = (
        "item      qty\n------  -----\nspam       41\n------  -----\neggs       42"
    )
    assert tabulate(table, headers=["item", "qty"], tablefmt="simple") == expected


def test_separating_line_plain_format():
    from tabulate import tabulate, SEPARATING_LINE

    table = [["spam", 41], SEPARATING_LINE, ["eggs", 42]]
    assert tabulate(table, tablefmt="plain") == "spam  41\n\neggs  42"


def test_tables_without_separator_unchanged():
    from tabulate import tabulate

    table = [["spam", 41], ["eggs", 42]]
    assert tabulate(table, tablefmt="simple") == (
        "----  --\nspam  41\neggs  42\n----  --"
    )
    assert tabulate(table, headers=["item", "qty"], tablefmt="github") == (
        "| item   |   qty |\n|--------|-------|\n| spam   |    41 |\n| eggs   |    42 |"
    )
