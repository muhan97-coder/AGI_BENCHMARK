"""Tiny double-entry ledger helpers (induced-failure target for gc-424)."""
from __future__ import annotations

# An entry is a dict: {"account": str, "debit": float, "credit": float}


def validate_entry(entry: dict) -> dict:
    """Return the entry; raise ValueError when malformed."""
    if not entry.get("account"):
        raise ValueError("entry needs an account")
    debit = float(entry.get("debit", 0))
    credit = float(entry.get("credit", 0))
    if debit < 0 or credit < 0:
        raise ValueError("amounts must be non-negative")
    if debit == 0 and credit == 0:
        raise ValueError("entry must move value")
    if debit > 0 and credit > 0:
        raise ValueError("entry cannot be both debit and credit")
    return {"account": entry["account"], "debit": debit, "credit": credit}


def post(journal: list[dict], entries: list[dict]) -> list[dict]:
    """Validate and append entries; returns the new journal (input untouched)."""
    new = list(journal)
    for e in entries:
        new.append(validate_entry(e))
    return new


def account_balance(journal: list[dict], account: str) -> float:
    """Debits minus credits for one account."""
    total = 0.0
    for e in journal:
        if e["account"] == account:
            total += e["debit"] - e["credit"]
    return total


def trial_balance(journal: list[dict]) -> float:
    """Sum of debits minus sum of credits across the whole journal."""
    debits = sum(e["debit"] for e in journal)
    credits = sum(e["credit"] for e in journal)
    return debits - credits


def running_totals(journal: list[dict]) -> list[float]:
    """Cumulative trial balance after each posted entry."""
    out = []
    total = 0.0
    for e in journal:
        total += e["debit"] - e["credit"]
        out.append(total)
    return out


def accounts(journal: list[dict]) -> list[str]:
    """Sorted unique account names."""
    return sorted({e["account"] for e in journal})


def largest_movement(journal: list[dict]) -> dict | None:
    """Entry with the largest absolute amount; None for an empty journal."""
    best = None
    best_amt = -1.0
    for e in journal:
        amt = max(e["debit"], e["credit"])
        if amt > best_amt:
            best = e
            best_amt = amt
    return best
