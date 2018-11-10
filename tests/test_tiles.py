#!/usr/bin/env python3

from unittest.mock import MagicMock, call

from pytest import approx

from maps.tiles import Tile


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
        tile = Tile(MagicMock(), MagicMock(), zoom)
        assert expected_x == tile.longitude_to_x(longitude)


def test_latitude_to_y():
    tile_z_0 = Tile(MagicMock(), MagicMock(), 0)
    tile_z_2 = Tile(MagicMock(), MagicMock(), 2)
    tile_z_4 = Tile(MagicMock(), MagicMock(), 4)

    assert 0.5 == tile_z_0.latitude_to_y(0)
    assert 2 == tile_z_2.latitude_to_y(0)
    # 85.0511 is the limit at which web mercator operates so the value should be really close to 0
    # but not quite 0
    assert 0 < tile_z_0.latitude_to_y(85.0511) < 0.001
    # -85.0511 is the limit at which web mercator operates so the value should be really close to 1
    # but not quite 1
    assert 0.999 < tile_z_0.latitude_to_y(-85.0511) < 1
    # values beyond -85.0511 or 85.0511 should be clamped
    assert tile_z_0.latitude_to_y(-85.0511) == tile_z_0.latitude_to_y(-90)
    assert tile_z_4.latitude_to_y(-85.0511) == tile_z_4.latitude_to_y(-95)
    assert tile_z_0.latitude_to_y(85.0511) == tile_z_0.latitude_to_y(90)
    assert tile_z_4.latitude_to_y(85.0511) == tile_z_4.latitude_to_y(95)


def test_translate():
    assert Tile(0, 0, 0).translate() == (approx(85.0511), -180)
    assert Tile(0, 0, 4).translate() == (approx(85.0511), -180)
    assert Tile(1, 1, 1).translate() == (0, 0)
    assert Tile(2, 2, 2).translate() == (0, 0)
    assert Tile(1, 1, 1).translate(1, 1) == Tile(2, 2, 1).translate()


def test_middle_and_corners():
    tile = Tile(0, 0, 0)
    # monkeypatch translate with a mock
    tile.translate = MagicMock()

    tile.middle()
    # middle should be x + 0.5, y + 0.5
    assert tile.translate.call_args == call(0.5, 0.5)

    tile.top_left()
    # top left should be x, y
    assert tile.translate.call_args == call(0, 0)

    tile.top_right()
    # top right should be x + 1, y
    assert tile.translate.call_args == call(1, 0)

    tile.bottom_right()
    # bottom right should be x + 1, y + 1
    assert tile.translate.call_args == call(1, 1)

    tile.bottom_left()
    # bottom left should be x, y + 1
    assert tile.translate.call_args == call(0, 1)
