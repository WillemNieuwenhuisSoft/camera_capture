import pytest
import pandas as pd
from pathlib import Path
from camera.camera_locations import load_urls_from_file, load_camera_locations
from camera.config import CameraConfig


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


# Test: load_camera_locations function
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


# test: load_urls_from_file function
def test_load_urls_from_file_valid(valid_csv):
    config = CameraConfig()
    config.location_file = Path(valid_csv)

    df = load_urls_from_file(config)
    assert not df.empty
    assert list(df.columns) == ["url", "location"]
    assert len(df) == 2
    assert df.iloc[0]["url"] == "http://cam1"
    assert df.iloc[0]["location"] == "Entrance"


def test_load_urls_from_file_missing_file(tmp_path):
    # File does not exist
    config = CameraConfig()
    config.location_file = tmp_path / "nonexistent.csv"
    df = load_urls_from_file(config)
    assert df.empty


def test_load_urls_from_file_empty_file(tmp_path):
    file_path = tmp_path / "camera_locations.txt"
    file_path.write_text("")
    config = CameraConfig()
    config.location_file = file_path
    df = load_urls_from_file(config)
    assert df.empty


def test_load_urls_from_file_invalid_columns(tmp_path):
    csv_content = "foo,bar\n1,2\n"
    file_path = tmp_path / "camera_locations.txt"
    file_path.write_text(csv_content)
    config = CameraConfig()
    config.location_file = file_path
    df = load_urls_from_file(config)
    assert df.empty
