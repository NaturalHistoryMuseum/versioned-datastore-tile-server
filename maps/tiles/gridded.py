#!/usr/bin/env python3

import bisect
import math

from PIL import Image

from maps.tiles import Tile
from maps.tiles.points import draw_point
from maps.utils import convert_to_png


class GriddedTile(Tile):
    """
    The gridded tile style renders a single coloured point representing a group of buckets within a
    certain area in the tile. This is done by grouping the buckets into something like an 8x8 grid,
    for example. The point colour represents the number of records in the group.
    """
    style = 'gridded'

    @staticmethod
    def assign_colour(count, cold_colour, hot_colour, range_size):
        """
        Assign a colour in the colour range from the cold colour to the hot colour based on the
        count. The range of colours is linear, however the assignment is exponential so that we can
        assign useful colours without knowing the real range of the counts.

        If the count is 0, None is returned

        :param count: the count
        :param cold_colour: the colour to assign to the lowest count (1)
        :param hot_colour: the colour to assign to the highest count (unknown as there is no upper
                           limit)
        :param range_size: the number of colours to include in the range from cold to hot, inclusive
        :return: None or a colour object
        """
        if count == 0:
            return None

        colours = list(cold_colour.range_to(hot_colour, range_size + 1))
        thresholds = [int(math.exp(i)) for i in range(range_size)]
        return colours[bisect.bisect_left(thresholds, count)]

    def group_buckets(self, buckets, grid_resolution):
        """
        Given a list of buckets, groups them into cells according to the size of the grid (given by
        the grid_resolution parameter). A list of lists is returned where each element is a row and
        each element within that is a 2-tuple containing the total records and the first record in
        the cell.

        :param buckets: a list of BucketResult objects
        :param grid_resolution: the resolution of the grid, i.e. how big each cell in the grid
                                within the tile is. For example, if set to 4 then the returned grid
                                will be 64x64. This value must result in a grid size that is a power
                                of 2.
        :return: a list of lists
        """
        grid_size = self.width // grid_resolution
        cell_ratio = (self.width // grid_resolution) / self.width

        # build a blank grid first
        grid = []
        for y in range(grid_size):
            row = []
            for x in range(grid_size):
                row.append([0, None])
            grid.append(row)

        # assign each bucket a cell in the grid and add its count to the total
        for bucket in buckets:
            # translate to x and y coordinates within the tile's bounds on the grid's scale
            x, y = self.translate_to_tile(bucket.centre_latitude, bucket.centre_longitude,
                                          cell_ratio)

            # ignore out of bounds points
            if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
                continue

            # round down to ensure ints as well as correct grouping
            x = int(x)
            y = int(y)

            # add the data to the grid
            grid[y][x][0] += bucket.total
            # set the first if it hasn't already been set
            if grid[y][x][1] is None:
                grid[y][x][1] = bucket.first_record

        return grid

    def as_image(self, buckets, *args, **kwargs):
        return self.render(buckets, *args, **kwargs)

    def render(self, buckets, grid_resolution, cold_colour, hot_colour, range_size, resize_factor):
        """
        Renders the series of buckets onto a grid, weighing the colour of the bucket in each cell of
        the grid using the total count of records in it.

        :param buckets: a list of BucketResult objects
        :param grid_resolution: the resolution of the grid, i.e. how big in pixels each cell should
                                be
        :param cold_colour: the colour to assign to the lowest count (1)
        :param hot_colour: the colour to assign to the highest count (unknown as there is no upper
                           limit)
        :param range_size: the number of colours to include in the range from cold to hot, inclusive
        :param resize_factor: the value to resize the tile by when rendering. The tile is rendered
                              at a higher resolution than the width/height requested and then scaled
                              down to the desired size. This means we can anti-alias the tile's
                              contents and get a smoother tile image.
        :return: a BytesIO object containing a png image
        """
        point_radius = grid_resolution // 2

        # create a new image object the size of the scaled up tile
        image = Image.new('RGBA', (self.width * resize_factor, self.height * resize_factor))

        for y, row in enumerate(self.group_buckets(buckets, grid_resolution)):
            for x, (count, _first) in enumerate(row):
                colour = self.assign_colour(count, cold_colour, hot_colour, range_size)
                if colour is None:
                    continue
                point_image = draw_point(point_radius, colour.hex, resize_factor=resize_factor)
                image.paste(point_image, (round((x * grid_resolution * resize_factor)),
                                          round((y * grid_resolution * resize_factor))),
                            mask=point_image)

        # if needed, resize the image and use antialiasing to smooth it out
        if resize_factor != 1:
            image = image.resize((self.width, self.height), resample=Image.ANTIALIAS)

        return convert_to_png(image)

    def get_marks(self, buckets, grid_resolution):
        """
        Returns a generator of coordinates to be marked in the UTFGrid produced by the as_grid
        function. Each element yielded is a 3-tuple of a point data dict, x, and y where the point
        data dict is the data dict to associate with the x and y coordinate in the utf grid result,
        and x and y are the cell coordinates within the grid.

        :param buckets: a list of BucketResult objects
        :param grid_resolution: the resolution of the grid, i.e. how big each cell in the grid
                                within the tile is. For example, if set to 4 then the returned grid
                                will be 64x64. This value must result in a grid size that is a power
                                of 2.
        :return: an iterable where each element is a 3-tuple of point data, x, and y
        """
        for y, row in enumerate(self.group_buckets(buckets, grid_resolution)):
            for x, (total, first) in enumerate(row):
                if total == 0:
                    continue
                # use the lat/long from the first record in this group. It would be nicer to use the
                # centre of the cell but it's probably not worth the time it would take to calculate
                # this
                latitude, longitude = map(float, first['meta']['geo'].split(','))

                point_data = {
                    'count': total,
                    'data': first['data'],
                    'record_latitude': latitude,
                    'record_longitude': longitude,
                }

                yield point_data, x, y
