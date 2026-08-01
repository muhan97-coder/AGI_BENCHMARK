# gc-332 Interface Contract — CollaborativeStoryBuilder (MARBLE coding task_id=42)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=42, at
commit `8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-332/solution.py`. The module must define a
`ConflictError(Exception)` class in addition to `StoryBuilder`.

## class StoryBuilder()

- `register(user) -> None` — duplicate raises `ValueError`.
- `create_story(owner, title) -> int` — ids start at 1; unknown owner raises
  `KeyError`. The owner is a contributor. New stories are at version 0 with no
  chapters.
- `invite(caller, story_id, user) -> None` — only the owner may invite, otherwise
  `PermissionError`; unknown story/user raises `KeyError`.
- `add_chapter(user, story_id, title, text) -> int` — contributors only, otherwise
  `PermissionError`. Returns the 0-based chapter index. Bumps the version by 1.
  If `user` is not the owner, the owner receives `"chapter_added:<story_id>:<user>"`.
- `edit_chapter(user, story_id, chapter_index, new_text, base_version) -> None`
  - Contributors only (`PermissionError`); bad index raises `IndexError`.
  - If `base_version != current_version(story_id)` raise `ConflictError` and change
    nothing (optimistic concurrency). Otherwise apply and bump version by 1.
- `current_version(story_id) -> int` — 0 after creation, +1 per add/edit/revert.
- `content(story_id) -> list[dict]` — `{"title", "text"}` per chapter, in order.
- `content_at(story_id, version) -> list[dict]` — the chapters exactly as they were
  at that version; unknown version raises `KeyError`.
- `history(story_id) -> list[dict]` — `{"version", "user", "action"}` per change,
  action in `{"add", "edit", "revert"}`, in order (version 1, 2, ...).
- `revert(user, story_id, version) -> None` — contributors only; restores
  `content_at(version)` as a new change with action `"revert"` (version bumps by 1).
- `publish(caller, story_id) -> None` — owner only (`PermissionError`). After
  publishing, `add_chapter`/`edit_chapter`/`revert` raise `RuntimeError`.
- `gallery() -> list` — `(story_id, title)` pairs of published stories, ordered by
  story id.
- `rate(user, story_id, score) -> None` — registered users only (`KeyError`);
  unpublished story raises `RuntimeError`; score outside 1..5 raises `ValueError`;
  re-rating by the same user replaces the old score. Owner receives
  `"rating:<story_id>:<user>"` (raters other than the owner only).
- `average_rating(story_id) -> float` — raises `RuntimeError` when unrated.
- `comment(user, story_id, text) -> None` — published only (`RuntimeError`);
  owner receives `"comment:<story_id>:<user>"` unless the owner commented.
- `comments(story_id) -> list` — `(user, text)` in order.
- `notifications(user) -> list[str]` — delivery order; unknown user raises `KeyError`.
