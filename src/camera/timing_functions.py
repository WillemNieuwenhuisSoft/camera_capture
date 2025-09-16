from datetime import datetime, timedelta
from time import time, sleep
from camera.config import CameraConfig


class EndCaptureException(Exception):
    """Exception to signal the user ended the capture process."""
    pass


def wait_until_first_capture_time(config: CameraConfig) -> None:
    '''This function is called at the start only to avoid initiating the capture process too early.'''
    now = datetime.now()
    if now.time() < config.start:
        sleep_time, _ = determine_delay_to_next_capture_time(config, now)
        wait_until_next_capture(sleep_time, 600)


def determine_delay_to_next_capture_time(config: CameraConfig, now: datetime) -> tuple[int, datetime]:
    """ Determine the initial start time based on the current time and the configured start time.
        Capture time is calculated at regular intervals since the start time.
        Example: If the start time is 06:30, the interval is 30 minutes and the current time is 07:13,
        the next capture will be at 07:30 (6:30 + 2 * 30).
        Return the seconds to wait before actually starting the capture.
    """
    dt_start = now.replace(hour=config.start.hour, minute=config.start.minute, second=0, microsecond=0)
    if now.time() <= config.start:
        return (dt_start - now).seconds, dt_start
    if now.time() == config.end:
        return 0, now
    if now.time() > config.end:
        target = dt_start + timedelta(days=1)
        return (target - now).seconds, target
    else:
        # Otherwise, return the next interval after the current time
        periods = (now - dt_start).seconds // (config.interval * 60)
        remain = (now - dt_start).seconds % (config.interval * 60)
        if (remain >= 0) and (remain < config.interval * 60):
            # last period, may be less then the interval, so adjust
            periods += 1
        target = dt_start + timedelta(minutes=(periods) * config.interval)
        return (target - now).seconds, target


def format_seconds_to_hours_minutes(seconds_to_wait: int) -> str:
    """
    Convert a number of seconds to a string in 'X hour(s) Y minute(s)' format.
    """
    hours = seconds_to_wait // 3600
    minutes = (seconds_to_wait % 3600) // 60
    seconds = seconds_to_wait % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or (hours == 0 and minutes == 0):
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    return ', '.join(parts)


def wait_until_next_capture(seconds: int, period_length: int = 600, print_func=print) -> None:
    """
        Wait until the next capture time, allowing for keyboard interrupts.
        Once per {period_length} report remaining time.
        Note that to get accurate timing, the period length should be short (fe. 1 or 10 minutes).
        The time.sleep() function can experience quite some drift.

        Parameters:
        - seconds: The total number of seconds to wait.
        - period_length: The length of each reporting period in seconds (minimum 1 minute).
        - print_func: Function to use for printing messages (default is print), use None to disable printing.

        Raises:
        - EndCaptureException: If the wait is interrupted by the user.

    """
    # reduce the period_length by 10% to account for drift
    period_length = max(60, int(period_length * 0.9))
    current_time = time()
    end_time = current_time + seconds
    while end_time > current_time:
        seconds_to_wait = min(seconds, period_length)
        try:
            to_go = format_seconds_to_hours_minutes(seconds)
            print_func(f'Sleep another {seconds_to_wait:.1f} seconds, (still {to_go} to go)')
            sleep(seconds_to_wait)
        except KeyboardInterrupt:
            print_func(f"Sleep interrupted at {datetime.now()}.")
            raise EndCaptureException("Capture interrupted by user.")

        # synchronize with actual time, make sure not to overshoot the end time
        current_time = time()
        seconds = max(end_time - current_time, 0)
