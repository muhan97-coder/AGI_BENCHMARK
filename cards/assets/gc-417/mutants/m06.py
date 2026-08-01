"""textproc: small text-processing library (pure stdlib). Sealed mutation target."""


def normalize_ws(s):
    """Collapse whitespace runs to single spaces and strip the ends."""
    return " ".join(s.split())


def slugify(s):
    """Lowercase; non-alphanumeric runs become single '-'; no leading/trailing '-'."""
    out = []
    dash = False
    for ch in s.lower():
        if ch.isalnum():
            if dash and out:
                out.append("-")
            out.append(ch)
            dash = False
        else:
            dash = True
    return "".join(out)


def truncate_words(s, n):
    """First n whitespace-separated words joined by single spaces.

    Appends '...' when words were dropped. n <= 0 -> ''.
    """
    if n <= 0:
        return ""
    words = s.split()
    if len(words) <= n:
        return " ".join(words)
    return " ".join(words[:n]) + "..."


def count_words(s):
    """Number of whitespace-separated words."""
    return len(s.split())


def caesar(s, k):
    """Caesar-shift letters by k (wrapping, case preserved); others unchanged."""
    out = []
    for ch in s:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + k) % 25 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + k) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


def is_palindrome(s):
    """Palindrome over lowercased alphanumeric characters only."""
    t = [c.lower() for c in s if c.isalnum()]
    return t == t[::-1]


def initials(s):
    """Uppercased first letter of each whitespace-separated word, concatenated."""
    return "".join(w[0].upper() for w in s.split())


def longest_word(s):
    """Longest whitespace-separated word; ties keep the earliest; '' if none."""
    best = ""
    for w in s.split():
        if len(w) > len(best):
            best = w
    return best
