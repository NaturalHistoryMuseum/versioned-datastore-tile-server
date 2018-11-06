#!/usr/bin/env python3

"""
This module contains default configuration options which will be read by flask on start. You can
override them on an application level basis by using a file called `maps.cfg` placed in the flask
instance folder.
"""

ELASTICSEARCH_HOSTS = ['http://localhost:9200']
