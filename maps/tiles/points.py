#!/usr/bin/env python3

import functools
import math

from PIL import Image, ImageDraw


@functools.lru_cache()
def draw_point(point_radius, colour, border_width=None, border_colour=None, resize_factor=1):
    """
    Creates an image of a point to display on the map. If a border is required then both the
    border_width and border_colour parameters should be provided.

    :param point_radius: the radius of the whole point in pixels (including any border if given)
    :param colour: the colour of the point, this should be in a form that pillow can accept
    :param border_width: the width of the border to draw in pixels, or None if no border should be
                         drawn (default: None)
    :param border_colour: the colour of the border, this should be in a form that pillow can accept,
                          or None to indicate that no border should be drawn (default: None)
    :param resize_factor: the resize factor that will be applied when scaling the tile image
                          down and smoothing with anti-aliasing meaning the point returned will be
                          point_radius * resize_factor (default: 1)
    :return: an image of the point
    """
    diameter = point_radius * 2 * resize_factor

    # create an image the size of the diameter of the point
    image = Image.new('RGBA', [diameter, diameter])
    draw = ImageDraw.Draw(image)

    # the image is exactly the diameter in width and height so the range of possible x and y
    # coordinates is 0 <= x|y < diameter. Therefore, the "far side" is at diameter - 1, cache
    # this value here for reuse
    far_side = diameter - 1

    if border_width and border_colour:
        # scale the border width up by the resize factor
        scaled_border_width = border_width * resize_factor
        # draw a background circle in the border colour
        draw.ellipse([0, 0, far_side, far_side], fill=border_colour)
        # then draw a smaller foreground circle on top in the colour requested for the point
        draw.ellipse([scaled_border_width, scaled_border_width,
                      far_side - scaled_border_width, far_side - scaled_border_width], fill=colour)
    else:
        # draw the circle in the colour
        draw.ellipse([0, 0, far_side, far_side], fill=colour)

    return image


@functools.lru_cache()
def draw_heatmap_point(radius, weight, intensity):
    """
    Creates a point that can be used to create heatmaps. The image produced is black circle* where
    the transparency increases as you get further from the centre. The transparency values are
    multiplied by the weight to achieve a darker or lighter point.

    *the result is actually a square but because of the way the alpha reduction is calculated it
    looks like a circle.

    :param radius: the radius of the point to create
    :param weight: the weight to multiply the alpha value by
    :param intensity: the intensity of the heatmap, this can have a dramatic impact on the resulting
                      image and usually requires a change in weight input calculation and/or point
                      radius
    :return: the image of the heatmap point
    """
    diameter = radius * 2
    image = Image.new('RGBA', (diameter, diameter))

    for y in range(diameter):
        for x in range(diameter):
            # find the distance to the center
            distance_to_center = math.sqrt((x - radius) ** 2 + (y - radius) ** 2)
            # scale it to the 0-1 range
            distance_to_center = float(distance_to_center) / (math.sqrt(2) * radius)
            # calculate the alpha value using the weight and the intensity
            alpha = int(255 * max(0, (intensity - distance_to_center))) * weight
            if alpha > 0:
                # write the pixel value in black with the calculated alpha value
                image.putpixel((x, y), (0, 0, 0, alpha))

    return image
