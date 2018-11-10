#!/usr/bin/env python3

import base64
import gzip
import json

from colour import Color
from flask import request

from maps.exceptions import InvalidColour, MissingIndex


def extract(name, default=None, parser=None):
    """
    Extract the named parameter from the request, using the parser function if passed to parse the
    value before returning. If the value is not present, the default is returned.

    :param name: the name of the parameter
    :param default: the default value (default: None)
    :param parser: a parser function (default: None, which means the value is returned as is)
    :return: the (parsed) parameter value or default
    """
    if name in request.args:
        value = request.args[name]
        return value if parser is None else parser(value)
    else:
        return default


def parse_query_body(raw_query_body):
    """
    Parses the query body parameter in it's raw compressed form. This is expected to be a base64
    encoded, gzipped piece of JSON.

    :param raw_query_body: the raw query body
    :return: a dict
    """
    return json.loads(gzip.decompress(base64.urlsafe_b64decode(raw_query_body)))


def parse_colour(value):
    """
    Given a string value returns a colour or raises an error if it can't be parsed by the colour
    library. The string must be a 3 or 6 character hex code with a # prefixed to it.

    :param value: the hex colour
    :return: a Color object
    """
    try:
        return Color(value)
    except AttributeError as e:
        # if an error occurs, chuck our error
        raise InvalidColour(e)


def extract_search_params():
    """
    Extract the search parameters from the request. Currently allowed params:

        - index: contains the indexes to be searched (can be a comma separated list)
        - search: JSON encoded elasticsearch search dict to restrict the results
        - query: gzipped, base64, JSON encoded string containing two keys, the "indexes" which
                 should be a list of the indexes to search (i.e. the same as the index parameter)
                 and "search" which should contain a dict to pass on to elasticsearch (i.e. the same
                 as the search parameter)

    An index is required otherwise a MissingIndex exception is raised.

    :return: a dict
    """
    # the index and search can be passed as individual parameters or as gzipped json, first try the
    # directly named parameters
    indexes = extract('indexes', parser=lambda i: i.split(','))
    search_body = extract('search', parser=json.loads)

    # then try the query body parameter
    query_body = extract('query', parser=parse_query_body)
    if query_body:
        search_body = query_body['search']
        indexes = query_body['indexes']

    # an index must be provided in one way or another
    if indexes is None:
        raise MissingIndex()

    return dict(
        indexes=[index.strip() for index in indexes],
        search_body=search_body,
    )


def extract_plot_parameters():
    """
    Extract the plot image parameters from the request.

    :return: a dict
    """
    return dict(
        point_radius=extract('point_radius', default=4, parser=int),
        point_colour=extract('point_colour', default=Color('#ee0000'), parser=parse_colour),
        border_width=extract('border_width', default=1, parser=int),
        border_colour=extract('border_colour', default=Color('#ffffff'), parser=parse_colour),
        resize_factor=extract('resize_factor', default=4, parser=int),
    )


def extract_gridded_parameters():
    """
    Extract the gridded image parameters from the request.

    :return: a dict
    """
    return dict(
        grid_resolution=extract('grid_resolution', default=8, parser=int),
        cold_colour=extract('cold_colour', default=Color('#f4f11a'), parser=parse_colour),
        hot_colour=extract('hot_colour', default=Color('#f02323'), parser=parse_colour),
        range_size=extract('range_size', default=12, parser=int),
        resize_factor=extract('resize_factor', default=4, parser=int),
    )


def extract_heatmap_parameters():
    """
    Extract the heatmap image parameters from the request.

    :return: a dict
    """
    return dict(
        point_radius=extract('point_radius', default=8, parser=int),
        cold_colour=extract('cold_colour', default=Color('#0000ee'), parser=parse_colour),
        hot_colour=extract('hot_colour', default=Color('#ee0000'), parser=parse_colour),
        intensity=extract('intensity', default=0.5, parser=float),
    )


def extract_plot_utf_grid_params():
    """
    Extract the UTFGrid parameters for plot requests from the request.

    :return: a dict
    """
    return dict(
        grid_resolution=extract('grid_resolution', default=4, parser=int),
        point_width=extract('point_width', default=3, parser=int),
    )


def extract_gridded_utf_grid_params():
    """
    Extract the UTFGrid parameters for gridded requests from the request.

    :return: a dict
    """
    return dict(
        grid_resolution=extract('grid_resolution', default=8, parser=int),
        point_width=extract('point_width', default=1, parser=int),
    )
