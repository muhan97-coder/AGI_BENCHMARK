"""Sealed acceptance suite for gc-334 (MARBLE coding task_id=45: AstroSim).

Loads the agent's solution from workspace/gc-334/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
import math
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-334" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc334", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def mod():
    return _load()


def _orbit_sim(mod):
    sun = mod.Body("sun", 1000.0, (0.0, 0.0), (0.0, 0.0), 0.01)
    planet = mod.Body("planet", 0.001, (10.0, 0.0), (0.0, 10.0), 0.001)
    return mod.Simulation([sun, planet], G=1.0)


def _reference_step(state, G, dt):
    """Independent implementation of the specified integrator (no collisions)."""
    n = len(state)
    acc = []
    for i in range(n):
        ax = ay = 0.0
        mi, (xi, yi), _ = state[i]
        for j in range(n):
            if i == j:
                continue
            mj, (xj, yj), _ = state[j]
            dx, dy = xj - xi, yj - yi
            d = math.sqrt(dx * dx + dy * dy)
            ax += G * mj * dx / d ** 3
            ay += G * mj * dy / d ** 3
        acc.append((ax, ay))
    out = []
    for i in range(n):
        m, (x, y), (vx, vy) = state[i]
        vx += acc[i][0] * dt
        vy += acc[i][1] * dt
        out.append((m, (x + vx * dt, y + vy * dt), (vx, vy)))
    return out


def test_body_attributes(mod):
    b = mod.Body("x", 2.5, (1.0, -2.0), (0.5, 0.25), 0.1)
    assert b.name == "x" and b.mass == 2.5
    assert tuple(b.pos) == (1.0, -2.0) and tuple(b.vel) == (0.5, 0.25)
    assert b.radius == 0.1


def test_single_step_hand_computed(mod):
    a = mod.Body("a", 1.0, (-1.0, 0.0), (0.0, 0.0), 0.01)
    b = mod.Body("b", 1.0, (1.0, 0.0), (0.0, 0.0), 0.01)
    sim = mod.Simulation([a, b], G=1.0)
    sim.step(0.1)
    # |a| = G*m/d^2 = 1/4; v = 0.025; x = -1 + 0.0025
    ba, bb = sim.bodies
    assert ba.vel[0] == pytest.approx(0.025, abs=1e-12)
    assert bb.vel[0] == pytest.approx(-0.025, abs=1e-12)
    assert ba.pos[0] == pytest.approx(-0.9975, abs=1e-12)
    assert bb.pos[0] == pytest.approx(0.9975, abs=1e-12)
    assert ba.pos[1] == 0.0 and bb.pos[1] == 0.0


def test_momentum_conserved(mod):
    sim = _orbit_sim(mod)
    p0 = sim.total_momentum()
    sim.run(200, 0.001)
    p1 = sim.total_momentum()
    assert p1[0] == pytest.approx(p0[0], abs=1e-9)
    assert p1[1] == pytest.approx(p0[1], abs=1e-9)


def test_reference_trajectory_three_bodies(mod):
    bodies = [
        mod.Body("a", 10.0, (0.0, 0.0), (0.0, 0.0), 0.001),
        mod.Body("b", 1.0, (5.0, 0.0), (0.0, 1.5), 0.001),
        mod.Body("c", 1.0, (0.0, 7.0), (-1.2, 0.0), 0.001),
    ]
    sim = mod.Simulation(bodies, G=1.0)
    state = [(10.0, (0.0, 0.0), (0.0, 0.0)),
             (1.0, (5.0, 0.0), (0.0, 1.5)),
             (1.0, (0.0, 7.0), (-1.2, 0.0))]
    for _ in range(50):
        sim.step(0.01)
        state = _reference_step(state, 1.0, 0.01)
    for body, (m, pos, vel) in zip(sim.bodies, state):
        assert body.pos[0] == pytest.approx(pos[0], abs=1e-9)
        assert body.pos[1] == pytest.approx(pos[1], abs=1e-9)
        assert body.vel[0] == pytest.approx(vel[0], abs=1e-9)
        assert body.vel[1] == pytest.approx(vel[1], abs=1e-9)


def test_energy_drift_bounded(mod):
    sim = _orbit_sim(mod)
    e0 = sim.kinetic_energy() + sim.potential_energy()
    sim.run(1000, 0.001)
    e1 = sim.kinetic_energy() + sim.potential_energy()
    assert abs(e1 - e0) / abs(e0) < 0.01


def test_circular_orbit_radius_stable(mod):
    sim = _orbit_sim(mod)
    sim.run(1000, 0.001)
    planet = sim.bodies[1]
    sun = sim.bodies[0]
    r = math.dist(planet.pos, sun.pos)
    assert abs(r - 10.0) / 10.0 < 0.02


def test_collision_merges_conserving_momentum(mod):
    a = mod.Body("a", 2.0, (-0.2, 0.0), (1.0, 0.0), 0.06)
    b = mod.Body("b", 1.0, (0.2, 0.0), (0.0, 0.0), 0.06)
    sim = mod.Simulation([a, b], G=0.0)
    for _ in range(3):
        sim.step(0.1)
    assert len(sim.bodies) == 1
    merged = sim.bodies[0]
    assert merged.name == "a+b"
    assert merged.mass == pytest.approx(3.0)
    assert merged.vel[0] == pytest.approx(2.0 / 3.0, abs=1e-12)
    assert merged.vel[1] == pytest.approx(0.0, abs=1e-12)


def test_merged_radius_cube_law(mod):
    a = mod.Body("a", 1.0, (0.0, 0.0), (0.0, 0.0), 0.06)
    b = mod.Body("b", 1.0, (0.05, 0.0), (0.0, 0.0), 0.06)
    sim = mod.Simulation([a, b], G=0.0)
    sim.step(0.001)
    assert len(sim.bodies) == 1
    assert sim.bodies[0].radius == pytest.approx((2 * 0.06 ** 3) ** (1 / 3), abs=1e-12)


def test_touching_bodies_do_not_merge(mod):
    a = mod.Body("a", 1.0, (0.0, 0.0), (0.0, 0.0), 0.5)
    b = mod.Body("b", 1.0, (1.0, 0.0), (0.0, 0.0), 0.5)
    sim = mod.Simulation([a, b], G=0.0)
    sim.step(0.1)
    assert len(sim.bodies) == 2


def test_potential_energy_exact(mod):
    a = mod.Body("a", 3.0, (0.0, 0.0), (0.0, 0.0), 0.01)
    b = mod.Body("b", 4.0, (0.0, 2.0), (0.0, 0.0), 0.01)
    sim = mod.Simulation([a, b], G=2.0)
    assert sim.potential_energy() == pytest.approx(-2.0 * 3.0 * 4.0 / 2.0, abs=1e-12)


def test_kinetic_energy_exact(mod):
    a = mod.Body("a", 2.0, (0.0, 0.0), (3.0, 4.0), 0.01)
    sim = mod.Simulation([a], G=1.0)
    assert sim.kinetic_energy() == pytest.approx(0.5 * 2.0 * 25.0, abs=1e-12)


def test_total_momentum_vector(mod):
    a = mod.Body("a", 2.0, (0.0, 0.0), (1.0, -1.0), 0.01)
    b = mod.Body("b", 3.0, (5.0, 5.0), (0.0, 2.0), 0.01)
    sim = mod.Simulation([a, b], G=1.0)
    px, py = sim.total_momentum()
    assert px == pytest.approx(2.0, abs=1e-12)
    assert py == pytest.approx(4.0, abs=1e-12)


def test_determinism_two_identical_sims(mod):
    s1, s2 = _orbit_sim(mod), _orbit_sim(mod)
    s1.run(300, 0.001)
    s2.run(300, 0.001)
    for b1, b2 in zip(s1.bodies, s2.bodies):
        assert tuple(b1.pos) == tuple(b2.pos)
        assert tuple(b1.vel) == tuple(b2.vel)


def test_run_equals_manual_steps(mod):
    s1, s2 = _orbit_sim(mod), _orbit_sim(mod)
    s1.run(10, 0.05)
    for _ in range(10):
        s2.step(0.05)
    for b1, b2 in zip(s1.bodies, s2.bodies):
        assert tuple(b1.pos) == tuple(b2.pos)
