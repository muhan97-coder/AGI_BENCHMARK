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


def slugify(text, separator="-", stopwords=None):
    """Return a slug for *text*: its words joined by *separator*.

    *stopwords* is an optional iterable of words to drop. Matching happens on
    the extracted, folded, lowercased words, so callers can pass them in any
    case. Filtering runs after word extraction, which is why removing a word
    in the middle cannot leave a doubled separator behind. A filter that would
    remove every word is ignored: an empty slug is never more useful than the
    unfiltered one.
    """
    tokens = words(text)
    if stopwords:
        dropped = {str(word).lower() for word in stopwords}
        kept = [token for token in tokens if token not in dropped]
        if kept:
            tokens = kept
    return separator.join(tokens)
