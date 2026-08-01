# Sealed acceptance tests for gc-343 (PyJWT: sub and jti claim validation).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import jwt
import pytest
from jwt.exceptions import InvalidJTIError, InvalidSubjectError

KEY = "sealed-secret"


def encode(payload):
    return jwt.encode(payload, KEY, algorithm="HS256")


def decode(token, **kwargs):
    return jwt.decode(token, KEY, algorithms=["HS256"], **kwargs)


def test_matching_subject_accepted():
    token = encode({"sub": "alice"})
    assert decode(token, subject="alice") == {"sub": "alice"}


def test_mismatched_subject_rejected():
    token = encode({"sub": "alice"})
    with pytest.raises(InvalidSubjectError):
        decode(token, subject="bob")


def test_non_string_subject_rejected():
    token = encode({"sub": 999})
    with pytest.raises(InvalidSubjectError):
        decode(token, subject="999")


def test_non_string_jti_rejected():
    token = encode({"jti": 123})
    with pytest.raises(InvalidJTIError):
        decode(token)


def test_string_jti_accepted():
    token = encode({"jti": "abc-123"})
    assert decode(token) == {"jti": "abc-123"}


def test_decode_without_subject_kwarg_unchanged():
    token = encode({"sub": "alice", "n": 1})
    assert decode(token) == {"sub": "alice", "n": 1}
