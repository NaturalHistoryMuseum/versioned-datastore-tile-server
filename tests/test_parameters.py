#!/usr/bin/env python3
import base64
import gzip
import json
from unittest.mock import MagicMock

import pytest
from colour import Color

from maps.exceptions import InvalidColour, MissingIndex
from maps.parameters import parse_colour, extract, parse_query_body, extract_search_params


def compress_query(query):
    return base64.urlsafe_b64encode(gzip.compress(json.dumps(query).encode('utf-8')))


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


def test_parse_query_body():
    query = {'test': 5.4}
    assert parse_query_body(compress_query(query)) == query


def test_parse_colour():
    with pytest.raises(InvalidColour):
        parse_colour('#ooooooo')

    with pytest.raises(InvalidColour):
        parse_colour('#ffff')

    with pytest.raises(InvalidColour):
        parse_colour('#fffffff')

    assert parse_colour('#00ff00') == Color('#00ff00')


class TestExtractSearchParams:

    def test_no_indexes_through_params(self, monkeypatch):
        args = {'not_indexes': ':('}
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))
        with pytest.raises(MissingIndex):
            extract_search_params()

    def test_no_indexes_as_no_query_no_indexes(self, monkeypatch):
        args = {}
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))
        with pytest.raises(MissingIndex):
            extract_search_params()

    def test_no_indexes_through_query(self, monkeypatch):
        args = {'query': compress_query({'search': {}, 'not_indexes': ':('})}
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))
        with pytest.raises(MissingIndex):
            extract_search_params()

    def test_valid_direct_params(self, monkeypatch):
        args = {
            'indexes': 'index1, index3, index100',
            'search': json.dumps({'search': 'something'})
        }
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

        params = extract_search_params()
        assert params['indexes'] == ['index1', 'index3', 'index100']
        assert params['search_body'] == {'search': 'something'}

    def test_valid_query_params(self, monkeypatch):
        args = {
            'query': compress_query({
                'indexes': ['index1', 'index3', 'index100'],
                'search': {'search': 'something'},
            })
        }
        monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

        params = extract_search_params()
        assert params['indexes'] == ['index1', 'index3', 'index100']
        assert params['search_body'] == {'search': 'something'}
