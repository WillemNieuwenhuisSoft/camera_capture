from datetime import datetime, timedelta, time as time_class
import pandas as pd
import time
import pytest
from unittest.mock import patch

from testfixtures import Replace, mock_time
from camera.capture import determine_delay_to_next_capture_time, wait_until_next_capture
from camera.capture import capture_all_repeat, NONSTOP_CAPTURE, CAPTURE_TODAY
from camera.config import CameraConfig


@pytest.mark.parametrize("current_time, start_time, end_time, expected_wait", [
    pytest.param(datetime(2023, 10, 1, 6, 0), time_class(6, 30), time_class(hour=18, minute=30),
                 1800, id='before start'),  # same day, before start: 30 minutes wait
    pytest.param(datetime(2023, 10, 1, 6, 30), time_class(6, 30), time_class(hour=18, minute=30),
                 0, id='at start'),  # No wait: Exactly at start
    pytest.param(datetime(2023, 10, 1, 7, 0), time_class(6, 30), time_class(hour=18, minute=30),
                 1800, id='past start, integer interval'),  # No wait, past start time at integer interval
    pytest.param(datetime(2023, 10, 1, 8, 15), time_class(6, 30), time_class(hour=18, minute=30),
                 900, id='past start, non-integer interval'),  # 15 minute wait, non-integer interval
    pytest.param(datetime(2023, 10, 1, 18, 0), time_class(6, 30), time_class(hour=18, minute=30),
                 1800, id='before end, integer interval'),  # No wait, before end at integer interval
    pytest.param(datetime(2023, 10, 1, 18, 30), time_class(6, 30), time_class(hour=18, minute=30),
                 0, id='at end'),  # No wait, exactly at end
    pytest.param(datetime(2023, 10, 1, 19, 0), time_class(6, 30), time_class(hour=18, minute=30),
                 41400, id='after end'),  # after end: wait until next day
])
def test_start_time_before_capture(current_time, start_time, end_time, expected_wait):
    """Test the correct determination of the next capture time for several scenarios."""
    time_class(6, 30)  # Set the start time to 6:30 AM
    config = CameraConfig()
    config.start = start_time
    config.end = end_time
    config.interval = 30
    # Mock the current time to be before the configured start time
    mock_now = current_time
    with patch("camera.capture.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        to_wait, _ = determine_delay_to_next_capture_time(config, mock_now)
    assert to_wait == expected_wait, f"Expected wait time {expected_wait} seconds, got {to_wait} seconds"


def test_next_capture_and_wait():
    """Test that the next capture time is correctly calculated and the wait function works as expected."""
    config = CameraConfig()
    config.start = time_class(6, 30)
    config.end = time_class(10, 30)
    config.interval = 60
    wait_period_length = 3600
    time_tuple = (2023, 10, 1, 7, 0, 0)
    now = datetime(*time_tuple)
    sleep_time, capture_time = determine_delay_to_next_capture_time(config, now)

    assert sleep_time == 1800, "Expected to wait for 30 minutes (1800 seconds)"
    assert capture_time == datetime(2023, 10, 1, 7, 30), "Expected next capture time to be at 07:30"

    # Test the wait_until_next_capture function
    with patch("camera.capture.sleep") as mock_sleep:
        wait_until_next_capture(sleep_time, wait_period_length)
        mock_sleep.assert_called_once_with(sleep_time)


@pytest.mark.parametrize("interval", [
    pytest.param(10, id='10 minute interval'),
    pytest.param(15, id='15 minute interval'),
    pytest.param(30, id='30 minute interval'),
    pytest.param(60, id='60 minute interval'),
    pytest.param(90, id='90 minute interval'),
])
def test_capture_time_and_wait_three_days(interval: int):
    """Test the cooperation between delay_to_next_capture_time and wait_until_next_capture functions
       to ensure captures are at the correct intervals.
       This test simulates a three-day period with a specified time range per day.
       The entry time (current_time) is not at an exact multiple of the interval time since the start time.
    """
    config = CameraConfig()
    config.start = time_class(6, 30)
    config.end = time_class(10, 30)
    config.interval = interval
    process_time = 10  # Simulate a processing time of 10 seconds
    wait_period_length = 3600 * 3
    current_time = datetime(2023, 10, 1, 7, 0, 10)

    import time
    # Mock the current time to be the same as now
    with patch("camera.capture.datetime") as mock_datetime:
        while current_time <= datetime(2023, 10, 3, 10, 30):
            # run for three days
            print(f"Current time: {current_time}")
            mock_datetime.now.return_value = current_time

            with patch("camera.capture.sleep") as mock_sleep:
                sleep_time, capture_time = determine_delay_to_next_capture_time(config, current_time)
                print(f"Next capture time: {capture_time}, Sleep time: {sleep_time}")
                wait_until_next_capture(sleep_time, wait_period_length)
                mock_sleep.assert_called()
            current_time = capture_time + timedelta(seconds=process_time)


@pytest.mark.parametrize("interval", [
    pytest.param(10, id='10 minute interval'),
    pytest.param(15, id='15 minute interval'),
    pytest.param(30, id='30 minute interval'),
    pytest.param(60, id='60 minute interval'),
    pytest.param(90, id='90 minute interval'),
])
def test_capture_repeat_one_day(interval: int):
    """Simulate the capture_all_repeat function to ensure it captures at the correct intervals over one day.
       This test uses a mock time to simulate the current time and the capture process, to allow it to run quickly.
    """
    config = CameraConfig()
    config.start = time_class(6, 30)
    config.end = time_class(10, 30)
    config.interval = interval
    config.verbose = True
    time_tuple = (2023, 10, 1, 7, 0, 10)
    current_time = datetime(*time_tuple)
    from testfixtures import Replace, mock_datetime, mock_time

    with Replace("camera.capture.datetime", mock_datetime(current_time, delta=interval, delta_type='minutes')):
        with patch("camera.capture.sleep") as mock_sleep:
            with Replace("camera.capture.time", mock_time(*time_tuple, delta=interval, delta_type='minutes')):
                succeeded = capture_all_repeat(pd.DataFrame(), config, capture_mode=CAPTURE_TODAY)
                assert succeeded, "Capture should succeed without errors"
