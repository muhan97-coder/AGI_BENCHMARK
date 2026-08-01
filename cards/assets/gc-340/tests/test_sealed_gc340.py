# Sealed acceptance tests for gc-340 (schedule: Job.until deadline support).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import datetime as dt

import pytest
import schedule


def test_until_past_deadline_raises():
    s = schedule.Scheduler()
    with pytest.raises(schedule.ScheduleValueError):
        s.every(1).seconds.until(dt.datetime.now() - dt.timedelta(hours=1))


def test_until_accepts_timedelta_and_sets_cancel_after():
    s = schedule.Scheduler()
    job = s.every(1).seconds.until(dt.timedelta(hours=2)).do(lambda: None)
    assert isinstance(job.cancel_after, dt.datetime)
    delta = job.cancel_after - dt.datetime.now()
    assert dt.timedelta(hours=1, minutes=59) < delta <= dt.timedelta(hours=2)


def test_until_accepts_datetime():
    s = schedule.Scheduler()
    deadline = dt.datetime.now() + dt.timedelta(days=1)
    job = s.every(1).seconds.until(deadline).do(lambda: None)
    assert job.cancel_after == deadline


def test_job_runs_while_within_deadline():
    s = schedule.Scheduler()
    calls = []
    job = (
        s.every(1)
        .seconds.until(dt.datetime.now() + dt.timedelta(hours=1))
        .do(lambda: calls.append(1))
    )
    job.next_run = dt.datetime.now() - dt.timedelta(seconds=1)
    s.run_pending()
    assert calls == [1]
    assert len(s.jobs) == 1


def test_job_cancelled_after_deadline_without_running():
    s = schedule.Scheduler()
    calls = []
    job = (
        s.every(1)
        .seconds.until(dt.datetime.now() + dt.timedelta(hours=1))
        .do(lambda: calls.append(1))
    )
    job.cancel_after = dt.datetime.now() - dt.timedelta(seconds=1)
    job.next_run = dt.datetime.now() - dt.timedelta(seconds=1)
    s.run_pending()
    assert calls == []
    assert len(s.jobs) == 0


def test_chaining_returns_job_for_further_setup():
    s = schedule.Scheduler()
    job = s.every(5).minutes.until(dt.timedelta(days=2))
    assert job.do(lambda: None) is not None
    assert len(s.jobs) == 1
