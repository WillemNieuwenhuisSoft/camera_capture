from datetime import datetime, time
import pytest
from unittest.mock import patch
from camera.capture import delay_to_next_capture_time
from camera.config import CameraConfig


@pytest.mark.parametrize("current_time, start_time, end_time, expected_wait", [
    (datetime(2023, 10, 1, 6, 0), time(6, 30), time(hour=18, minute=30), 1800),  # same day, before start: 30 minutes wait
    (datetime(2023, 10, 1, 6, 30), time(6, 30), time(hour=18, minute=30), 0),  # No wait: Exactly at start
    (datetime(2023, 10, 1, 7, 0), time(6, 30), time(hour=18, minute=30), 0),  # No wait, past start time at integer interval
    (datetime(2023, 10, 1, 8, 15), time(6, 30), time(hour=18, minute=30), 900),  # 15 minute wait, non-integer interval
    (datetime(2023, 10, 1, 18, 0), time(6, 30), time(hour=18, minute=30), 0),  # No wait, before end at integer interval
    (datetime(2023, 10, 1, 18, 30), time(6, 30), time(hour=18, minute=30), 0),  # No wait, exactly at end
    (datetime(2023, 10, 1, 19, 0), time(6, 30), time(hour=18, minute=30), 41400),  # after end: wait until next day
])
def test_start_time_before_capture(current_time, start_time, end_time, expected_wait):
    """Test that the initial start time is correctly determined before the capture starts."""
    config = CameraConfig()
    config.start = start_time
    config.end = end_time
    config.interval = 30
    # Mock the current time to be before the configured start time
    mock_now = current_time
    with patch("camera.capture.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        to_wait, _ = delay_to_next_capture_time(config)
    assert to_wait == expected_wait, f"Expected wait time {expected_wait} seconds, got {to_wait} seconds"
