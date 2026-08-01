# Sealed acceptance tests for gc-345 (packaging: PEP 639 license expressions).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import pytest


def canonicalize(expr):
    from packaging.licenses import canonicalize_license_expression

    return canonicalize_license_expression(expr)


def test_single_id_case_normalized():
    assert canonicalize("mit") == "MIT"


def test_or_expression_normalized():
    assert canonicalize("mit or apache-2.0") == "MIT OR Apache-2.0"


def test_nested_parentheses_normalized():
    assert (
        canonicalize("MIT AND (Apache-2.0 OR bsd-2-clause)")
        == "MIT AND (Apache-2.0 OR BSD-2-Clause)"
    )


def test_plus_suffix_and_exception_clause():
    assert (
        canonicalize("gpl-2.0+ WITH bison-exception-2.2")
        == "GPL-2.0+ WITH Bison-exception-2.2"
    )


def test_licenseref_passthrough():
    assert canonicalize("LicenseRef-Public-Domain") == "LicenseRef-Public-Domain"


def test_result_is_a_string():
    assert isinstance(canonicalize("mit"), str)


def test_invalid_expressions_rejected():
    from packaging.licenses import InvalidLicenseExpression

    for bad in ["mit or", "unknownlicense", "MIT AND OR"]:
        with pytest.raises(InvalidLicenseExpression):
            canonicalize(bad)
