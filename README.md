# Versioned datastore tile server

[![Travis](https://img.shields.io/travis/NaturalHistoryMuseum/versioned-datastore-tile-server.svg?style=flat-square)](https://travis-ci.org/NaturalHistoryMuseum/versioned-datastore-tile-server)
[![Coveralls github](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/versioned-datastore-tile-server.svg?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/versioned-datastore-tile-server)

A tile server for use with the versioned datastore: https://github.com/NaturalHistoryMuseum/ckanext-versioned-datastore.

![NHM Heatmap](/resources/heatmap.png?raw=true "NHM Specimen Heatmap")


### Install
Currently the best way to install is to:
 
1. Clone the repo
2. Inside your clone, create a python (>=3.5) virtualenv:
    ```bash
    mkdir venv
    virtualenv venv -p python3.5
    source venv/bin/activate
    ```
3. Install the requirements into your virtualenv:
    ```bash
    pip install -r requirements.txt
    ```

And that's it.


### Running the server
The main Flask app is located in `maps/web.py` and should be run under [uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/).
From within the virtualenv, simply run:
```bash
uwsgi uwsgi.ini
```
to start the server with the default app and uwsgi settings.

To modify the app settings, create a file containing the overrides and an environment variable called `maps_config` that contains the full path to that file.
For example:
```bash
export maps_config=/home/josh/work/versioned-datastore-tile-server/maps.cfg
```
See the Configuration section below for more information about the format of this file and the available settings.

#### Running in development
Flask comes with it's own simple server for development work and the `maps/web.py` module is setup to start this when it is run.
Hence, _for test and development purposes only_ you can start the server with:
```bash
python -m maps.web.py
```
With the default settings, this will start a server running at `0.0.0.0:5000`.

#### Running in production
For production you should run the `uwsgi` server, probably behind `nginx`.
It is recommended that you use a service like `supervisor` to control the uwsgi server.


### App configuration
The app can be configured using a configuration file whose absolute path is stored in an environment variable called `maps_config`.
Currently the available options are:

| Name | Expected type | Description | Default |
|------|---------------|-------------|---------|
| `ELASTICSEARCH_HOSTS` | a list of strings | Each element in the list should be the full root HTTP(S) address of an Elasticsearch server | `['http://localhost:9200']` |
| `ELASTICSEARCH_SNIFF_ON_START` | boolean | Corresponds to the Elasticsearch client's `sniff_on_start` parameter | `True` |
| `ELASTICSEARCH_SNIFF_ON_CONNECTION_FAIL` | boolean | Corresponds to the Elasticsearch client's `sniff_on_connection_fail` parameter | `True` |
| `ELASTICSEARCH_SNIFFER_TIMEOUT` | integer | Corresponds to the Elasticsearch client's `sniffer_timeout` parameter | `60` |
| `ELASTICSEARCH_SNIFF_TIMEOUT` | integer | Corresponds to the Elasticsearch client's `sniff_timeout` parameter | `10` |
| `ELASTICSEARCH_HTTP_COMPRESS` | boolean | Corresponds to the Elasticsearch client's `http_compress` parameter | `False` |
| `ELASTICSEARCH_TIMEOUT` | integer | Corresponds to the Elasticsearch client's `timeout` parameter | `60` |

The configuration file can be a Python file. It is read using Flask's `from_envvar` function.


### Request configuration
All 3 map styles have configuration options available.
The defaults are hard coded and are intended to be modified at the request level, not the main app config level (though this could change, it just seemed sensible when creating the project).

#### General options
##### Request query string options
| Name | Description | Default |
|------|-------------|---------|
| `indexes` | The Elasticsearch indexes that should be searched to produce the points in the rendered tile | |
| `search` | The Elasticsearch query that should be used to limit the data. This shouldn't include the tile limiting geo-query, but simply any other query that should be used in combination with the queries and filters added by the server. This should be a stringified JSON object| |
| `query` | A gzipped, base64 encoded, JSON string containing the indexes (key: `indexes`) to search and the search too perform (key: `search`) | |
| `style` | The style of map tile to render, must be either `plot`, `gridded` or `heatmap` | `plot` |

The indexes to be searched is the only required variable and must be set either through `indexes` itself or in `query`.

##### Request path options
Requests should be directed at `http(s)://<domain>/{z}/{x}/{y}.{request_type}` where:

| Name | Description |
|------|-------------|
| `z` | The z value of the tile |
| `x` | The x value of the tile |
| `y` | The y value of the tile |
| `request_type` | The type of response to get, either `png` or `grid.json` |

For example: `http://localhost:5000/0/0/0.png` or `http://localhost:5000/0/0/0.grid.json`


#### Plot options
##### Request query string options
| Name | Applies to request type | Description | Default |
|------|-------------------------|-------------|---------|
| `point_radius` | `png` | The integer radius of the rendered points (including the border) | `4` |
| `point_colour` | `png` | The hex value to render the points in | `#ee0000` ![#ee0000](https://placehold.it/15/ee0000/000000?text=+) |
| `border_width` | `png` | The integer border width of the rendered points | `1` |
| `border_colour` | `png` | The hex value to render the borders of the points in | `#ffffff` ![#ffffff](https://placehold.it/15/ffffff/000000?text=+) |
| `resize_factor` | `png` | A resize value to use when smoothing the tile. This value will be used to scale the tile and then down (with anti-aliasing) to produce a smoother output. Increasing this value will negatively impact performance | `4` |
| `grid_resolution` | `grid.json` | The integer size of the cells in the grid that each tile is split into for the UTFGrid. The default of `4` produces a 64x64 grid within each tile | `4` |
| `point_width` | `grid.json` | The integer width of the points in the UTFGrid | `3` |

#### Gridded options
##### Request query string options
| Name | Applies to request type | Description | Default |
|------|-------------------------|-------------|---------|
| `grid_resolution` | `png` | The integer size of the cells in the grid that each tile is split into. The default of `8` produces a 32x32 grid within each tile and therefore matches the default `grid.json` setting too | `8` |
| `cold_colour` | `png` | The hex value to be used to render the points with the lowest counts | `#f4f11a` ![#f4f11a](https://placehold.it/15/f4f11a/000000?text=+) |
| `hot_colour` | `png` | The hex value to be used to render the points with the highest counts | `#f02323` ![#f02323](https://placehold.it/15/f02323/000000?text=+) |
| `range_size` | `png` | This many colours will be used to render the points dependant on their counts | `12` |
| `resize_factor` | `png` | A resize value to use when smoothing the tile. This value will be used to scale the tile and then down (with anti-aliasing) to produce a smoother output. Increasing this value will negatively impact performance | `4` |
| `grid_resolution` | `grid.json` | The integer size of the cells in the grid that each tile is split into for the UTFGrid. The default of `8` produces a 32x32 grid within each tile and therefore matches the default `png` setting too | `8` |
| `point_width` | `grid.json` | The integer width of the points in the UTFGrid | `1` |

#### Heatmap options
##### Request query string options
| Name | Applies to request type | Description | Default |
|------|-------------------------|-------------|---------|
| `point_radius` | `png` | The integer radius of the rendered points (including the border) | `8` |
| `cold_colour` | `png` | The hex value to be used to render the points with the lowest counts | `#0000ee` ![#0000ee](https://placehold.it/15/0000ee/000000?text=+) |
| `hot_colour` | `png` | The hex value to be used to render the points with the highest counts | `#ee0000` ![#ee0000](https://placehold.it/15/ee0000/000000?text=+) |
| `intensity` | `png` | The decimal intensity (between 0 and 1) to render the tile with | `0.5` |


### Running the tests

Make sure you've installed the test requirements into your virtualenv - `pip install -r tests/requirements.txt`, then:

 - To run the tests against the python version installed in your virtualenv, run `pytest`
 - To run the tests against the python version installed in your virtualenv and get a coverage report too, run `pytest --cov=maps`
