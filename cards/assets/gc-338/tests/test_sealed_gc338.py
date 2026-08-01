# Sealed acceptance tests for gc-338 (humanize: SI metric prefix formatting).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import humanize


def test_metric_kilo_with_unit():
    assert humanize.metric(1500, "V") == "1.50 kV"


def test_metric_micro_with_unit():
    assert humanize.metric(0.000001, "A") == "1.00 μA"


def test_metric_out_of_prefix_range_uses_scientific():
    assert humanize.metric(1e27) == "1.00 x 10²⁷"


def test_metric_milli_no_unit():
    assert humanize.metric(0.9) == "900 m"


def test_metric_precision_parameter():
    assert humanize.metric(10000, precision=5) == "10.000 k"


def test_existing_api_unchanged():
    assert humanize.intcomma(123456) == "123,456"
    assert humanize.naturalsize(300) == "300 Bytes"
