# Sealed acceptance tests for gc-337 (xmltodict: XML comment capture).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import xmltodict


def test_process_comments_captures_comment():
    d = xmltodict.parse("<a><!-- hi there --><b>1</b></a>", process_comments=True)
    assert d["a"]["#comment"] == "hi there"
    assert d["a"]["b"] == "1"


def test_comments_ignored_by_default():
    d = xmltodict.parse("<a><!-- hi --><b>1</b></a>")
    assert d["a"] == {"b": "1"}


def test_process_comments_false_matches_default():
    d = xmltodict.parse("<a><!-- hi --><b>1</b></a>", process_comments=False)
    assert d["a"] == {"b": "1"}


def test_nested_comment():
    d = xmltodict.parse(
        "<r><child><!-- note --><x>2</x></child></r>", process_comments=True
    )
    assert d["r"]["child"]["#comment"] == "note"
    assert d["r"]["child"]["x"] == "2"


def test_roundtrip_without_comments_still_works():
    d = xmltodict.parse("<a><b>1</b><b>2</b></a>")
    assert d["a"]["b"] == ["1", "2"]
    assert xmltodict.unparse(d, full_document=False) == "<a><b>1</b><b>2</b></a>"
