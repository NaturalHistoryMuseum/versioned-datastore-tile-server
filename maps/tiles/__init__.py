#!/usr/bin/env python3

import abc
import itertools
import math

from maps.exceptions import GridNotPowerOfTwoException
from maps.utils import clamp, is_power_of_two


class Tile(metaclass=abc.ABCMeta):
    """
    Represents a tile in a map and holds functions relating to rendering the tile and calculating
    other values based on the tile.
    """
    # the style name of this tile
    style = None

    def __init__(self, x, y, z, tile_size=256):
        """
        :param x: tile x coordinate (left edge)
        :param y: tile y coordinate (top edge)
        :param z: tile zoom level
        :param tile_size: the size of the tile (will be used as width and height, tiles have to be
                          square)
        """
        self.x = x
        self.y = y
        self.z = z
        self.width = tile_size
        self.height = tile_size

    def as_image(self, points, *args, **kwargs):
        """
        Renders the passed points within the tile as a png image and returns the data as an BytesIO
        object.

        :param points: a list of 4-tuples, each containing the latitude, longitude, total records at
                       the coordinate and the first record at the coordinate
        :return: a BytesIO object containing a png image
        """
        pass

    def as_grid(self, points, grid_resolution, point_width):
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
        that area.

        For more info on the specifics of implementing the spec and an example, see here:
        https://github.com/mapbox/utfgrid-spec/blob/master/1.3/utfgrid.md.

        :param points: a list of 4-tuples, each containing the latitude, longitude, total records at
                       the coordinate and the first record at the coordinate
        :param grid_resolution: the resolution of the grid, i.e. how big each cell in the grid
                                within the tile is. For example, if set to 4 then the returned grid
                                will be 64x64. This value must result in a grid size that is a power
                                of 2 (and will error if it isn't).
        :param point_width: the width of the points to mark - i.e. how precise we want interactions
                            to be. This works in combination with the grid resolution and also how
                            big the png tile rendered points actually are.
        :return: a dict of UTFGrid data for this tile
        """
        grid_size = self.width // grid_resolution

        # nope!
        if not is_power_of_two(grid_size):
            raise GridNotPowerOfTwoException(grid_size)

        # create a blank grid to start with, filled with spaces. Note that in this grid variable the
        # rows are lists not strings, we'll join them before returning the data at the end
        grid = [[' ' for _i in range(grid_size)] for _j in range(grid_size)]
        # this will hold all the keys in use in the grid, note that the empty string is necessary
        # as it maps the empty areas that are designated with spaces
        keys = [""]
        # an empty data dict to start with
        data = {}
        # each point that makes it into the returned grid must have an id, this generates them
        point_id_generator = self.get_point_id_generator()

        for latitude, longitude, x, y, total, first in self.get_marks(points, grid_resolution):
            # keep track of the grid coordinates we want to mark for this point
            to_mark = []
            # loop through all the points in the grid to mark
            for x_to_mark, y_to_mark in self.get_points_to_mark(round(x), round(y), point_width):
                # the x and y positions must be in the grid otherwise we don't mark them
                if 0 <= x_to_mark < grid_size and 0 <= y_to_mark < grid_size:
                    to_mark.append((y_to_mark, x_to_mark))

            if to_mark:
                # there are points to mark, so generate the point ids required
                point_id, encoded_id = next(point_id_generator)

                # mark the position with the encoded point id
                for y_to_mark, x_to_mark in to_mark:
                    grid[y_to_mark][x_to_mark] = encoded_id

                # add the point_id to the keys list
                keys.append(point_id)

                if total == 1:
                    # extract the actual record coordinates
                    report_latitude, report_longitude = map(float, first['meta']['geo'].split(','))
                else:
                    # otherwise use the group coordinates
                    report_latitude, report_longitude = latitude, longitude

                # add the data for the point
                data[point_id] = {
                    'count': total,
                    'data': first['data'],
                    'record_latitude': report_latitude,
                    'record_longitude': report_longitude,
                    # return a filter value that if it was used as part of a further geo query
                    # filter (i.e. __geo__) it would be understood by the versioned datastore
                    # backend and would restrict any results to the point(s) at this lat/long pair
                    'geo_filter': {
                        # we'll use a point for this as it'll be more accurate than calculating a
                        # estimating a bounding box size and passing a Polygon
                        "type": "Point",
                        # note the reversal of these points cause this is GeoJSON
                        "coordinates": [report_longitude, report_latitude],
                        # use a tight distance to ensure we only get these points in any future
                        # searches
                        "distance": "1m"
                    }
                }

        return {
            # make each row a string not a list
            'grid': [''.join(row) for row in grid],
            'keys': keys,
            'data': data
        }

    def get_marks(self, points, grid_resolution):
        """
        Returns an iterable of coordinates to be marked in the UTFGrid produced by the as_grid
        function. Each element of the iterable must be a 6-tuple of latitude, longitude, x, y, total
        and first, where latitude and longitude mark the real world points of the mark, x and y mark
        the cell coordinates within the grid, total is the total number of records at the mark and
        first represents the first record found at the mark.

        :param points: a list of 4-tuples, each containing the latitude, longitude, total records at
                       the coordinate and the first record at the coordinate
        :param grid_resolution: the resolution of the grid, i.e. how big each cell in the grid
                                within the tile is. For example, if set to 4 then the returned grid
                                will be 64x64. This value must result in a grid size that is a power
                                of 2.
        :return: an iterable where each element is a 6-tuple of latitude, longitude, x, y, total and
                 first
        """
        return []

    def longitude_to_x(self, longitude):
        """
        Converts a longitude value at the tile's zoom level to an x coordinate using the web
        mercator projection (EPSG:3857).

        :param longitude: the longitude value
        :return: the x coordinate of the longitude at the given zoom
        """
        # treat out of range longitudes as if the map is wrapped around like a cylinder with the map
        # on the outside
        if longitude < -180 or longitude > 180:
            longitude = ((longitude + 180) % 360) - 180

        # scale the longitude onto the 360 degree scale and then multiply it by 2^zoom to convert it
        # to the correct position at the given zoom level
        return ((longitude + 180) / 360) * (2 ** self.z)

    def latitude_to_y(self, latitude):
        """
        Converts a latitude value at the tile's zoom level to a y coordinate using the web mercator
        projection (EPSG:3857).

        :param latitude: the latitude value
        :return: the y coordinate of the latitude at the given zoom
        """
        # ensure the latitude is within the web mercator bounds
        latitude = clamp(latitude, -85.0511, 85.0511)

        # convert the latitude to a y coordinate. This is a blend of logic from the calculations on:
        # https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames but is essentially just the
        # standard web mercator translation
        radians = math.radians(latitude)
        zoom = 2 ** self.z
        return (1 - math.log(math.tan(radians) + 1 / math.cos(radians)) / math.pi) / 2 * zoom

    def translate(self, x_extra=0, y_extra=0):
        """
        Translates the tile's x, y, z values into a latitude and longitude coordinate pair, pointing
        to the top left corner of the tile. The x_extra and y_extra parameters allow offsets to be
        applied to the tile's x and y values before translation.

        :param x_extra: an offset to be added to the tile's x coordinate
        :param y_extra: an offset to be added to the tile's y coordinate
        :return: a tuple of the latitude and longitude of the top left corner of the tile, in
                 degrees
        """
        # basically the same as the code at:
        # https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_numbers_to_lon..2Flat._2
        zoom = 2 ** self.z
        longitude_degrees = (self.x + x_extra) / zoom * 360.0 - 180.0
        latitude_radians = math.atan(math.sinh(math.pi * (1 - 2 * (self.y + y_extra) / zoom)))
        return math.degrees(latitude_radians), longitude_degrees

    def middle(self):
        """
        Returns the latitude and longitude of the middle of the tile.

        :return: returns a tuple containing the latitude and longitude
        """
        return self.translate(0.5, 0.5)

    def bottom_left(self, extra=0):
        """
        Returns the latitude and longitude of the bottom left of the tile.

        :param extra: an extra value to account into the x,y position before translation to latitude
                      and longitude. This is useful if slightly more context around the tile is
                      required. Defaults to 0.
        :return: returns a tuple containing the latitude and longitude
        """
        return self.translate(-extra, 1 + extra)

    def bottom_right(self, extra=0):
        """
        Returns the latitude and longitude of the bottom right of the tile.

        :param extra: an extra value to account into the x,y position before translation to latitude
                      and longitude. This is useful if slightly more context around the tile is
                      required. Defaults to 0.
        :return: returns a tuple containing the latitude and longitude
        """
        return self.translate(1 + extra, 1 + extra)

    def top_left(self, extra=0):
        """
        Returns the latitude and longitude of the top left of the tile.

        :param extra: an extra value to account into the x,y position before translation to latitude
                      and longitude. This is useful if slightly more context around the tile is
                      required. Defaults to 0.
        :return: returns a tuple containing the latitude and longitude
        """
        return self.translate(-extra, -extra)

    def top_right(self, extra=0):
        """
        Returns the latitude and longitude of the top right of the tile.

        :param extra: an extra value to account into the x,y position before translation to latitude
                      and longitude. This is useful if slightly more context around the tile is
                      required. Defaults to 0.
        :return: returns a tuple containing the latitude and longitude
        """
        return self.translate(1 + extra, -extra)

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
        x = self.longitude_to_x(longitude)
        # convert the longitude of the centre of the tile into an x value on the whole map
        centre_x = self.longitude_to_x(self.middle()[1])
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
        y = self.latitude_to_y(latitude)
        # convert the latitude of the centre of the tile into a y value on the whole map
        centre_y = self.latitude_to_y(self.middle()[0])
        # calculate the relative y value to the tile
        return (y - centre_y) * height + height / 2

    def translate_to_tile(self, latitude, longitude, resize_factor):
        """
        Translate the given latitude and longitude to an x, y coordinate pair within the tile, at a
        given a resize multiplier. A return of (0, 0) would be the top left corner of the tile.

        :param latitude: the latitude of the point
        :param longitude: the longitude of the point
        :param resize_factor: the resize factor that will be applied by the tile when rendering
        :return: a tuple containing the x and y values
        """
        return (self.longitude_to_tile_x(longitude, resize_factor),
                self.latitude_to_tile_y(latitude, resize_factor))

    @staticmethod
    def get_point_id_generator():
        """
        Generates sequential point ids and their encoded counterparts according to the UTFGrid
        specification.

        :return: a 2-tuple containing an str id and an char encoded id
        """
        for point_id in itertools.count(start=1):
            encoded_id = point_id + 32
            if encoded_id >= 34:
                encoded_id += 1
            if encoded_id >= 92:
                encoded_id += 1
            yield str(point_id), chr(encoded_id)

    @staticmethod
    def get_points_to_mark(x, y, point_width):
        """
        Returns a generator of x and y coordinates in the grid to mark for interactivity. The point
        width is used to create a diamond shaped area around the centre point (given by the
        parameters x, y) of points to mark. For example, if point_width was 5, the points yielded
        would form the following around the centre x, y point:

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

    def calculate_precision(self):
        """
        Calculate the precision to be used in the elasticsearch geo_hash aggregation based on the z
        value of this tile. See the elasticsearch doc for info about the possible values and their
        meaning.

        The precision values assigned to each zoom level have been chosen based on a few factors:

            - the estimated sizes of each tile at the given zoom level
            - the estimated cell dimensions produced by each precision value
            - how the precision looks when it's actually rendered (mainly whether it looks griddy or
              not)
            - what a reasonable number of points in each tile could be (the more points, the lower
              the precision could be otherwise our geo hash will miss off points due to the size
              limit)

        Choosing values is fairly subjective and therefore after playing around with the specimens
        resource its more than a million points, the values in this function were chosen. The basic
        principle of the values below is that when you're zoomed out and a tile is several hundred
        kilometres wide, two points a few metres apart will appear as the same point and therefore
        we can aggregate them without the user noticing. However, when you zoom in these points
        should be split apart as your tile resolution increases. This is a performance trick to
        avoid having to render thousands and thousands of points on top of each other at the macro
        level which would be a waste of time, but still allow us to render exact locations (or at
        least within a few centimeters) at the micro level.

        :return: a precision value between 1 and 12
        """
        # typical web mercator maps have a z range from 0-19
        return {
            0: 3,
            1: 3,
            2: 4,
            3: 4,
            4: 5,
            5: 5,
            6: 6,
            7: 6,
            8: 7,
            9: 7,
            10: 8,
            11: 9,
            12: 9,
            13: 10,
            14: 10,
            15: 11,
            16: 11,
            17: 11,
            18: 12,
            19: 12,
        }[clamp(self.z, 0, 19)]
