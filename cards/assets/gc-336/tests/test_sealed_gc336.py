# Sealed acceptance tests for gc-336 (python-slugify: user-defined replacements).
# Do not edit: the grader overwrites the copy in the workspace with this file.


def test_replacements_basic():
    from slugify import slugify

    assert (
        slugify("10 | 20 %", replacements=[["|", "or"], ["%", "percent"]])
        == "10-or-20-percent"
    )


def test_replacements_umlaut_mapping():
    from slugify import slugify

    assert (
        slugify("ÜBER Über German Umlaut", replacements=[["Ü", "UE"], ["ü", "ue"]])
        == "ueber-ueber-german-umlaut"
    )


def test_replacements_applied_before_transliteration():
    from slugify import slugify

    # Without the replacement, Ü transliterates to plain U.
    assert slugify("Über", replacements=[["Ü", "UE"]]) == "ueber"
    assert slugify("Über") == "uber"


def test_replacements_empty_list_is_noop():
    from slugify import slugify

    assert slugify("hello world", replacements=[]) == "hello-world"


def test_default_behavior_unchanged():
    from slugify import slugify

    assert slugify("This is a test ---") == "this-is-a-test"
    assert slugify("10 | 20 %") == "10-20"
