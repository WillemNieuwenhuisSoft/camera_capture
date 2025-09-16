import pytest
from unittest import mock
import json
from pathlib import Path
from datetime import time
from camera.config import CameraConfig

# src/camera/test_config.py


@pytest.fixture(autouse=True)
def patch_logger():
    with mock.patch("camera.config.logger"):
        yield


@pytest.fixture
def patch_home_and_config(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr("camera.config.Path.home", lambda: fake_home)
    config_file = fake_home / "camera.config"
    monkeypatch.setattr("camera.config.CONFIG_FILE", config_file)
    return config_file


def test_default_initialization_creates_config(patch_home_and_config):
    config_file = patch_home_and_config
    assert not config_file.exists()
    cfg = CameraConfig()
    assert config_file.exists()
    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["image_save_path"] == str(Path.home() / "camera_images")
    assert data["locations_file"] == "camera_locations.txt"


def test_load_existing_config_all_fields(patch_home_and_config):
    config_file = patch_home_and_config
    config_data = {
        "image_save_path": "/tmp/images",
        "locations_file": "/tmp/locs.txt",
        "start": "07:15",
        "end": "19:45",
        "interval": 42,
        "verbose": True
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f)
    cfg = CameraConfig()
    assert cfg.image_save_path == Path("/tmp/images")
    assert cfg.location_file == "locs.txt"
    assert cfg.start == time(7, 15)
    assert cfg.end == time(19, 45)
    assert cfg.interval == 42
    assert cfg.verbose is True


def test_load_config_missing_fields(patch_home_and_config):
    config_file = patch_home_and_config
    config_data = {
        "image_save_path": "/tmp/images"
        # missing other fields
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f)
    cfg = CameraConfig()
    assert cfg.image_save_path == Path("/tmp/images")
    # Defaults for missing fields
    assert cfg.locations_file == "camera_locations.txt"
    assert cfg.start == time(6, 30)
    assert cfg.end == time(18, 30)
    assert cfg.interval == 30
    assert cfg.verbose is False


def test_load_config_invalid_fields(patch_home_and_config):
    config_file = patch_home_and_config
    config_data = {
        "image_save_path": "/tmp/images",
        "locations_file": "/tmp/locs.txt",
        "start": "not-a-time",
        "end": "not-a-time",
        "interval": "not-an-int",
        "verbose": "not-a-bool"
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f)
    # Should log error and use defaults for invalid fields
    cfg = CameraConfig()
    assert cfg.image_save_path == Path("/tmp/images")
    assert cfg.location_file == "locs.txt"
    assert cfg.start == time(6, 30)
    assert cfg.end == time(18, 30)
    assert cfg.interval == 30
    assert cfg.verbose is False


def test_save_writes_config_file(patch_home_and_config):
    config_file = patch_home_and_config
    cfg = CameraConfig()
    cfg.image_save_path = Path("/abc")
    cfg.location_file = "def.txt"
    cfg.start = time(8, 0)
    cfg.end = time(20, 0)
    cfg.interval = 99
    cfg.verbose = True
    cfg.save()
    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert Path(data["image_save_path"]) == Path("/abc")
    assert data["locations_file"] == "def.txt"
    assert data["start"] == "08:00"
    assert data["end"] == "20:00"
    assert data["interval"] == 99
    assert data["verbose"] is True


def test_fields_yields_all_fields_with_descriptions():
    cfg = CameraConfig()
    fields = dict((name, (value, desc)) for name, value, desc in cfg.fields())
    for field_name in cfg.__dataclass_fields__:
        assert field_name in fields
        # Description should match FIELD_DESCRIPTIONS or be empty string
        assert isinstance(fields[field_name][1], str)
