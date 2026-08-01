# Sealed acceptance tests for gc-341 (marshmallow: fields.Enum).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import enum

import pytest
from marshmallow import Schema, ValidationError, fields


class Color(enum.Enum):
    RED = 1
    GREEN = 2


class ByNameSchema(Schema):
    c = fields.Enum(Color)


class ByValueSchema(Schema):
    c = fields.Enum(Color, by_value=True)


def test_dump_by_name():
    assert ByNameSchema().dump({"c": Color.RED}) == {"c": "RED"}


def test_load_by_name():
    assert ByNameSchema().load({"c": "GREEN"}) == {"c": Color.GREEN}


def test_dump_by_value():
    assert ByValueSchema().dump({"c": Color.RED}) == {"c": 1}


def test_load_by_value():
    assert ByValueSchema().load({"c": 2}) == {"c": Color.GREEN}


def test_load_invalid_name_raises():
    with pytest.raises(ValidationError) as exc:
        ByNameSchema().load({"c": "BLUE"})
    assert exc.value.messages == {"c": ["Must be one of: RED, GREEN."]}


def test_load_invalid_value_raises():
    with pytest.raises(ValidationError) as exc:
        ByValueSchema().load({"c": 3})
    assert exc.value.messages == {"c": ["Must be one of: 1, 2."]}


def test_by_value_with_field_type():
    class TypedSchema(Schema):
        c = fields.Enum(Color, by_value=fields.Integer)

    assert TypedSchema().dump({"c": Color.GREEN}) == {"c": 2}
    assert TypedSchema().load({"c": 1}) == {"c": Color.RED}
