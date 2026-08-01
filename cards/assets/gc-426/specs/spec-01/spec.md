# spec-01: rle_encode(s: str) -> str
Run-length encode: each maximal run of a character becomes `<char><count>`.
Empty string encodes to empty string. Example: 'aaabbc' -> 'a3b2c1'.
