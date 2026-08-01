"""globlite: minimal single-segment glob matching.

Starter implementation for the gc-409 campaign. Copy this file to
work/gc-409/globlite.py before editing. It contains seeded defects.
"""


def _tokenize(pattern):
    tokens = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            tokens.append(("star",))
            i += 1
        elif c == "?":
            tokens.append(("q",))
            i += 1
        elif c == "[":
            j = i + 1
            negated = False
            if j < len(pattern) and pattern[j] == "!":
                negated = True
                j += 1
            k = j
            while pattern[k] != "]":
                k += 1
            tokens.append(("set", frozenset(pattern[j:k]), negated))
            i = k + 1
        else:
            tokens.append(("lit", c))
            i += 1
    return tokens


def _match_tokens(tokens, name):
    n, m = len(tokens), len(name)
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(1, n + 1):
        if tokens[i - 1][0] in ("star", "q"):
            dp[i][0] = dp[i - 1][0]
    for i in range(1, n + 1):
        t = tokens[i - 1]
        for j in range(1, m + 1):
            ch = name[j - 1]
            if t[0] == "star":
                dp[i][j] = dp[i - 1][j - 1] or dp[i][j - 1]
            elif t[0] == "q":
                dp[i][j] = dp[i - 1][j - 1]
            elif t[0] == "lit":
                dp[i][j] = dp[i - 1][j - 1] and ch == t[1]
            else:
                inset = ch in t[1]
                dp[i][j] = dp[i - 1][j - 1] and inset
    return dp[n][m]


def match(pattern, name):
    return _match_tokens(_tokenize(pattern), name)
