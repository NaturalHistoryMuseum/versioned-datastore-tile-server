#!/usr/bin/env python3

import io
import os
import random
import requests
from PIL import Image


def clamp(value, minimum, maximum):
    """
    Ensures the passed value is between the minimum and the maximum. If it is below the minimum then
    the passed minimum value is returned and if it is above the maximum the passed maximum value is
    returned.

    :param value: the value to clamp
    :param minimum: the minimum the value can be
    :param maximum: the maximum the value can be
    :return: minimum, maximum or value
    """
    return max(minimum, min(value, maximum))


def lat_lon_clamp(pair):
    """
    Clamp a pair of numbers to latitude and longitude min/max.

    :param pair: a pair of numbers representing a latitude and a longitude
    :return: a pair of numbers, guaranteed to be valid
    """
    return clamp(pair[0], -85.0511, 85.0511), clamp(pair[1], -180, 180)


def is_power_of_two(number):
    """
    Returns True if the number is a power of two and False if not.

    :param number: the number
    :return: True if the number is a power of two and False if not.
    """
    return number != 0 and number & (number - 1) == 0


def convert_to_png(image):
    """
    Renders an image object in the png format and returns the bytes in a BytesIO object.

    :param image: the image object
    :return: a BytesIO object
    """
    # save the image to a io buffer in png format
    buffer = io.BytesIO()
    image.save(buffer, format='png')
    # make sure we seek back to the start of the buffer otherwise no data will be read when the
    # buffer is next read from
    buffer.seek(0)
    return buffer


def get_openstreetmap_tile(x, y, z):
    """
    Returns a pillow image object of the given tile from Open Street Map.

    :param x: the tile's x coordinate
    :param y: the tile's y coordinate
    :param z: the tile's z coordinate
    :return: the image object
    """
    url = 'https://{server}.tile.openstreetmap.org/{z}/{x}/{y}.png'
    tile_url = url.format(server=random.choice('abc'), z=z, x=x, y=y)
    response = requests.get(tile_url)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def rebuild_data(parsed_data):
    """
    Rebuild the original data encoded by Splitgill.

    :param parsed_data: the parsed dict
    :return: the rebuilt data dict
    """
    # this doesn't need _ checks because you can't currently have parsed types at the
    # root level of the data dict
    return {key: rebuild_dict_or_list(value) for key, value in parsed_data.items()}


def rebuild_dict_or_list(value):
    """
    Rebuild a dict or a list inside the parsed dict.

    :param value: a dict which can either be for structure or a value, or a list of
                  either value or structure dicts
    :return: a dict, list, or value
    """
    if isinstance(value, dict):
        if "_u" in value:
            # this is a value dict, return the original value
            return value["_u"]
        else:
            # this is a structural dict, pass each value through this function but
            # filter out fields that start with an underscore, unless they are the
            # special _id field
            return {
                key: rebuild_dict_or_list(value)
                for key, value in value.items()
                if not key.startswith("_") or key == "_id"
            }
    elif isinstance(value, list):
        # pass each element of the list through this function
        return [rebuild_dict_or_list(element) for element in value]
    else:
        # failsafe: just return the value. This should only really happen with lists
        # containing Nones (which is technically allowed)
        return value
