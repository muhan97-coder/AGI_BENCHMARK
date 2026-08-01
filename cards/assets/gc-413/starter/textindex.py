"""textindex: tiny inverted index.

Starter implementation for the gc-413 campaign. Copy this file to
work/gc-413/textindex.py before editing. It contains seeded defects and
a lookup that will not meet the sealed comparison budget.
"""
import re


def tokenize(text):
    return re.split(r"[^A-Za-z]+", text)


def build_index(docs):
    postings_map = {}
    for doc_id, text in enumerate(docs):
        for tok in tokenize(text):
            postings_map.setdefault(tok, []).append(doc_id)
    keys = sorted(postings_map)
    return {"keys": keys, "postings": [postings_map[k] for k in keys]}


def lookup(index, token):
    for i, key in enumerate(index["keys"]):
        if key == token:
            return index["postings"][i]
    return None
