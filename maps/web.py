#!/usr/bin/env python3

from elasticsearch import Elasticsearch
from flask import Flask, send_file, request, jsonify

from maps import parameters
from maps.exceptions import InvalidRequestType, InvalidStyle
from maps.query import search
from maps.tiles.gridded import GriddedTile
from maps.tiles.heatmap import HeatmapTile
from maps.tiles.plot import PlotTile

try:
    # attempt to import the uwsgi postfork decorator. If it fails, not a problem, we're just not
    # running in a uwsgi environment (https://uwsgi-docs.readthedocs.io/en/latest/PythonModule.html)
    from uwsgidecorators import postfork
except ImportError:
    # just replace postfork with a noop decorator function
    def postfork(f):
        return f

# it's flask time!
app = Flask(__name__)
# load the default config settings
app.config.from_object('maps.config')
# load any settings from the config file pointed at by the maps_config environment variable
app.config.from_envvar('maps_config', silent=True)


@postfork
def init_elasticsearch():
    """
    This function instantiates an elasticsearch client for use. It is set on the app in the "client"
    property.

    This function is also decorated with @postfork so that if running under uswgi in prefork mode
    (the uwsgi default) this function is called after the fork has taken place (shocker) allowing us
    to reinstantiate the elasticsearch client because it can't handle the forking - it produces all
    kinds of weird errors during concurrent multiprocess use if you don't do this.
    """
    app.client = Elasticsearch(hosts=app.config['ELASTICSEARCH_HOSTS'],
                               sniff_on_start=app.config['ELASTICSEARCH_SNIFF_ON_START'],
                               sniff_on_connection_fail=app.config[
                                   'ELASTICSEARCH_SNIFF_ON_CONNECTION_FAIL'],
                               sniffer_timeout=app.config['ELASTICSEARCH_SNIFFER_TIMEOUT'],
                               sniff_timeout=app.config['ELASTICSEARCH_SNIFF_TIMEOUT'],
                               http_compress=app.config['ELASTICSEARCH_HTTP_COMPRESS'],
                               timeout=app.config['ELASTICSEARCH_TIMEOUT'])


# create an elasticsearch client for us to use
init_elasticsearch()

# map the various tile styles to their implementation classes
tile_styles = {tile_class.style: tile_class for tile_class in (PlotTile, GriddedTile, HeatmapTile)}
tile_parameters = {
    PlotTile.style: {
        'png': parameters.extract_plot_parameters,
        'grid.json': parameters.extract_plot_utf_grid_params,
    },
    GriddedTile.style: {
        'png': parameters.extract_gridded_parameters,
        'grid.json': parameters.extract_gridded_utf_grid_params,
    },
    HeatmapTile.style: {
        'png': parameters.extract_heatmap_parameters,
        # no UTFGrid for heatmaps
        'grid.json': None,
    }
}


# TODO: store/expose request/response stats somewhere for monitoring?
@app.route('/<int:z>/<int:x>/<int:y>.<string:request_type>')
def render_tile(x, y, z, request_type):
    """
    Handles tile image and UTFGrid requests.

    :param x: the tile's x value
    :param y: the tile's y value
    :param z: the tile's z value
    :param request_type: the request type, this should be either `png` or `grid.json`
    :return: either a png image or a json document
    """
    if request_type != 'png' and request_type != 'grid.json':
        raise InvalidRequestType(request_type)

    # get the requested style, default to plot if it's missing
    style = request.args.get('style', PlotTile.style)
    if style not in tile_styles:
        raise InvalidStyle(style)

    tile = tile_styles[style](x, y, z)

    # query elasticsearch, this will return a list of buckets containing locations and counts
    points = search(tile, **parameters.extract_search_params())

    # extract the parameters for the tile style and request type combination
    params = tile_parameters[style][request_type]()

    # create the appropriate response, either png or grid.json
    if request_type == 'png':
        response = send_file(tile.as_image(points, **params), mimetype='image/png')
    else:
        response = jsonify(tile.as_grid(points, **params))

    # ahhh cors
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# for dev use only
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
