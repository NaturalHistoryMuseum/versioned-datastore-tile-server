#!/usr/bin/env python3

import io
import math

from PIL import ImageDraw, Image

from maps.exceptions import GridNotPowerOfTwoException
from maps.utils import clamp, is_power_of_two


def longitude_to_x(longitude, zoom):
    """
    Converts a longitude value at a given zoom level to an x coordinate.

    :param longitude: the longitude value
    :param zoom: the zoom value
    :return: the x coordinate of the longitude at the given zoom
    """
    # treat out of range longitudes as if the map is wrapped around like a cylinder with the map on
    # the outside
    if longitude < -180 or longitude > 180:
        longitude = ((longitude + 180) % 360) - 180

    # scale the longitude onto the 360 degree scale and then multiply it by 2^zoom to convert it to
    # the correct position at the given zoom level
    return ((longitude + 180) / 360) * pow(2, zoom)


def latitude_to_y(latitude, zoom):
    """
    Converts a latitude value at a given zoom level to a y coordinate using the web mercator
    projection (EPSG:3857).

    :param latitude:
    :param zoom:
    :return:
    """
    # ensure the latitude is within the web mercator bounds
    latitude = clamp(latitude, -85.0511, 85.0511)

    # convert the latitude to a y coordinate. This is a blend of logic from the calculations on:
    # https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames but is essentially just the standard
    # web mercator translation
    # first convert to radians
    radians = math.radians(latitude)
    # then calculate the y value and apply the zoom
    return (1 - math.log(math.tan(radians) + 1 / math.cos(radians)) / math.pi) / 2 * pow(2, zoom)


def translate(x, y, z):
    """
    Translates the given tile x, y, z values into a latitude and longitude coordinate pair, pointing
    to the top left corner of the tile.

    :param x: the x coordinate
    :param y: the y coordinate
    :param z: the z coordinate
    :return: a tuple of the latitude and longitude of the top left corner of the tile, in degrees
    """
    # source: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_numbers_to_lon..2Flat._2
    zoom = pow(2, z)
    longitude_degrees = x / zoom * 360.0 - 180.0
    latitude_radians = math.atan(math.sinh(math.pi * (1 - 2 * y / zoom)))
    return math.degrees(latitude_radians), longitude_degrees


class PointCache:
    """
    A cache for points! It is much faster to render the different points we want to draw once and
    then paste them into the tiles we want to render. This class holds the points currently cached
    and creates new ones when they are requested for the first time.
    """

    def __init__(self):
        self.cache = {}

    def get_point(self, point_radius, border_width, resize_factor, point_colour, border_colour):
        """
        Given a set of parameters for the point, returns a point image to be used in the rendering
        of a tile. If the point has already been created we get it from the cache, otherwise we
        create a new one.

        :param point_radius: the total radius of the point (including border), in pixels
        :param border_width: the width of the border, in pixels
        :param resize_factor: the scaling that is going to be applied to the tile after rendering
                              all the points on it to smooth out the image (using anti-aliasing)
        :param point_colour: the colour of the point, this should be a tuple of 3 or 4 ints
                             representing the RGB(A) values on a scale from 0 to 255
        :param border_colour: the colour of the border, this should be a tuple of 3 or 4 ints
                              representing the RGB(A) values on a scale from 0 to 255
        :return: an image object containing the requested points
        """
        point_radius = int(point_radius)
        border_width = int(border_width)
        resize_factor = int(resize_factor)
        point_colour = tuple(map(int, point_colour))
        border_colour = tuple(map(int, border_colour))
        key = (point_radius, border_width, resize_factor, point_colour, border_colour)
        if key not in self.cache:
            self.cache[key] = self.create_point(*key)
        return self.cache[key]

    @staticmethod
    def create_point(point_radius, border_width, resize_factor, point_colour, border_colour):
        """
        Creates an image of a point to display on the map. This point is made up of two circles to
        create a red-filled circle with a white border.

        :param point_radius: the radius of the whole point in pixels (including the border)
        :param border_width: the width of the border in pixels
        :param resize_factor: the resize factor that will be applied when scaling the tile image
                              down and anti-aliasing
        :param point_colour: the colour of the point, this should be a tuple of 3 or 4 ints
                             representing the RGB(A) values on a scale from 0 to 255
        :param border_colour: the colour of the border, this should be a tuple of 3 or 4 ints
                             representing the RGB(A) values on a scale from 0 to 255
        :return: an image of the point
        """
        diameter = point_radius * 2 * resize_factor

        # create an image the size of the diameter of the point
        image = Image.new('RGBA', [diameter, diameter])
        draw = ImageDraw.Draw(image)

        # the image is exactly the diameter in width and height so range of possible x and y
        # coordinates is 0 <= x|y < diameter. Therefore, the "far side" is at diameter - 1, cache
        # this value here
        far_size = diameter - 1
        # scale the border width up by the resize factor
        scaled_border_width = border_width * resize_factor

        # draw the background circle in the border colour
        draw.ellipse([0, 0, far_size, far_size], fill=border_colour)
        # then draw a smaller foreground circle on top in the colour requested for the point
        draw.ellipse([scaled_border_width, scaled_border_width,
                      far_size - scaled_border_width, far_size - scaled_border_width],
                     fill=point_colour)

        # return the image we've created
        return image


class Tile(object):
    """
    Represents a tile in a map and holds functions relating to rendering the tile and calculating
    other values based on the tile.
    """

    # the cache of point images
    point_cache = PointCache()

    def __init__(self, x, y, z, tile_size=(256, 256)):
        self.x = x
        self.y = y
        self.z = z
        self.width, self.height = tile_size

    def as_image(self, points, point_radius, border_width, resize_factor, point_colour,
                 border_colour):
        """
        Renders the series of latitude and longitude points onto a tile using the point options to
        determine the size and colour of each point.

        :param points: an iterable of points to render, each element should be a tuple containing
                       the latitude and longitude values
        :param point_radius: the radius of the point, this is the whole radius in pixels, including
                             the border width
        :param border_width: the width in pixels of the border around the point
        :param resize_factor: the value to resize the tile by when rendering. The tile is rendered
                              at a higher resolution than the width/height requested and then scaled
                              down to the desired size. This means we can anti-alias the tile's
                              contents and get a smoother tile image.
        :param point_colour: the colour of the point, this should be a tuple of 3 or 4 ints
                             representing the RGB(A) values on a scale from 0 to 255
        :param border_colour: the colour of the point, this should be a tuple of 3 or 4 ints
                              representing the RGB(A) values on a scale from 0 to 255
        :return: the BytesIO object containing the byte data that makes up the png tile image
        """
        # create a new image object the size of the scaled up tile
        image = Image.new('RGBA', (self.width * resize_factor, self.height * resize_factor))
        # grab the point image we're going to use to render each point in the tile
        point_image = Tile.point_cache.get_point(point_radius, border_width, resize_factor,
                                                 point_colour, border_colour)
        # figure out the radius of the points we're going to render at the resize factor value
        scaled_radius = point_radius * resize_factor

        # loop through all the point pairs
        for latitude, longitude, _total in points:
            # translate to x and y coordinates within the tile's bounds
            x, y = self.translate_to_tile(latitude, longitude, resize_factor)
            # paste the point image at the x and y coordinates. Note that we can only paste at
            # integer positions and therefore we round the values up or down. This shouldn't make
            # the points too off their exact location given that we scale the image after adding all
            # them all
            image.paste(point_image, (round(x - scaled_radius), round(y - scaled_radius)),
                        mask=point_image)

        # if needed, resize the image and use antialiasing to smooth it out
        if resize_factor != 1:
            image = image.resize((self.width, self.height), resample=Image.ANTIALIAS)

        # save the image to a io buffer in png format
        buffer = io.BytesIO()
        image.save(buffer, format='png')
        # make sure we seek back to the start of the buffer otherwise no data will be read when the
        # buffer is next read from
        buffer.seek(0)
        # return the buffer
        return buffer

    def as_grid(self, points_with_count, grid_ratio, point_width):
        """
        Produces a dict of data about the points in this tile according to the UTFGrid specification
        for rasterized interaction data (https://github.com/mapbox/utfgrid-spec).

        A brief introduction to UTFGrid: essentially, the data in the returned dict defines the
        areas in the tile which can be interacted with. It does this using an array of strings
        to represent the tile's pixels (or more commonly, a group of pixels to limit the size of the
        UTFGrid JSON file and because pixel level interactivity granularity is probably unnecessary.
        There are `y` elements in the array and `x` characters in each string element, thus
        representing all areas in the entire `x*y` area. If a character is a space, there's no
        interaction in that area. If it's not a space then there is interaction in that area and the
        character in the position can be looked up in a map to see data about what is present in
        that area, in this case just a total of records at that location and the tile within which
        the point is contained.

        For more info on the specifics of implementing the spec and an example, see here:
        https://github.com/mapbox/utfgrid-spec/blob/master/1.3/utfgrid.md.

        :param points_with_count: an iterable of points with the total records at the point. This
                                  should be in the form (latitude, longitude, total).
        :param grid_ratio: the ratio of the grid to the tile. The recommended default is 0.25 which
                           means the standard 256x256 tile is split up into 4x4 areas. The grid
                           width and height have to be powers of 2
        :param point_width: the width of the points to mark - i.e. how precise we want interactions
                            to be. This works in combination with the grid size and also how big the
                            rendered points actually are. Default is 5 to allow a bit of wiggle room
                            for the user otherwise it's hard to interact exactly every time and
                            because the default rendered point size is 4
        :return: a dict of UTFGrid data for this tile
        """
        grid_width = int(self.width * grid_ratio)
        grid_height = int(self.height * grid_ratio)

        # nope!
        if not is_power_of_two(grid_width) or not is_power_of_two(grid_height):
            raise GridNotPowerOfTwoException(grid_width, grid_height)

        # create a blank grid to start with, filled with spaces. Note that in this grid variable the
        # rows are lists not strings, we'll join them before returning the data at the end. This is
        # done like this because lists are immutable whereas strings aren't
        grid = [[' ' for _i in range(grid_width)] for _j in range(grid_height)]
        # this will hold all the keys in use in the grid, note that the empty string is necessary
        # as it maps the empty areas that are designated with spaces
        keys = [""]
        # an empty data dict to start with
        data = {}

        # iterate through all the points
        for point_id, (latitude, longitude, total) in enumerate(points_with_count, start=1):
            # translate the latitude and longitude coordinate into an x and y coordinate within the
            # tile's bounds
            x, y = self.translate_to_tile(latitude, longitude, resize_factor=grid_ratio)
            # convert the point id to its character for the interaction map
            encoded_id = chr(self.encode_id(point_id))

            # we only add the point to keys and data if it is actually in the grid which isn't
            # guaranteed due to rounding and such, therefore keep track of whether the point is used
            marked = False
            # loop through all the exact characters in the grid to mark
            for x_to_mark, y_to_mark in self.get_points_to_mark(round(x), round(y), point_width):
                # if the x and y positions to mark are both within the grid, mark them
                if 0 <= x_to_mark < grid_width and 0 <= y_to_mark < grid_height:
                    # mark the position with the encoded point id
                    grid[y_to_mark][x_to_mark] = encoded_id
                    marked = True

            # only add the keys and data entries if the point appears in the grid
            if marked:
                # the point id is used as a string in both the keys list and the data dict so
                # convert it first
                string_point_id = str(point_id)
                # add it to the keys list
                keys.append(string_point_id)
                # add the data for the point
                data[string_point_id] = {
                    # TODO: tile? Is that useful here? Needed by ckanext-maps maybe?
                    '_tiledmap_count': f'total: {total}, tile: {self.z}/{self.x}/{self.y}'
                }

        # return the data we've produced
        return {
            # make each row a string not a list
            'grid': [''.join(row) for row in grid],
            'keys': keys,
            'data': data
        }

    def middle(self):
        """
        Returns the latitude and longitude of the middle of the tile.

        :return: returns a tuple containing the latitude and longitude
        """
        return translate(self.x + 0.5, self.y + 0.5, self.z)

    def bottom_left(self):
        """
        Returns the latitude and longitude of the bottom left of the tile.

        :return: returns a tuple containing the latitude and longitude
        """
        return translate(self.x, self.y + 1, self.z)

    def bottom_right(self):
        """
        Returns the latitude and longitude of the bottom right of the tile.

        :return: returns a tuple containing the latitude and longitude
        """
        return translate(self.x + 1, self.y + 1, self.z)

    def top_left(self):
        """
        Returns the latitude and longitude of the top left of the tile.

        :return: returns a tuple containing the latitude and longitude
        """
        return translate(self.x, self.y, self.z)

    def top_right(self):
        """
        Returns the latitude and longitude of the top right of the tile.

        :return: returns a tuple containing the latitude and longitude
        """
        return translate(self.x + 1, self.y, self.z)

    def longitude_to_tile_x(self, longitude, resize_factor):
        """
        Converts the longitude to an x coordinate relative to the tile's bounds.

        :param longitude: the longitude value
        :param resize_factor: the resize factor to be applied to the tile so that we can calculate
                              the x value correctly with respect to it
        :return: the x coordinate
        """
        # scale up the width using the resize factor
        width = self.width * resize_factor
        # convert the longitude we were passed into an x value on the whole map at this zoom level
        x = longitude_to_x(longitude, self.z)
        # convert the longitude of the centre of the tile into an x value on the whole map
        centre_x = longitude_to_x(self.middle()[1], self.z)
        # calculate the relative x value to the tile
        return (x - centre_x) * width + width / 2

    def latitude_to_tile_y(self, latitude, resize_factor):
        """
        Converts the latitude to a y coordinate relative to the tile's bounds.

        :param latitude: the latitude value
        :param resize_factor: the resize factor to be applied to the tile so that we can calculate
                              the y value correctly with respect to it
        :return: the y coordinate
        """
        # scale up the width using the resize factor
        height = self.height * resize_factor
        # convert the latitude we were passed into a y value on the whole map at this zoom level
        y = latitude_to_y(latitude, self.z)
        # convert the latitude of the centre of the tile into a y value on the whole map
        centre_y = latitude_to_y(self.middle()[0], self.z)
        # calculate the relative y value to the tile
        return (y - centre_y) * height + height / 2

    def translate_to_tile(self, latitude, longitude, resize_factor):
        """
        Translate the given latitude and longitude to an x, y coordinate pair within the tile, at a
        given a resize multiplier.

        :param latitude: the latitude of the point
        :param longitude: the longitude of the point
        :param resize_factor: the resize factor that will be applied by the tile when rendering
        :return: a tuple containing the x and y values
        """
        return (self.longitude_to_tile_x(longitude, resize_factor),
                self.latitude_to_tile_y(latitude, resize_factor))

    def encode_id(self, point_id):
        """
        Converts the point's integer id to an encoded id according to the UTFGrid specification.

        :param point_id: the integer point id
        :return: an integer id
        """
        encoded_id = point_id + 32
        if encoded_id >= 34:
            encoded_id += 1
        if encoded_id >= 92:
            encoded_id += 1
        return encoded_id

    def get_points_to_mark(self, x, y, point_width):
        """
        Returns a generator of x and y coordinates in the grid to mark for interactivity. The point
        width is used to create a diamond shaped area around the centre point (given by the
        parameters x, y) of points to mark. For example, if point_width was 5, the points yielded
        would form the following:

               #
              ###
             #####
              ###
               #

        :param x: the x point in the grid
        :param y: the y point in the grid
        :param point_width: how big the point in the interactivity grid should be
        :return: a generator which yields x,y pairs of points to mark
        """
        # do integer division on the width to determine how many positions out from the point's
        # origin position should be yielded and therefore marked
        offset = point_width // 2

        if offset:
            # lets build a diamond shape!
            for i in range(-offset, offset + 1):
                for j in range(-offset, offset + 1):
                    if abs(i) == offset and abs(j) == offset:
                        continue
                    yield x + i, y + j
        else:
            # the offset is 0, therefore just return the exact point
            yield x, y
