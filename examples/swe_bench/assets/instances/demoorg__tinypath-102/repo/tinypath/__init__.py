"""tinypath -- a miniature pure-text path normaliser (demo instance repo)."""

__all__ = ["normalize"]
__version__ = "1.4.2"


def normalize(path):
    """Collapse '.', '..' and duplicated separators in *path*."""
    absolute = path.startswith("/")
    parts = []
    for segment in path.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append("..")
            continue
        parts.append(segment)
    joined = "/".join(parts)
    if absolute:
        return "/" + joined
    return joined or "."
