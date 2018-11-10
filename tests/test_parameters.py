#!/usr/bin/env python3
from unittest.mock import MagicMock

import pytest
from colour import Color

from maps.exceptions import InvalidColour
from maps.parameters import parse_colour, extract


class TestExtract:

    def test_extract_param_is_present_no_parser(self, monkeypatch):
        args = {'test': 5.4}
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))
        assert extract('test', default=None, parser=None) == 5.4

    def test_extract_param_is_present_with_parser(self, monkeypatch):
        args = {'test': 5.4}
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))
        assert extract('test', default=None, parser=int) == 5

    def test_extract_param_is_not_present_no_parser(self, monkeypatch):
        args = {'test': 5.4}
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))
        assert extract('not_test', default=6.1, parser=None) == 6.1

    def test_extract_param_is_not_present_with_parser(self, monkeypatch):
        args = {'test': 5.4}
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))
        assert extract('not_test', default=6.1, parser=int) == 6.1


def test_parse_colour():
    with pytest.raises(InvalidColour):
        parse_colour('#ooooooo')

    with pytest.raises(InvalidColour):
        parse_colour('#ffff')

    with pytest.raises(InvalidColour):
        parse_colour('#fffffff')

    assert parse_colour('#00ff00') == Color('#00ff00')