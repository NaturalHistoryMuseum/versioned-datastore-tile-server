#!/usr/bin/env python3
import base64
import gzip
import json

from elasticsearch import Elasticsearch
from flask import Flask, send_file, request, jsonify

from maps.exceptions import InvalidRequestType, MissingIndex
from maps.query import search
from maps.tiles import Tile
from maps.utils import parse_colour

# it's flask time!
app = Flask(__name__)
# load the default config settings
app.config.from_object('maps.config')
# load any settings from the config file pointed at by the maps_config environment variable
app.config.from_envvar('maps_config')

app.client = Elasticsearch(hosts=app.config['ELASTICSEARCH_HOSTS'], sniff_on_start=True,
                           sniff_on_connection_fail=True, sniffer_timeout=60, sniff_timeout=10,
                           http_compress=False)


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
    indexes = request.args.get('indexes', None)
    search_body = request.args.get('search', None)
    if search_body:
        search_body = json.loads(search_body)

    # then try the query body parameter
    query_body = request.args.get('query', None)
    if query_body:
        query_body = json.loads(gzip.decompress(base64.urlsafe_b64decode(query_body)))
        search_body = query_body['search']
        indexes = query_body['indexes']

    # an index must be provided in one way or another
    if indexes is None:
        raise MissingIndex()

    # if the index is a string then attempt to split it on commas to allow multi-index searching
    if isinstance(indexes, str):
        indexes = indexes.split(',')

    return dict(
        index=[index.strip() for index in indexes],
        search_body=search_body,
    )


def extract_image_params():
    """
    Extract the image parameters from the request.

    :return: a dict
    """
    return dict(
        point_radius=int(request.args.get('point_radius', default=4)),
        border_width=int(request.args.get('border_width', default=1)),
        resize_factor=int(request.args.get('resize_factor', default=4)),
        point_colour=parse_colour(request.args.get('point_colour', default=(238, 0, 0))),
        border_colour=parse_colour(request.args.get('border_colour', default=(255, 255, 255))),
    )


def extract_grid_params():
    """
    Extract the grid parameters from the request.

    :return: a dict
    """
    return dict(
        grid_ratio=float(request.args.get('grid_ratio', default=0.25)),
        point_width=int(request.args.get('point_width', default=5)),
    )


# TODO: store/expose request/response stats somewhere for monitoring?
@app.route('/<int:z>/<int:x>/<int:y>.<string:request_type>')
def get(x, y, z, request_type):
    """
    Handles tile image and UTFGrid requests.

    :param x: the tile's x value
    :param y: the tile's y value
    :param z: the tile's z value
    :param request_type: the request type, this should be either `png` or `grid.json`
    :return: either a png image or a json document
    """
    if request_type != 'png' and request_type != 'grid.json':
        raise InvalidRequestType(request_type)

    tile = Tile(x, y, z)

    # query elasticsearch, this will return a list of buckets containing locations and counts in
    # ascending count order
    points = search(tile, **extract_search_params())
    if request_type == 'png':
        response = send_file(tile.as_image(points, **extract_image_params()), mimetype='image/png')
    else:
        response = jsonify(tile.as_grid(points, **extract_grid_params()))
    # ahhh cors
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
