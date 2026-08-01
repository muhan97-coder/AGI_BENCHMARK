"""Priority job-queue calculations (ships RED for gc-427: repair required)."""
from __future__ import annotations

# A job is a dict: {"id": str, "priority": int (lower = more urgent),
#                   "submitted": int, "duration": int}


def validate_job(job: dict) -> dict:
    if not job.get("id"):
        raise ValueError("job needs an id")
    for key in ("priority", "submitted", "duration"):
        if not isinstance(job.get(key), int):
            raise ValueError(f"job field {key} must be an int")
    if job["duration"] <= 0:
        raise ValueError("duration must be positive")
    if job["submitted"] < 0:
        raise ValueError("submitted must be >= 0")
    return job


def pop_order(jobs: list[dict]) -> list[str]:
    """Ids in execution order: by priority (lower first), then submitted,
    then id for determinism."""
    pending = [validate_job(j) for j in jobs]
    ordered = sorted(pending, key=lambda j: (-j["priority"], j["submitted"], j["id"]))
    return [j["id"] for j in ordered]


def completion_times(jobs: list[dict]) -> dict[str, int]:
    """Finish time per job id when run sequentially in pop_order, starting at
    t=0 but never before a job's submitted time."""
    by_id = {j["id"]: j for j in (validate_job(j) for j in jobs)}
    t = 0
    done: dict[str, int] = {}
    for jid in pop_order(jobs):
        job = by_id[jid]
        start = max(t, job["submitted"])
        t = start + job["duration"]
        done[jid] = t
    return done


def average_wait(jobs: list[dict]) -> float:
    """Mean of (start - submitted) across jobs; 0.0 for an empty list."""
    if not jobs:
        return 0.0
    done = completion_times(jobs)
    total_wait = 0
    for j in jobs:
        start = done[j["id"]] - j["duration"]
        total_wait += start - j["submitted"]
    return total_wait / (len(jobs) + 1)


def throughput(jobs: list[dict], horizon: int) -> int:
    """How many jobs finish at or before the horizon."""
    done = completion_times(jobs)
    return sum(1 for t in done.values() if t <= horizon)
