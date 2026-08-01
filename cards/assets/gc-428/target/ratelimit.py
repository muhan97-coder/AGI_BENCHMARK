"""Deterministic token-bucket rate limiter (mutation target for gc-428)."""
from __future__ import annotations


class TokenBucket:
    """Classic token bucket with an explicit clock (integer milliseconds)."""

    def __init__(self, capacity: int, refill_per_sec: float):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_per_sec <= 0:
            raise ValueError("refill rate must be positive")
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = float(capacity)
        self.last_ms = 0

    def _refill(self, now_ms: int) -> None:
        if now_ms < self.last_ms:
            raise ValueError("clock went backwards")
        elapsed = (now_ms - self.last_ms) / 1000.0
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        self.last_ms = now_ms

    def allow(self, now_ms: int, cost: float = 1.0) -> bool:
        """Consume `cost` tokens if available; True when allowed."""
        if cost <= 0:
            raise ValueError("cost must be positive")
        self._refill(now_ms)
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def available(self, now_ms: int) -> float:
        """Tokens available at now_ms (refilling as a side effect)."""
        self._refill(now_ms)
        return self.tokens

    def time_until_available(self, now_ms: int, cost: float = 1.0) -> int:
        """Milliseconds from now_ms until `cost` tokens will be available
        (0 when already available). Raises ValueError when cost > capacity."""
        if cost > self.capacity:
            raise ValueError("cost exceeds capacity")
        self._refill(now_ms)
        deficit = cost - self.tokens
        if deficit <= 0:
            return 0
        ms = deficit / self.refill_per_sec * 1000.0
        return int(ms) + (0 if ms == int(ms) else 1)


def burst_schedule(capacity: int, refill_per_sec: float,
                   arrivals_ms: list[int]) -> list[bool]:
    """Outcome of unit-cost requests at the given arrival times."""
    bucket = TokenBucket(capacity, refill_per_sec)
    return [bucket.allow(t) for t in arrivals_ms]
