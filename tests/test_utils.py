#!/usr/bin/env python3
import pytest

from maps.exceptions import InvalidColour
from maps.utils import clamp, is_power_of_two, parse_colour, lat_lon_clamp


def test_clamp():
    assert clamp(3, 0, 5) == 3
    assert clamp(3, 0, 3) == 3
    assert clamp(3, 0, 2) == 2
    assert clamp(3, 0, 0) == 0
    assert clamp(-3, -10, 5) == -3
    assert clamp(0, 0, 5) == 0
    assert clamp(3, 3, 3) == 3
    assert clamp(-2, -10, 5) == -2
    assert clamp(6, 3, 5) == 5
    assert clamp(1, 3, 5) == 3


def test_is_power_of_two():
    assert not is_power_of_two(0)
    assert not is_power_of_two(1023)
    assert not is_power_of_two(3)
    assert not is_power_of_two(-2)
    assert not is_power_of_two(-1)
    assert is_power_of_two(1)
    assert is_power_of_two(2)
    assert is_power_of_two(4)
    assert is_power_of_two(64)
    assert is_power_of_two(1024)


def test_parse_colour():
    # these should all error but should throw the InvalidColour exception
    should_all_error = [
        # shouldn't accept more than 4 elements
        (1, 2, 3, 4, 5, 6),
        # shouldn't accept less than 3 elements
        (1, 2),
        # shouldn't accept an empty string
        '',
        # shouldn't accept an invalid string
        '43f349g3498gbogb8',
        # shouldn't accept non-number values
        ['not a number!', 2, 3],
        # shouldn't accept non-number values in strings either
        '["not a number!", 2, 3]',
        # shouldn't accept invalid values
        '#XX03FF',
        # shouldn't accept unbalanced brackets
        '[1, 2, 3]]',
        # shouldn't accept out of range numbers (below 0)
        (-1, 2, 3, 4),
        # shouldn't accept out of range numbers (above 255)
        (1, 2, 300, 4),
    ]
    for error_value in should_all_error:
        with pytest.raises(InvalidColour):
            parse_colour(error_value)

    assert parse_colour((1, 2, 3)) == (1, 2, 3)
    assert parse_colour('(1, 2, 3)') == (1, 2, 3)
    assert parse_colour([1, 2, 3]) == (1, 2, 3)
    assert parse_colour((1, 2, 3, 4)) == (1, 2, 3, 4)
    assert parse_colour([1, 2, 3, 4]) == (1, 2, 3, 4)
    assert parse_colour('[1,2, 3,4]') == (1, 2, 3, 4)
    assert parse_colour('#010203') == (1, 2, 3)
    assert parse_colour('#ffFFff') == (255, 255, 255)
    # even this dumb formatting works, huzzah!
    assert parse_colour('[1,2,          3  ,4)') == (1, 2, 3, 4)
    assert parse_colour((1.1, 2.2, 3.3, 4.4)) == (1, 2, 3, 4)


def test_lat_lon_clamp():
    assert lat_lon_clamp((0, 0)) == (0, 0)
    assert lat_lon_clamp((-90, 90)) == (-85.0511, 90)
    assert lat_lon_clamp((90, 90)) == (85.0511, 90)
    assert lat_lon_clamp((10, 499)) == (10, 180)
    assert lat_lon_clamp((10, -499)) == (10, -180)
    assert lat_lon_clamp((-90, -499)) == (-85.0511, -180)
    assert lat_lon_clamp((90, 499)) == (85.0511, 180)
