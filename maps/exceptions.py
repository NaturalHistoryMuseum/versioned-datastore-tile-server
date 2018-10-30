#!/usr/bin/env python3

from werkzeug.exceptions import HTTPException


class GridNotPowerOfTwoException(HTTPException):
    """
    Exception used to indicate that the grid width and height in use are invalid.
    """

    code = 400

    def __init__(self, grid_width, grid_height):
        super().__init__(f'Grid width ({grid_width}) and height ({grid_height}) must both be '
                         f'powers of two')


class InvalidRequestType(HTTPException):
    """
    Exception used to indicate that the request type was invalid.
    """

    code = 400

    def __init__(self, request_type):
        super().__init__(f'{request_type} is not a valid request type, must be png or grid.json')


class InvalidColour(HTTPException):
    """
    Exception used to indicate that one of the colour parameters could not be parsed.
    """

    code = 400

    def __init__(self, colour):
        super().__init__()
        self.colour = colour

    def get_description(self, environ=None):
        return (f"{self.colour} was not in a recognised format and could not be parsed as a "
                f"colour. Valid formats: </br><ul>"
                f"<li>a hex colour string starting with a hash, like: '#ff00ff'</li>"
                f"<li>a sequence of values between 0 and 255 representing RGB and A if "
                f"needed. The values should be comma seperated and enclosed in circular "
                f"or square brackets, for example '(255, 0, 255)' or '[255, 0, 255, 190]'"
                f"</li></ul>")


class MissingIndex(HTTPException):
    """
    Exception used to indicate that no resource was passed in the request.
    """

    code = 400

    def __init__(self):
        super().__init__('An index must be specified')
