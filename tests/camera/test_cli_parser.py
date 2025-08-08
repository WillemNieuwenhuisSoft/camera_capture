from datetime import time
from unittest import mock
from argparse import Namespace
from camera.cli_parser import cli_parser, list_cli, update_cli

# src/camera/test_cli_parser.py


def test_cli_parser_structure():
    parser = cli_parser()
    args = parser.parse_args(['run'])
    assert args.Command == 'run'
    args = parser.parse_args(['run-repeat-no-limit'])
    assert args.Command == 'run-repeat-no-limit'
    args = parser.parse_args(['run-repeat'])
    assert args.Command == 'run-repeat'
    args = parser.parse_args(['config', 'list'])
    assert args.Command == 'config'
    assert args.Configuration == 'list'
    args = parser.parse_args(['config', 'update', 'interval', '30'])
    assert args.Command == 'config'
    assert args.Configuration == 'update'
    assert args.key == 'interval'
    assert args.value == '30'


def test_list_cli_prints_fields(monkeypatch):
    fake_fields = [
        ('image_save_path', '/tmp', 'desc1'),
        ('interval', 30, 'desc2'),
    ]
    with mock.patch("camera.cli_parser.CameraConfig") as MockConfig:
        instance = MockConfig.return_value
        instance.fields.return_value = fake_fields
        with mock.patch("builtins.print") as mock_print:
            list_cli(Namespace())
            # Should print config file and each field
            assert any('/tmp' in str(call) for call in mock_print.call_args_list)
            assert any('interval' in str(call) for call in mock_print.call_args_list)


def test_update_cli_image_save_path(monkeypatch):
    with mock.patch("camera.cli_parser.CameraConfig") as MockConfig, \
            mock.patch("camera.cli_parser.logger") as mock_logger:
        instance = MockConfig.return_value
        args = Namespace(key='image_save_path', value='/abc')
        update_cli(args)
        assert instance.image_save_path == mock.ANY
        instance.save.assert_called_once()
        mock_logger.info.assert_called()


def test_update_cli_interval_valid(monkeypatch):
    with mock.patch("camera.cli_parser.CameraConfig") as MockConfig, \
            mock.patch("camera.cli_parser.logger") as mock_logger:
        instance = MockConfig.return_value
        args = Namespace(key='interval', value='60')
        update_cli(args)
        assert hasattr(instance, 'capture_interval')
        instance.save.assert_called_once()
        mock_logger.info.assert_called()


def test_update_cli_interval_invalid(monkeypatch):
    with mock.patch("camera.cli_parser.CameraConfig") as MockConfig, \
            mock.patch("camera.cli_parser.logger") as mock_logger:
        instance = MockConfig.return_value
        args = Namespace(key='interval', value='notanint')
        update_cli(args)
        mock_logger.error.assert_called_with("Invalid value for capture interval. Must be an integer.")
        instance.save.assert_not_called()


def test_update_cli_interval_out_of_range(monkeypatch):
    with mock.patch("camera.cli_parser.CameraConfig") as MockConfig, \
            mock.patch("camera.cli_parser.logger") as mock_logger:
        instance = MockConfig.return_value
        args = Namespace(key='interval', value='5')
        update_cli(args)
        mock_logger.error.assert_called_with("Allowed capture interval range: 15 to 360 minutes.")
        instance.save.assert_not_called()


def test_update_cli_start_end_valid(monkeypatch):
    with mock.patch("camera.cli_parser.CameraConfig") as MockConfig, \
            mock.patch("camera.cli_parser.logger") as mock_logger:
        instance = MockConfig.return_value
        instance.start = mock.Mock()
        instance.end = time(18, 30)
        args = Namespace(key='start', value='07:00')
        # Patch setattr to actually set .start

        def fake_setattr(obj, name, value):
            setattr(instance, name, value)
        monkeypatch.setattr("camera.cli_parser.CameraConfig.setattr", fake_setattr)
        update_cli(args)
        instance.save.assert_called_once()
        mock_logger.info.assert_called()


def test_update_cli_start_end_invalid(monkeypatch):
    with mock.patch("camera.cli_parser.CameraConfig") as MockConfig, \
            mock.patch("camera.cli_parser.logger") as mock_logger:
        instance = MockConfig.return_value
        args = Namespace(key='start', value='badtime')
        update_cli(args)
        assert any("Invalid time for start time" in str(call) for call in mock_logger.error.call_args_list)
        instance.save.assert_not_called()


def test_update_cli_start_after_end(monkeypatch):
    with mock.patch("camera.cli_parser.CameraConfig") as MockConfig, \
            mock.patch("camera.cli_parser.logger") as mock_logger:
        config = MockConfig.return_value

        # Patch setattr to set .start and .end so start >= end
        def fake_setattr(obj, name, value):
            if name == "start":
                config.start = time(10, 30)
        monkeypatch.setattr("camera.cli_parser.CameraConfig.setattr", fake_setattr)
        args = Namespace(key='start', value='10:00')
        config.end = time(5, 30)
        update_cli(args)
        mock_logger.error.assert_called_with("Start time must be before end time.")
        config.save.assert_not_called()
