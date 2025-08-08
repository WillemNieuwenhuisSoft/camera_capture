import pytest
from unittest import mock
from pathlib import Path
from datetime import date, datetime
from camera.capture_functions import retrieve_image, update_folder_tree, save_camera_image

# src/camera/test_capture_functions.py


@pytest.fixture(autouse=True)
def patch_logger():
    with mock.patch("camera.capture_functions.logger"):
        yield


def test_retrieve_image_empty_url():
    assert retrieve_image("") is None


def test_retrieve_image_success(monkeypatch):
    class MockResponse:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = b"fakeimagedata"

    def mock_get(url, headers):
        return MockResponse()
    monkeypatch.setattr("camera.capture_functions.requests.get", mock_get)
    result = retrieve_image("http://example.com/image.png")
    assert result == b"fakeimagedata"


def test_retrieve_image_non_image(monkeypatch):
    class MockResponse:
        status_code = 200
        headers = {"Content-Type": "text/html"}
        content = b"notanimage"

    def mock_get(url, headers):
        return MockResponse()
    monkeypatch.setattr("camera.capture_functions.requests.get", mock_get)
    result = retrieve_image("http://example.com/notimage")
    assert result is None


def test_retrieve_image_http_error(monkeypatch):
    class MockResponse:
        status_code = 404
        headers = {"Content-Type": "image/png"}
        content = b""

    def mock_get(url, headers):
        return MockResponse()
    monkeypatch.setattr("camera.capture_functions.requests.get", mock_get)
    result = retrieve_image("http://example.com/404")
    assert result is None


def test_update_folder_tree_creates_path(tmp_path, monkeypatch):
    # Fix the date to a known value
    monkeypatch.setattr("camera.capture_functions.date", mock.Mock(today=lambda: date(2023, 6, 1)))
    station = "stationA"
    expected = tmp_path / station / "2023" / "6" / "1"
    result = update_folder_tree(tmp_path, station)
    assert result == expected
    assert expected.exists()
    assert expected.is_dir()


def test_update_folder_tree_existing_path(tmp_path, monkeypatch):
    monkeypatch.setattr("camera.capture_functions.date", mock.Mock(today=lambda: date(2023, 6, 1)))
    station = "stationB"
    expected = tmp_path / station / "2023" / "6" / "1"
    expected.mkdir(parents=True)
    result = update_folder_tree(tmp_path, station)
    assert result == expected
    assert expected.exists()


def test_save_camera_image_creates_file(tmp_path, monkeypatch):
    # Fix the date and datetime
    monkeypatch.setattr("camera.capture_functions.date", mock.Mock(today=lambda: date(2023, 6, 1)))
    fixed_dt = datetime(2023, 6, 1, 12, 34)
    monkeypatch.setattr("camera.capture_functions.datetime", mock.Mock(
        now=lambda: fixed_dt, strftime=datetime.strftime))
    station = "stationC"
    suffix = ".jpg"
    img_data = b"abc123"
    save_camera_image(img_data, tmp_path, station, suffix)
    img_folder = tmp_path / station / "2023" / "6" / "1"
    expected_filename = img_folder / f"{station}_20230601_1234{suffix}"
    assert expected_filename.exists()
    with open(expected_filename, "rb") as f:
        assert f.read() == img_data
