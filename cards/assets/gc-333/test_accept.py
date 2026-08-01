"""Sealed acceptance suite for gc-333 (MARBLE coding task_id=17: MultiAgentMaze).

Loads the agent's solution from workspace/gc-333/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-333" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc333", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MAZE_OPEN = [
    "S..#.",
    ".#.#.",
    ".#...",
    ".#.#.",
    "...#E",
]

MAZE_BLOCKED = [
    "S..#.",
    ".#.#.",
    ".#B..",
    ".#.#.",
    "...#E",
]


@pytest.fixture()
def mod():
    return _load()


def _game(mod, levels, roles=("pf", "bl", "sw")):
    g = mod.MazeGame(levels)
    names = {"pf": "pathfinder", "bl": "blocker", "sw": "swapper"}
    for r in roles:
        g.add_player(r, names[r])
    return g


def test_grid_validation_two_starts(mod):
    with pytest.raises(ValueError):
        mod.MazeGame([["SS", ".E"]])


def test_grid_validation_bad_char(mod):
    with pytest.raises(ValueError):
        mod.MazeGame([["SX", ".E"]])


def test_grid_validation_missing_exit_and_ragged(mod):
    with pytest.raises(ValueError):
        mod.MazeGame([["S.", ".."]])
    with pytest.raises(ValueError):
        mod.MazeGame([["S.E", ".."]])


def test_add_player_validation(mod):
    g = mod.MazeGame([MAZE_OPEN])
    g.add_player("a", "pathfinder")
    with pytest.raises(ValueError):
        g.add_player("a", "blocker")
    with pytest.raises(ValueError):
        g.add_player("b", "navigator")


def test_role_enforcement(mod):
    g = _game(mod, [MAZE_BLOCKED])
    with pytest.raises(PermissionError):
        g.move("bl", "right")
    with pytest.raises(PermissionError):
        g.push("pf", (2, 2), "down")
    with pytest.raises(PermissionError):
        g.swap("pf", (2, 2), (4, 0))


def test_move_wall_and_edge(mod):
    g = _game(mod, [MAZE_OPEN])
    g.move("pf", "down")          # (1,0)
    with pytest.raises(mod.IllegalMove):
        g.move("pf", "right")     # (1,1) wall
    g.move("pf", "up")            # (0,0)
    with pytest.raises(mod.IllegalMove):
        g.move("pf", "up")        # off grid
    assert g.state()["avatar"] == (0, 0)


def test_move_onto_block_illegal(mod):
    g = _game(mod, [MAZE_BLOCKED])
    g.move("pf", "right")
    g.move("pf", "right")
    g.move("pf", "down")          # (1,2)
    with pytest.raises(mod.IllegalMove):
        g.move("pf", "down")      # (2,2) block


def test_hint_open_maze(mod):
    g = _game(mod, [MAZE_OPEN])
    assert g.hint() == 8


def test_hint_none_when_blocked(mod):
    g = _game(mod, [MAZE_BLOCKED])
    assert g.hint() is None


def test_push_opens_path(mod):
    g = _game(mod, [MAZE_BLOCKED])
    g.push("bl", (2, 2), "down")
    st = g.state()
    assert [tuple(b) for b in st["blocks"]] == [(3, 2)]
    assert g.hint() == 8


def test_push_illegal_cases(mod):
    g = _game(mod, [MAZE_BLOCKED])
    with pytest.raises(mod.IllegalMove):
        g.push("bl", (2, 2), "left")    # (2,1) wall
    with pytest.raises(mod.IllegalMove):
        g.push("bl", (1, 2), "down")    # no block there
    assert [tuple(b) for b in g.state()["blocks"]] == [(2, 2)]


def test_swap_teleports_block(mod):
    g = _game(mod, [MAZE_BLOCKED])
    g.swap("sw", (2, 2), (4, 0))
    st = g.state()
    assert [tuple(b) for b in st["blocks"]] == [(4, 0)]
    assert g.hint() == 8


def test_swap_illegal_cases(mod):
    g = _game(mod, [MAZE_BLOCKED])
    with pytest.raises(mod.IllegalMove):
        g.swap("sw", (2, 3), (2, 4))    # two floor cells, no block
    with pytest.raises(mod.IllegalMove):
        g.swap("sw", (2, 2), (2, 1))    # wall involved
    with pytest.raises(mod.IllegalMove):
        g.swap("sw", (2, 2), (0, 0))    # avatar cell


def test_moves_counter_ignores_illegal(mod):
    g = _game(mod, [MAZE_OPEN])
    g.move("pf", "right")
    try:
        g.move("pf", "down")  # (1,1) wall
    except mod.IllegalMove:
        pass
    assert g.state()["moves"] == 1


def test_single_level_completion_score(mod):
    g = _game(mod, [["S.E"]])
    g.move("pf", "right")
    g.move("pf", "right")
    st = g.state()
    assert st["finished"] is True
    assert st["score"] == 1030  # 1000 - 20 + 50 bonus (opt=2)


def test_level_advance_and_total_score(mod):
    g = _game(mod, [["S.E"], ["S", ".", "E"]])
    g.move("pf", "right")
    g.move("pf", "right")
    st = g.state()
    assert st["level"] == 1 and st["finished"] is False
    assert st["avatar"] == (0, 0) and st["moves"] == 0
    g.move("pf", "down")
    g.move("pf", "down")
    st = g.state()
    assert st["finished"] is True
    assert st["score"] == 2060


def test_no_bonus_when_wasteful(mod):
    g = _game(mod, [["S.E"]])
    for d in ("right", "left", "right", "left", "right"):
        g.move("pf", d)
    g.move("pf", "right")
    st = g.state()
    # 6 moves > opt(2) + 2 -> no bonus; 1000 - 60 = 940
    assert st["score"] == 940 and st["finished"] is True
