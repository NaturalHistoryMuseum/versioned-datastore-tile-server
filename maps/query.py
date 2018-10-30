#!/usr/bin/env python3

import geohash
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

client = Elasticsearch(hosts=[u'http://172.17.0.2:9200'], sniff_on_start=True,
                       sniff_on_connection_fail=True, sniffer_timeout=60, sniff_timeout=10,
                       http_compress=True)


def search(tile, index, precision, points=5000):
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
    :param index: the index to query
    :param precision: the precision to use in the geohash grid aggregation. See the elasticsearch
                      doc for info about the possible values for this parameter and their meaning
    :param points: the number of points to return in the aggregation, i.e. the maximum number of
                   points that will be returned in the buckets list (default: 5000)
    :return: a list of dicts, each containing a "key" with a geohash and a "doc_count" with the
             total records at that geohash
    """
    # create the geo_bounding_box query, which will filter the data by the tile's bounding box
    geo_search = {
        'meta.geo': {
            'top_left': '{}, {}'.format(*tile.top_left()),
            'bottom_right': '{}, {}'.format(*tile.bottom_right()),
        }
    }
    # create a search object with the geo_bounding_box filter. Also note that from and size are both
    # set to 0 using the slice at the end to save elasticsearch sending us data we don't need
    s = Search(using=client, index=index).filter('geo_bounding_box', **geo_search)[0:0]
    # add the geohash_grid aggregation
    s.aggs.bucket('grid', 'geohash_grid', field='meta.geo', precision=precision, size=points)
    # run the query and extract the buckets part of the response
    buckets = s.execute().aggs.to_dict()['grid']['buckets']
    # loop through the aggregated buckets that are returned from elasticsearch converting the
    # geohashes into latitude/longitude pairs and storing them with the count at each point. We
    # iterate through the buckets in reverse order as elasticsearch returns them in descending total
    # order but we want to render the most significant points (the ones with the highest totals) on
    # top when creating tiles and UTFGrids later
    return [(*geohash.decode(bucket['key']), bucket['doc_count']) for bucket in reversed(buckets)]
