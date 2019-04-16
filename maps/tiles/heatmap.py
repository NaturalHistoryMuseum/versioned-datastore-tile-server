#!/usr/bin/env python3

import math

from PIL import Image, ImageFilter

from maps.tiles import Tile
from maps.tiles.points import draw_heatmap_point
from maps.utils import clamp, convert_to_png


class HeatmapTile(Tile):
    """
    The heatmap tile style renders a more overall picture by blending the buckets out across the
    tile with areas where there are lots of records at the red end of the spectrum and areas where
    there are smaller numbers of records at the blue end of the spectrum.
    """
    style = 'heatmap'

    def as_image(self, buckets, *args, **kwargs):
        return self.render(buckets, *args, **kwargs)

    def render(self, buckets, point_radius, cold_colour, hot_colour, intensity):
        # create the colour range from blue through to red. This range has the same number of
        # colours in it as the allowed alpha range (i.e. 256 distinct values). This importantly
        # includes (0, 0, 0, 0) in index 0
        colour_range = [tuple(int(n * 255) for n in colour.get_rgb()) + (i,)
                        for i, colour in enumerate(cold_colour.range_to(hot_colour, 256))]

        point_diameter = point_radius * 2

        # create a new image object the size of the scaled up tile
        image = Image.new('RGBA', (self.width + (point_diameter * 2),
                                   self.height + (point_diameter * 2)))

        # loop through all the point pairs
        for bucket in buckets:
            # translate to x and y coordinates within the tile's bounds
            x, y = self.translate_to_tile(bucket.centre_latitude, bucket.centre_longitude, 1)
            # clamp the log of the total to the 1-10 range. This prevents us from giving huge totals
            # too much importance and ensures all totals are represented sensibly
            weight = clamp(int(math.log(bucket.total)), 1, 10)
            point = draw_heatmap_point(point_radius, weight, intensity)
            # merge it into the image at the position required. The translated the coordinates are
            # to ensure we draw the point in the right place (this is a simplified version of
            # (x - point_radius + point_diameter) where (x - point_radius) offsets the location to
            # ensure the middle of the point we draw is on the x, y coordinate and then the
            # (+ point_diameter) moves it to the right place on our shifted tile. Therefore we can
            # just use (+ point_radius)
            image.alpha_composite(point, (round(x + point_radius), round(y + point_radius)))

        # retrieve the alpha channel from the image we've created and loop through it producing a
        # new list of RGBA values from our lookup dict
        data = [colour_range[alpha] for alpha in image.getdata(3)]
        # replace the image with the new data
        image.putdata(data)

        # smooth the image to make it look nicer
        image = image.filter(ImageFilter.SMOOTH_MORE)
        # and then crop it to the tile size
        image = image.crop((point_diameter, point_diameter, self.width + point_diameter,
                            self.height + point_diameter))

        return convert_to_png(image)

    def as_grid(self, points, grid_resolution, point_width):
        """
        No UTFGrid for heatmaps, wouldn't really make much sense? We could do it. Meh.
        """
        return {}
