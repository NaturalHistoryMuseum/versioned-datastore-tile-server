#!/usr/bin/env python3

from PIL import Image

from maps.tiles import Tile
from maps.tiles.points import draw_point
from maps.utils import convert_to_png


class PlotTile(Tile):
    """
    The plot tile style renders a single coloured point with a border for each point in the tile.
    """
    style = 'plot'

    def as_image(self, points, *args, **kwargs):
        return self.render(points, *args, **kwargs)

    def render(self, points, point_radius, point_colour, border_width, border_colour,
               resize_factor):
        """
        Renders the series of latitude and longitude points onto a tile using the point options to
        determine the size and colour of each point.

        :param points: an iterable of points to render, each element should be a tuple containing
                       the latitude and longitude values
        :param point_radius: the radius of the point, this is the whole radius in pixels, including
                             the border width
        :param point_colour: the colour of the point, this should be a tuple of 3 or 4 ints
                             representing the RGB(A) values on a scale from 0 to 255
        :param border_width: the width in pixels of the border around the point
        :param border_colour: the colour of the point, this should be a tuple of 3 or 4 ints
                              representing the RGB(A) values on a scale from 0 to 255
        :param resize_factor: the value to resize the tile by when rendering. The tile is rendered
                              at a higher resolution than the width/height requested and then scaled
                              down to the desired size. This means we can anti-alias the tile's
                              contents and get a smoother tile image.
        :return: the BytesIO object containing the byte data that makes up the png tile image
        """
        # create a new image object the size of the scaled up tile
        image = Image.new('RGBA', (self.width * resize_factor, self.height * resize_factor))
        # pre-render the point image we're going to use to render each point in the tile
        point_image = draw_point(point_radius, point_colour.hex, border_width, border_colour.hex,
                                 resize_factor)
        # figure out the radius of the points we're going to render at the resize factor value
        scaled_radius = point_radius * resize_factor

        for latitude, longitude, _total, _first in points:
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

        return convert_to_png(image)

    def get_marks(self, points, grid_resolution):
        """
        Returns a generator of coordinates to be marked in the UTFGrid produced by the as_grid
        function. Each element yielded is a 6-tuple of latitude, longitude, x, y, total and first,
        where latitude and longitude mark the real world points of the mark, x and y mark the cell
        coordinates within the grid, total is the total number of records at the mark and first
        represents the first record found at the mark.

        :param points: a list of 4-tuples, each containing the latitude, longitude, total records at
                       the coordinate and the first record at the coordinate
        :param grid_resolution: the resolution of the grid, i.e. how big each cell in the grid
                                within the tile is. For example, if set to 4 then the returned grid
                                will be 64x64. This value must result in a grid size that is a power
                                of 2.
        :return: an iterable where each element is a 6-tuple of latitude, longitude, x, y, total and
                 first
        """
        cell_ratio = (self.width // grid_resolution) / self.width

        for latitude, longitude, total, first in points:
            # translate the latitude and longitude coordinate into an x and y coordinate within the
            # tile's bounds with respect to the size of the grid
            x, y = self.translate_to_tile(latitude, longitude, cell_ratio)
            yield latitude, longitude, x, y, total, first
