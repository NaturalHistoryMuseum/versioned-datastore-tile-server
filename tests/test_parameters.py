#!/usr/bin/env python3
import base64
import gzip
import json
from unittest.mock import MagicMock

import pytest
from colour import Color

from maps.exceptions import InvalidColour, MissingIndex
from maps.parameters import parse_colour, extract, parse_query_body, extract_search_params, \
    extract_plot_parameters, extract_plot_utf_grid_params, extract_gridded_utf_grid_params, \
    extract_gridded_parameters


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


def test_extract_plot_parameters_all(monkeypatch):
    args = {
        # use 10.4 to ensure it's converted to an int
        'point_radius': 10.4,
        # use a 3 digit hex code to test that part
        'point_colour': '#fff',
        # use 3.2 to ensure it's converted to an int
        'border_width': 3.2,
        # use a 6 digit hex code to test that part
        'border_colour': '#000000',
        # use 2.1 to ensure it's converted to an int
        'resize_factor': 2.1,
    }
    monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

    params = extract_plot_parameters()
    assert params['point_radius'] == 10
    assert params['point_colour'] == Color('white')
    assert params['border_width'] == 3
    assert params['border_colour'] == Color('black')
    assert params['resize_factor'] == 2


def test_extract_plot_parameters_none(monkeypatch):
    args = {}
    monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

    params = extract_plot_parameters()
    for name in {'point_radius', 'point_colour', 'border_width', 'border_colour', 'resize_factor'}:
        # check that each of the expected names is in the params dict
        assert name in params


def test_extract_plot_utf_grid_params_all(monkeypatch):
    args = {
        # use 5.2 to ensure it's converted to an int
        'grid_resolution': 5.2,
        # use 4.6 to ensure it's converted to an int
        'point_width': 4.6,
    }
    monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

    params = extract_plot_utf_grid_params()
    assert params['grid_resolution'] == 5
    assert params['point_width'] == 4


def test_extract_plot_utf_grid_params_none(monkeypatch):
    args = {}
    monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

    params = extract_plot_utf_grid_params()
    for name in {'grid_resolution', 'point_width'}:
        # check that each of the expected names is in the params dict
        assert name in params


def test_extract_gridded_parameters_all(monkeypatch):
    args = {
        # use 10.4 to ensure it's converted to an int
        'grid_resolution': 10.4,
        # use a 3 digit hex code to test that part
        'cold_colour': '#fff',
        # use a 6 digit hex code to test that part
        'hot_colour': '#000000',
        # use 13.2 to ensure it's converted to an int
        'range_size': 13.2,
        # use 2.1 to ensure it's converted to an int
        'resize_factor': 2.1,
    }
    monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

    params = extract_gridded_parameters()
    assert params['grid_resolution'] == 10
    assert params['cold_colour'] == Color('white')
    assert params['hot_colour'] == Color('black')
    assert params['range_size'] == 13
    assert params['resize_factor'] == 2


def test_extract_gridded_parameters_none(monkeypatch):
    args = {}
    monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

    params = extract_gridded_parameters()
    for name in {'grid_resolution', 'cold_colour', 'hot_colour', 'range_size', 'resize_factor'}:
        # check that each of the expected names is in the params dict
        assert name in params


def test_extract_gridded_utf_grid_params_all(monkeypatch):
    args = {
        # use 5.2 to ensure it's converted to an int
        'grid_resolution': 5.2,
        # use 4.6 to ensure it's converted to an int
        'point_width': 4.6,
    }
    monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

    params = extract_gridded_utf_grid_params()
    assert params['grid_resolution'] == 5
    assert params['point_width'] == 4


def test_extract_gridded_utf_grid_params_none(monkeypatch):
    args = {}
    monkeypatch.setattr('maps.parameters.request', MagicMock(args=args))

    params = extract_gridded_utf_grid_params()
    for name in {'grid_resolution', 'point_width'}:
        # check that each of the expected names is in the params dict
        assert name in params
