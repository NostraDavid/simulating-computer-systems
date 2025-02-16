import math
import pytest
from unittest import mock
from scs.main import expntl, main
from hypothesis import given
import hypothesis.strategies as st


@given(st.floats(min_value=0.1, max_value=1000.0))
def test_expntl_hypothesis(mean):
    with mock.patch("random.random", return_value=0.5):
        assert expntl(mean) == pytest.approx(-mean * math.log(0.5), 0.001)


@pytest.mark.parametrize(
    "random_value, expected",
    [
        (0.5, -100 * math.log(0.5)),
        (0.1, -100 * math.log(0.1)),
        (0.9, -100 * math.log(0.9)),
    ],
)
def test_expntl(random_value, expected):
    with mock.patch("random.random", return_value=random_value):
        assert expntl(100) == pytest.approx(expected, 0.001)


def test_main():
    with mock.patch("scs.main.expntl") as mock_expntl:
        # Mock expntl to return predictable values
        mock_expntl.return_value = 500
        main()
        assert mock_expntl.call_count == 800
