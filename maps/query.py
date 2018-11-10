#!/usr/bin/env python3

import flask
import geohash
from elasticsearch_dsl import Search

from maps.utils import lat_lon_clamp


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
        'meta.geo': {
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
        .bucket('grid', 'geohash_grid', field='meta.geo', precision=precision, size=points) \
        .bucket('first', 'top_hits', size=1)

    # run the query and extract the buckets part of the response
    result = s.execute()
    buckets = result.aggs.to_dict()['grid']['buckets']
    # loop through the aggregated buckets that are returned from elasticsearch converting the
    # geohashes into latitude/longitude pairs and storing them with the count at each point and the
    # first hit's data
    return [(*geohash.decode(bucket['key']), bucket['doc_count'],
             bucket['first']['hits']['hits'][0]['_source']) for bucket in buckets]
