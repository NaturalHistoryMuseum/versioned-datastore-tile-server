#!/usr/bin/env python3

from PIL import Image

from maps.tiles import Tile
from maps.tiles.points import draw_point
from maps.utils import convert_to_png, rebuild_data


class PlotTile(Tile):
    """
    The plot tile style renders a single coloured point with a border for each point in the tile.
    """
    style = 'plot'

    def as_image(self, buckets, *args, **kwargs):
        return self.render(buckets, *args, **kwargs)

    def render(self, buckets, point_radius, point_colour, border_width, border_colour,
               resize_factor):
        """
        Renders the series of buckets onto a tile using the point options to determine the size and
        colour of each point.

        :param buckets: an iterable buckets to render, each element should be a BucketResult object
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

        for bucket in buckets:
            # translate to x and y coordinates within the tile's bounds
            x, y = self.translate_to_tile(bucket.centre_latitude, bucket.centre_longitude,
                                          resize_factor)
            # paste the point image at the x and y coordinates. Note that we can only paste at
            # integer positions and therefore we round the values up or down. This shouldn't make
            # the points too off their exact location given that we scale the image after adding all
            # them all
            image.paste(point_image, (round(x - scaled_radius), round(y - scaled_radius)),
                        mask=point_image)

        # if needed, resize the image and use antialiasing to smooth it out
        if resize_factor != 1:
            image = image.resize((self.width, self.height), resample=Image.LANCZOS)

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
        cell_ratio = (self.width // grid_resolution) / self.width

        for bucket in buckets:
            # translate the latitude and longitude coordinate into an x and y coordinate within the
            # tile's bounds with respect to the size of the grid
            x, y = self.translate_to_tile(bucket.centre_latitude, bucket.centre_longitude,
                                          cell_ratio)

            point_data = {
                'count': bucket.total,
                'data': rebuild_data(bucket.first_record['data']),
            }

            point_data.update({
                # use the centre lat and lon of the bucket
                'record_latitude': bucket.centre_latitude,
                'record_longitude': bucket.centre_longitude,
                # return a filter value that if it was used as part of a further geo
                # query filter (i.e. __geo__) it would be understood by the versioned
                # datastore backend and would restrict any results to the points in this
                # bucket
                'geo_filter': bucket.as_geo_json_bbox()
            })

            yield point_data, x, y
