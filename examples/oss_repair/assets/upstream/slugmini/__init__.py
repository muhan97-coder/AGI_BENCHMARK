"""slugmini -- a miniature slug builder (demo package, pinned at 0.3.1)."""

import re
import unicodedata

__all__ = ["slugify", "words"]
__version__ = "0.3.1"

_WORD_RE = re.compile(r"[a-z0-9]+")


def _fold(text):
    """Strip accents by decomposing and dropping combining marks."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def words(text):
    """Split *text* into lowercase alphanumeric words."""
    return _WORD_RE.findall(_fold(text).lower())


def slugify(text, separator="-"):
    """Return a slug for *text*: its words joined by *separator*."""
    return separator.join(words(text))
