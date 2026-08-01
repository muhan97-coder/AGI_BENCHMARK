"""tinydate -- a miniature duration formatter (demo instance repo)."""

__all__ = ["format_duration"]
__version__ = "0.9.0"


def format_duration(seconds):
    """Render *seconds* as a compact '1h 30m 5s' string."""
    if seconds < 0:
        raise ValueError("seconds must be non-negative")
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs:
        parts.append(f"{secs}s")
    return " ".join(parts)
