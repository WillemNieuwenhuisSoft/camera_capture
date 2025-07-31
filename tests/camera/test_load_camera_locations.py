import pytest
import pandas as pd
from camera.camera_locations import load_camera_locations


@pytest.fixture
def valid_csv(tmp_path):
    content = "url,location\nhttp://cam1,Entrance\nhttp://cam2,Exit"
    file = tmp_path / "cameras.csv"
    file.write_text(content)
    return str(file)


@pytest.fixture
def missing_columns_csv(tmp_path):
    content = "url,name\nhttp://cam1,Main"
    file = tmp_path / "bad.csv"
    file.write_text(content)
    return str(file)


@pytest.fixture
def malformed_csv(tmp_path):
    content = "url,location\nhttp://cam1"
    file = tmp_path / "malformed.csv"
    file.write_text(content)
    return str(file)


def test_load_camera_locations_valid(valid_csv):
    """ test loading a valid CSV file with camera locations"""
    df = load_camera_locations(valid_csv)
    assert not df.empty
    assert set(df.columns) == {"url", "location"}
    assert df.iloc[0]["url"] == "http://cam1"
    assert df.iloc[1]["location"] == "Exit"


def test_load_camera_locations_missing_columns(missing_columns_csv):
    """ test missing of required columns (url, location)"""
    df = load_camera_locations(missing_columns_csv)
    assert df.empty


def test_load_camera_locations_file_not_found(tmp_path):
    """ test that a non-existent file returns an empty DataFrame"""
    non_existent = tmp_path / "does_not_exist.csv"
    df = load_camera_locations(str(non_existent))
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_load_camera_locations_malformed_csv(malformed_csv):
    """ test that incomplete records are removed"""
    df = load_camera_locations(malformed_csv)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
