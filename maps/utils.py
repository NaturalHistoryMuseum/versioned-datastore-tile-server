#!/usr/bin/env python3

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


def is_power_of_two(number):
    """
    Returns True if the number is a power of two and False if not.

    :param number: the number
    :return: True if the number is a power of two and False if not.
    """
    return number != 0 and number & (number - 1) == 0
