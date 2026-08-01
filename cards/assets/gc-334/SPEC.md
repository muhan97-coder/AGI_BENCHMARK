# gc-334 Interface Contract — AstroSim (MARBLE coding task_id=45)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=45, at
commit `8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-334/solution.py`. Pure Python, deterministic, 2D vectors as
`(x, y)` tuples.

## class Body(name, mass, pos, vel, radius)

Attributes `.name`, `.mass`, `.pos`, `.vel`, `.radius` (pos/vel are `(x, y)` tuples).

## class Simulation(bodies: list[Body], G=1.0)

- `.bodies` — current list of `Body` objects, in order.
- `step(dt)` — exactly this update rule (semi-implicit / symplectic Euler):
  1. For every body i compute acceleration from current positions:
     `a_i = sum over j != i of G * m_j * (r_j - r_i) / |r_j - r_i|^3`.
  2. For every body: `v_i += a_i * dt` (all velocity updates use the accelerations
     from step 1).
  3. For every body: `r_i += v_i * dt`.
  4. Collision handling: while any pair has `|r_i - r_j| < radius_i + radius_j`
     (strictly less), merge the pair with the smallest indices (i, then j): the
     merged body takes the earlier index and the later body is removed. Merged body:
     `mass = m_i + m_j`; `pos` = center of mass; `vel` = total momentum / total mass;
     `radius = (radius_i^3 + radius_j^3) ** (1/3)`; `name = "<name_i>+<name_j>"`.
- `run(steps, dt)` — calls `step(dt)` `steps` times.
- `kinetic_energy() -> float` — `sum(0.5 * m * |v|^2)`.
- `potential_energy() -> float` — `sum over pairs i<j of -G * m_i * m_j / |r_i - r_j|`.
- `total_momentum() -> (px, py)`.

No randomness anywhere: two simulations built from identical inputs must produce
bit-identical trajectories.
