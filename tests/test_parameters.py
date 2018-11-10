#!/usr/bin/env python3

import pytest
from colour import Color

from maps.exceptions import InvalidColour
from maps.parameters import parse_colour


def test_parse_colour():
    with pytest.raises(InvalidColour):
        parse_colour('#ooooooo')

    with pytest.raises(InvalidColour):
        parse_colour('#ffff')

    with pytest.raises(InvalidColour):
        parse_colour('#fffffff')

    assert parse_colour('#00ff00') == Color('#00ff00')
