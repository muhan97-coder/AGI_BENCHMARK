# gc-330 Interface Contract — MultiAgentTaskScheduler (MARBLE coding task_id=90)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=90, at
commit `8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-330/solution.py`. Times are ints supplied by the caller.

## class MultiAgentTaskScheduler()

Auto-assignment rule (applies immediately after `add_task`, `complete`,
`set_unavailable`, `set_available`): repeatedly take the highest-priority pending task
(ties: earliest added first) and assign it to the available agent with the lowest
current load (in-progress task count < capacity; ties: alphabetical agent name).
Stop when no pending task or no available agent remains. An unavailable agent is
never assignable.

- `add_agent(name, capacity) -> None` — duplicate raises `ValueError`;
  `capacity < 1` raises `ValueError`. Agents start available.
- `add_task(name, priority, time, description="") -> None` — duplicate raises
  `ValueError`. New tasks are `"pending"`, then auto-assignment runs at `time`.
- `status(task) -> str` — `"pending" | "in_progress" | "completed"`; unknown task
  raises `KeyError`.
- `assignee(task) -> str | None` — current agent, `None` when pending/completed.
- `complete(agent, task, time) -> None` — only the assigned agent may complete,
  otherwise `PermissionError`; task must be `"in_progress"` else `RuntimeError`.
  Frees the agent slot, then auto-assignment runs at `time`.
- `set_unavailable(agent, time) -> None` — unknown agent raises `KeyError`. All of
  the agent's in-progress tasks return to `"pending"` (requeued in their original
  add order at their original priority), then auto-assignment runs at `time` (other
  agents may pick them up).
- `set_available(agent, time) -> None` — re-enables the agent, then auto-assignment
  runs at `time`.
- `history() -> list[dict]` — append-only event log; each entry
  `{"event", "task", "agent", "time"}` with events `"assigned"`, `"completed"`,
  `"requeued"` (agent = the agent it was pulled from).
- `send(sender, recipient, text) -> None` / `inbox(recipient) -> list` of
  `(sender, text)` in order; unknown agent raises `KeyError`.
- `tasks_by_status(status) -> list[str]` — sorted task names; invalid status raises
  `ValueError`.
- `find(keyword) -> list[str]` — sorted names of tasks whose name or description
  contains `keyword` (case-sensitive).
