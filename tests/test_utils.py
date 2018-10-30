#!/usr/bin/env python3

from maps.utils import clamp, is_power_of_two


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
