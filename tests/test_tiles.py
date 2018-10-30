#!/usr/bin/env python3

from pytest import approx

from maps.tiles import longitude_to_x, latitude_to_y, translate


def test_longitude_to_x():
    checks = [
        # using 0 as the zoom puts the results in the range 0-1
        (0, 0, 0.5),
        (-180, 0, 0),
        (180, 0, 1),
        (-360, 0, 0.5),
        (360, 0, 0.5),
        (-540, 0, 0),
        (540, 0, 0),
        # now zoom level 2
        (0, 2, 2),
        (-180, 2, 0),
        (180, 2, 4),
        (-360, 2, 2),
        (360, 2, 2),
        (-540, 2, 0),
        (540, 2, 0),
    ]
    for longitude, zoom, expected_x in checks:
        assert expected_x == longitude_to_x(longitude, zoom)


def test_latitude_to_y():
    assert 0.5 == latitude_to_y(0, 0)
    assert 2 == latitude_to_y(0, 2)
    # 85.0511 is the limit at which web mercator operates so the value should be really close to 0
    # but not quite 0
    assert 0 < latitude_to_y(85.0511, 0) < 0.001
    # -85.0511 is the limit at which web mercator operates so the value should be really close to 1
    # but not quite 1
    assert 0.999 < latitude_to_y(-85.0511, 0) < 1
    # values beyond -85.0511 or 85.0511 should be clamped
    assert latitude_to_y(-85.0511, 0) == latitude_to_y(-90, 0)
    assert latitude_to_y(-85.0511, 4) == latitude_to_y(-95, 4)
    assert latitude_to_y(85.0511, 0) == latitude_to_y(90, 0)
    assert latitude_to_y(85.0511, 4) == latitude_to_y(95, 4)


def test_translate():
    assert translate(0, 0, 0) == (approx(85.0511), -180)
    assert translate(0, 0, 4) == (approx(85.0511), -180)
    assert translate(1, 1, 1) == (0, 0)
    assert translate(2, 2, 2) == (0, 0)
