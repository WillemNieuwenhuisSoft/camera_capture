from time import time, gmtime
import pytest
from camera.timing_functions import format_seconds_to_hours_minutes, wait_until_next_capture


@pytest.mark.skip(reason="Manual timing test; run manually only.")
def test_timing():
    print("this test will use the actual time functions, so it will take a long while to run.")
    print("this should be run manually, not as part of the test suite.")
    start = time()
    print(f'Starting time {gmtime(start)}, waiting for a long time...')
    wait_until_next_capture(239980, 3600*3, print_func=print)
    end = time()
    print(f'Finished waiting at {gmtime(end)}')
    print(f'Total time waited: {end - start} seconds')

    assert False  # force capture of output to show up


@pytest.mark.parametrize("seconds,expected", [
    pytest.param(0, "0 seconds", id="zero seconds"),
    pytest.param(59, "59 seconds", id="fifty-nine seconds"),
    pytest.param(60, "1 minute", id="sixty seconds"),
    pytest.param(61, "1 minute, 1 second", id="sixty-one seconds"),
    pytest.param(119, "1 minute, 59 seconds", id="one hundred nineteen seconds"),
    pytest.param(120, "2 minutes", id="one hundred twenty seconds"),
    pytest.param(3599, "59 minutes, 59 seconds", id="fifty-nine minutes"),
    pytest.param(3600, "1 hour", id="1 hour 0 minutes"),
    pytest.param(3659, "1 hour, 59 seconds", id="1 hour 59 seconds"),
    pytest.param(3660, "1 hour, 1 minute", id="1 hour 1 minute"),
    pytest.param(3720, "1 hour, 2 minutes", id="1 hour 2 minutes"),
    pytest.param(7200, "2 hours", id="2 hours 0 minutes"),
    pytest.param(7261, "2 hours, 1 minute, 1 second", id="2 hours 1 minute"),
    pytest.param(86399, "23 hours, 59 minutes, 59 seconds", id="23 hours 59 minutes"),
])
def test_format_seconds_to_hours_minutes(seconds, expected):
    assert format_seconds_to_hours_minutes(seconds) == expected
