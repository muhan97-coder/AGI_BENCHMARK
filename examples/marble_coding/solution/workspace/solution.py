"""Reference solution for ex-marble_coding — MeetingRoomBooker.

Stdlib only, single file, loaded by path by the sealed acceptance suite.
Bookings occupy the half-open interval [start, end), which is what makes
touching endpoints legal and overlaps illegal.
"""
from __future__ import annotations

WORKING_DAY_HOURS = 8.0


class MeetingRoomBooker:
    def __init__(self) -> None:
        self._rooms: dict[str, int] = {}
        self._bookings: dict[int, dict] = {}
        self._notifications: dict[str, list[str]] = {}
        self._next_id = 1

    # --- rooms -----------------------------------------------------------
    def add_room(self, name: str, capacity: int) -> None:
        if name in self._rooms:
            raise ValueError(f"room already exists: {name}")
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._rooms[name] = capacity

    def _require_room(self, room: str) -> int:
        if room not in self._rooms:
            raise KeyError(room)
        return self._rooms[room]

    def _active(self, room: str, day: str) -> list[dict]:
        return [b for b in self._bookings.values()
                if b["active"] and b["room"] == room and b["day"] == day]

    # --- booking ----------------------------------------------------------
    def book(self, user: str, room: str, day: str, start: int, end: int,
             attendees: int) -> int:
        capacity = self._require_room(room)
        if end <= start:
            raise ValueError("end must be after start")
        if start < 0 or end > 24:
            raise ValueError("hours must lie within 0..24")
        if attendees < 1 or attendees > capacity:
            raise ValueError("attendees outside room capacity")
        for other in self._active(room, day):
            if start < other["end"] and other["start"] < end:
                raise ValueError(f"overlaps booking {other['booking_id']}")

        # ids are only consumed by bookings that actually happen
        booking_id = self._next_id
        self._next_id += 1
        self._bookings[booking_id] = {
            "booking_id": booking_id, "user": user, "room": room, "day": day,
            "start": start, "end": end, "attendees": attendees, "active": True,
        }
        self._notify(user, f"booked:{booking_id}")
        return booking_id

    def cancel(self, user: str, booking_id: int) -> None:
        if booking_id not in self._bookings:
            raise KeyError(booking_id)
        booking = self._bookings[booking_id]
        if booking["user"] != user:
            raise PermissionError("only the owner may cancel a booking")
        booking["active"] = False
        self._notify(user, f"cancelled:{booking_id}")

    # --- views ------------------------------------------------------------
    def schedule(self, room: str, day: str) -> list[dict]:
        self._require_room(room)
        rows = sorted(self._active(room, day), key=lambda b: b["start"])
        keys = ("booking_id", "user", "start", "end", "attendees")
        return [{k: row[k] for k in keys} for row in rows]

    def _notify(self, user: str, message: str) -> None:
        self._notifications.setdefault(user, []).append(message)

    def notifications(self, user: str) -> list[str]:
        return list(self._notifications.get(user, []))

    def utilization(self, room: str, day: str) -> float:
        self._require_room(room)
        hours = sum(b["end"] - b["start"] for b in self._active(room, day))
        return round(hours / WORKING_DAY_HOURS, 4)

    def busiest_room(self, day: str) -> str | None:
        totals: dict[str, int] = {}
        for booking in self._bookings.values():
            if booking["active"] and booking["day"] == day:
                totals[booking["room"]] = (totals.get(booking["room"], 0)
                                           + booking["end"] - booking["start"])
        if not totals:
            return None
        return min(totals, key=lambda room: (-totals[room], room))
