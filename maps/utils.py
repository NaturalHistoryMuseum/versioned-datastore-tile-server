#!/usr/bin/env python3

from contextlib import suppress

from maps.exceptions import InvalidColour


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
    colour = None
    with suppress(ValueError, IndexError):
        # if the value is a tuple or a list and its length is 3 or 4 (RGB or RGBA) just return it
        if isinstance(value, (tuple, list)) and len(value) in (3, 4):
            colour = tuple(map(int, value))
        if isinstance(value, str):
            value = value.strip()
            # if the string starts with a hash, assume hex colour value and convert to a RGB tuple
            if value[0] == '#':
                colour = tuple(int(value[i:i + 2], 16) for i in range(1, 6, 2))
            # if the string starts and ends with a bracket and has 2 or 3 commas in it, split the
            # contents by commas and create a tuple of RGB or RGBA values
            if value[0] in ('(', '[') and value[-1] in (')', ']') and value.count(',') in (2, 3):
                colour = tuple(map(int, value[1:-1].split(',')))

    # if the colour has been extracted and it's valid, return it
    if colour is not None and min(colour) >= 0 and max(colour) <= 255:
        return colour

    # if nothing matches (or an error occurs), chuck an error
    raise InvalidColour(value)
