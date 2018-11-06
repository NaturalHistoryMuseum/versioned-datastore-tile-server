#!/usr/bin/env python3

"""
This module contains default configuration options which will be read by flask on start. You can
override them by using creating a configuration file and then pointing the environment variable
"maps_config" at it. Make sure to use the full path. The configuration file can just be a python
file like this one.
"""

ELASTICSEARCH_HOSTS = ['http://localhost:9200']
