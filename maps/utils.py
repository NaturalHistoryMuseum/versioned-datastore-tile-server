#!/usr/bin/env python3

import io


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
