#!/usr/bin/env python3

from werkzeug.exceptions import HTTPException


class GridNotPowerOfTwoException(HTTPException):
    """
    Exception used to indicate that the grid width in use is invalid.
    """

    code = 400

    def __init__(self, grid_width):
        super().__init__('Grid size ({}) must a be power of two'.format(grid_width))


class InvalidRequestType(HTTPException):
    """
    Exception used to indicate that the request type was invalid.
    """

    code = 400

    def __init__(self, request_type):
        super().__init__('{} is not a valid request type, must be png or grid.json'.format(
            request_type))


class InvalidColour(HTTPException):
    """
    Exception used to indicate that one of the colour parameters could not be parsed.
    """

    code = 400

    def __init__(self, error):
        super().__init__(str(error))


class MissingIndex(HTTPException):
    """
    Exception used to indicate that no resource was passed in the request.
    """

    code = 400

    def __init__(self):
        super().__init__('An index must be specified')


class InvalidStyle(HTTPException):
    """
    Exception used to indicate that the style was invalid.
    """

    code = 400

    def __init__(self, style):
        super().__init__('{} is not a valid style, must be plot, gridded or heatmap'.format(style))
