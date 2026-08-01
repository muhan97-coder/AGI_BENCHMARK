"""Sealed acceptance suite for gc-332 (MARBLE coding task_id=42: CollaborativeStoryBuilder).

Loads the agent's solution from workspace/gc-332/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-332" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc332", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def mod():
    return _load()


@pytest.fixture()
def sb(mod):
    s = mod.StoryBuilder()
    for u in ("owner", "coauthor", "reader"):
        s.register(u)
    return s


@pytest.fixture()
def story(sb):
    sid = sb.create_story("owner", "The Long Voyage")
    sb.invite("owner", sid, "coauthor")
    return sid


def test_register_and_create_validation(sb):
    with pytest.raises(ValueError):
        sb.register("owner")
    with pytest.raises(KeyError):
        sb.create_story("ghost", "x")
    assert sb.create_story("owner", "a") == 1
    assert sb.create_story("owner", "b") == 2


def test_invite_owner_only(sb, story):
    with pytest.raises(PermissionError):
        sb.invite("coauthor", story, "reader")
    with pytest.raises(KeyError):
        sb.invite("owner", story, "ghost")


def test_add_chapter_permissions_and_index(sb, story):
    assert sb.add_chapter("owner", story, "ch1", "Once") == 0
    assert sb.add_chapter("coauthor", story, "ch2", "upon") == 1
    with pytest.raises(PermissionError):
        sb.add_chapter("reader", story, "ch3", "nope")


def test_add_chapter_notifies_owner(sb, story):
    sb.add_chapter("coauthor", story, "ch1", "text")
    assert sb.notifications("owner") == [f"chapter_added:{story}:coauthor"]
    sb.add_chapter("owner", story, "ch2", "text")
    assert len(sb.notifications("owner")) == 1  # own action not notified


def test_versioning_increments(sb, story):
    assert sb.current_version(story) == 0
    sb.add_chapter("owner", story, "ch1", "v1")
    assert sb.current_version(story) == 1
    sb.edit_chapter("owner", story, 0, "v2", base_version=1)
    assert sb.current_version(story) == 2


def test_edit_conflict_detection(mod, sb, story):
    sb.add_chapter("owner", story, "ch1", "base")
    v = sb.current_version(story)
    sb.edit_chapter("owner", story, 0, "owner edit", base_version=v)
    with pytest.raises(mod.ConflictError):
        sb.edit_chapter("coauthor", story, 0, "stale edit", base_version=v)
    assert sb.content(story)[0]["text"] == "owner edit"


def test_edit_bad_index(sb, story):
    sb.add_chapter("owner", story, "ch1", "x")
    with pytest.raises(IndexError):
        sb.edit_chapter("owner", story, 5, "y", base_version=1)


def test_content_at_versions(sb, story):
    sb.add_chapter("owner", story, "ch1", "alpha")
    sb.edit_chapter("owner", story, 0, "beta", base_version=1)
    assert sb.content_at(story, 1)[0]["text"] == "alpha"
    assert sb.content_at(story, 2)[0]["text"] == "beta"
    assert sb.content_at(story, 0) == []
    with pytest.raises(KeyError):
        sb.content_at(story, 99)


def test_history_records_identity(sb, story):
    sb.add_chapter("owner", story, "ch1", "alpha")
    sb.edit_chapter("coauthor", story, 0, "beta", base_version=1)
    sb.revert("owner", story, 1)
    h = [(e["version"], e["user"], e["action"]) for e in sb.history(story)]
    assert h == [(1, "owner", "add"), (2, "coauthor", "edit"), (3, "owner", "revert")]


def test_revert_restores_content(sb, story):
    sb.add_chapter("owner", story, "ch1", "alpha")
    sb.edit_chapter("owner", story, 0, "beta", base_version=1)
    sb.revert("owner", story, 1)
    assert sb.content(story)[0]["text"] == "alpha"
    assert sb.current_version(story) == 3
    # revert is itself versioned: content at v2 still beta
    assert sb.content_at(story, 2)[0]["text"] == "beta"


def test_publish_freezes_story(sb, story):
    sb.add_chapter("owner", story, "ch1", "alpha")
    with pytest.raises(PermissionError):
        sb.publish("coauthor", story)
    sb.publish("owner", story)
    with pytest.raises(RuntimeError):
        sb.add_chapter("owner", story, "ch2", "more")
    with pytest.raises(RuntimeError):
        sb.edit_chapter("owner", story, 0, "z", base_version=sb.current_version(story))
    with pytest.raises(RuntimeError):
        sb.revert("owner", story, 1)


def test_gallery_lists_published_only(sb):
    s1 = sb.create_story("owner", "First")
    s2 = sb.create_story("owner", "Second")
    sb.add_chapter("owner", s2, "ch", "x")
    sb.publish("owner", s2)
    assert [tuple(g) for g in sb.gallery()] == [(s2, "Second")]
    sb.add_chapter("owner", s1, "ch", "y")
    sb.publish("owner", s1)
    assert [tuple(g) for g in sb.gallery()] == [(s1, "First"), (s2, "Second")]


def test_rating_rules(sb, story):
    sb.add_chapter("owner", story, "ch1", "x")
    with pytest.raises(RuntimeError):
        sb.rate("reader", story, 5)
    sb.publish("owner", story)
    with pytest.raises(ValueError):
        sb.rate("reader", story, 0)
    with pytest.raises(ValueError):
        sb.rate("reader", story, 6)
    with pytest.raises(KeyError):
        sb.rate("ghost", story, 3)
    sb.rate("reader", story, 5)
    sb.rate("coauthor", story, 2)
    assert abs(sb.average_rating(story) - 3.5) < 1e-9
    sb.rate("reader", story, 3)  # replaces
    assert abs(sb.average_rating(story) - 2.5) < 1e-9


def test_average_rating_unrated(sb, story):
    sb.add_chapter("owner", story, "ch1", "x")
    sb.publish("owner", story)
    with pytest.raises(RuntimeError):
        sb.average_rating(story)


def test_comments_and_owner_notifications(sb, story):
    sb.add_chapter("owner", story, "ch1", "x")
    with pytest.raises(RuntimeError):
        sb.comment("reader", story, "too early")
    sb.publish("owner", story)
    sb.comment("reader", story, "loved it")
    sb.comment("owner", story, "thanks")
    assert [list(c) for c in sb.comments(story)] == [
        ["reader", "loved it"], ["owner", "thanks"]]
    notes = sb.notifications("owner")
    assert f"comment:{story}:reader" in notes
    assert f"comment:{story}:owner" not in notes


def test_rating_notification(sb, story):
    sb.add_chapter("owner", story, "ch1", "x")
    sb.publish("owner", story)
    sb.rate("reader", story, 4)
    assert f"rating:{story}:reader" in sb.notifications("owner")


def test_notifications_unknown_user(sb):
    with pytest.raises(KeyError):
        sb.notifications("ghost")
