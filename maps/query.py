#!/usr/bin/env python3

import flask
import geohash
from elasticsearch_dsl import Search

from maps.utils import lat_lon_clamp


class BucketResult:
    """
    Class representing a bucket from the elasticsearch geohash_grid aggregation.
    """

    def __init__(self, bucket):
        """
        :param bucket: the bucket dict
        """
        self.bucket = bucket
        # this will be the geohash value of the bucket
        self.key = bucket['key']
        # decode the centre lat/lon coordinate for the bucket
        self.centre_latitude, self.centre_longitude = geohash.decode(self.key)
        # extract the number of records in this bucket
        self.total = bucket['doc_count']
        # extract the first record in the bucket
        self.first_record = bucket['first']['hits']['hits'][0]['_source']

    def as_geo_json_bbox(self):
        """
        Returns a GeoJSON polygon dict representing bounding box that surrounds this bucket.

        :return: a GeoJSON polygon dict
        """
        bounding_box = geohash.bbox(self.key)
        return {
            "type": "Polygon",
            # note the reversal of the lat/lon and the double list wrap, it's cause this is GeoJSON
            "coordinates": [[
                # top left corner
                [bounding_box['w'], bounding_box['n']],
                # top right corner
                [bounding_box['e'], bounding_box['n']],
                # bottom right corner
                [bounding_box['e'], bounding_box['s']],
                # bottom left corner
                [bounding_box['w'], bounding_box['s']],
            ]],
        }


def search(tile, indexes, search_body, points=15000):
    """
    Search the given index in elasticsearch to get the points and total records at each point
    within the given tile. The buckets from the aggregation are returned as is and therefore will
    look something like this:

        [
            {
                "key": "mwgjy7sz3w",
                "doc_count": 21789
            },
            {
                "key": "gcnc6vgcp6",
                "doc_count": 21674
            },
            {
                "key": "gcpv3b46xz",
                "doc_count": 19636
            },
            ...
        ]

    :param tile: the tile object
    :param indexes: the indexes to query
    :param search_body: the elasticsearch query. This should be a dict or None to use the default.
    :param points: the number of points to return in the aggregation, i.e. the maximum number of
                   points that will be returned in the buckets list (default: 15000)
    :return: a list of dicts, each containing a "key" with a geohash and a "doc_count" with the
             total records at that geohash
    """
    # create a search object with the search_body if there is one
    if search_body is not None:
        s = Search.from_dict(search_body)
    else:
        s = Search()
    # set the indexes and the client to be used as well as setting the from and size to 0 using the
    # slice at the end to stop elasticsearch sending us data we don't need
    s = s.index(indexes).using(flask.current_app.client)[0:0]
    # create the geo_bounding_box query, which will filter the data by the tile's bounding box
    bounding_box = {
        'all_points': {
            # include a small bit of extra wiggle room to ensure we render dots on the edge of tiles
            # correctly (i.e. the actual point should appear in both tiles even when the point
            # itself only reside in one)
            'top_left': '{}, {}'.format(*lat_lon_clamp(tile.top_left(extra=0.01))),
            'bottom_right': '{}, {}'.format(*lat_lon_clamp(tile.bottom_right(extra=0.01))),
        }
    }
    # apply the bounding box filter
    s = s.filter('geo_bounding_box', **bounding_box)
    # calculate the precision to use in the aggregation
    precision = tile.calculate_precision()
    # add the geohash_grid aggregation and the aggregation which will find the first hit
    s.aggs \
        .bucket('grid', 'geohash_grid', field='all_points', precision=precision, size=points) \
        .bucket('first', 'top_hits', size=1)

    # run the query and extract the buckets part of the response
    result = s.execute()
    # loop through the aggregated buckets that are returned from elasticsearch and create
    # BucketResult objects for each
    return [BucketResult(bucket) for bucket in result.aggs.to_dict()['grid']['buckets']]
