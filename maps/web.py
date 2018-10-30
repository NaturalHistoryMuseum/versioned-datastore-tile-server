#!/usr/bin/env python3

from flask import Flask, send_file, request, jsonify

from maps.query import search
from maps.tiles import Tile
from maps.exceptions import InvalidRequestType, InvalidColour, MissingIndex

# it's flask time!
app = Flask(__name__)


def parse_colour(value):
    """
    Parse the given value into a 3 or 4-tuple RGB or RGBA value. Valid parameters:

        - a 3 or 4-tuple/list of ints
        - a hex string colour
        - a 3 or 4-tuple/list of ints, as a string (like '(255,255,255)' or '[255,255,255,255]')

    All int values should be in the range 0-255.

    :param value: the value to parse
    :return: a 3 or 4-tuple of ints
    """
    try:
        # if the value is a tuple or a list and its length is 3 or 4 (RGB or RGBA) just return it
        if isinstance(value, (tuple, list)) and len(value) in (3, 4):
            return tuple(map(int, value))
        if isinstance(value, str):
            value = value.strip()
            # if the string starts with a hash, assume hex colour value and convert to a RGB tuple
            if value[0] == '#':
                return tuple(int(value[i:i + 2], 16) for i in range(1, 6, 2))
            # if the string starts and ends with a bracket and has 2 or 3 commas in it, split the
            # contents by commas and create a tuple of RGB or RGBA values
            if value[0] in ('(', '[') and value[-1] in (')', ']') and value.count(',') in (2, 3):
                return tuple(map(int, value[1:-1].split(',')))
    except Exception as e:
        # if anything goes wrong, log a warning and then fall threw to the exception
        app.logger.warning(f'Failed to parse "{value}" as a colour', e)
    # if nothing matches (or an error occurs), chuck an error
    raise InvalidColour(value)


def extract_search_params():
    """
    Extract the search parameters from the request.

    :return: a dict
    """
    index = request.args.get('index', None)
    if index is None:
        raise MissingIndex()
    return dict(
        index=index.strip(),
        # TODO: do adaptive precision based on z?
        precision=int(request.args.get('precision', default=10)),
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
@app.route('/tiles/<int:z>/<int:x>/<int:y>.<string:request_type>')
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
        return send_file(tile.as_image(points, **extract_image_params()), mimetype='image/png')
    else:
        return jsonify(tile.as_grid(points, **extract_grid_params()))


if __name__ == "__main__":
    app.run(port=5000)
