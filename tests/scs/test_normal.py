import importlib
import math
from unittest import mock

import pytest


def test_normal_initializes_and_reuses_the_cached_pair():
    generator = importlib.reload(importlib.import_module("scs.smpl.rand"))
    expected = 3.0 + 2.0 * math.sqrt(-math.log(0.5))
    with mock.patch.object(generator, "ranf", side_effect=[0.75, 0.75]) as random:
        assert generator.normal(3.0, 2.0) == pytest.approx(expected)
        assert generator.normal(3.0, 2.0) == pytest.approx(expected)
        assert random.call_count == 2
