# Versioned datastore tile server

[![Travis](https://img.shields.io/travis/NaturalHistoryMuseum/versioned-datastore-tile-server.svg?style=flat-square)](https://travis-ci.org/NaturalHistoryMuseum/versioned-datastore-tile-server)
[![Coveralls github](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/versioned-datastore-tile-server.svg?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/versioned-datastore-tile-server)

A tile server for use with the versioned datastore: https://github.com/NaturalHistoryMuseum/ckanext-versioned-datastore.

**This project is currently under active development.**


### Running the tests

Make sure you've installed the test requirements into your virtualenv - `pip install -r tests/requirements.txt`, then:

 - To run the tests against the python version installed in your virtualenv, run `pytest`
 - To run the tests against the python version installed in your virtualenv and get a coverage report too, run `pytest --cov=maps`
