# Sealed acceptance tests for ex-oss_repair (slugmini: stopwords option).
# Do not edit: the grader re-copies this file over the workspace before running,
# so edits here cannot turn the run green.


def test_stopwords_are_dropped():
    from slugmini import slugify

    assert slugify("The Quick Brown Fox", stopwords=["the"]) == "quick-brown-fox"


def test_stopwords_match_case_insensitively():
    from slugmini import slugify

    assert slugify("A Tale Of Two Cities", stopwords=["Of", "A"]) == "tale-two-cities"


def test_dropping_a_middle_word_leaves_no_separator_run():
    from slugmini import slugify

    assert (
        slugify("news and the world and back", stopwords=["and", "the"])
        == "news-world-back"
    )


def test_stopwords_that_would_empty_the_slug_are_ignored():
    from slugmini import slugify

    # Dropping every word would yield an empty slug, which is never useful:
    # fall back to the unfiltered slug instead.
    assert slugify("The The", stopwords=["the"]) == "the-the"


def test_default_behaviour_is_unchanged():
    from slugmini import slugify

    assert slugify("Crème Brûlée, 2024!") == "creme-brulee-2024"
    assert slugify("hello world", separator="_") == "hello_world"
    assert slugify("") == ""
