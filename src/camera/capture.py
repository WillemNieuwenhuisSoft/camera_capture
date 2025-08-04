from datetime import datetime, timedelta
import logging
from pathlib import Path
import requests
import sys
import pandas as pd
from time import sleep, time
from bs4 import BeautifulSoup
from camera.config import CameraConfig
from camera.camera_locations import load_camera_locations
from camera.capture_functions import find_camera_title, get_camera_coordinates
from camera.capture_functions import get_latest_image_url, retrieve_image, save_camera_image
from camera.cli_parser import cli_parser

CAPTURE_TODAY = 1
NONSTOP_CAPTURE = 2


class EndCaptureException(Exception):
    """Exception to signal the user ended the capture process."""
    pass


logger = logging.getLogger(__name__)


def capture(page_url: str) -> tuple[bytes, str] | tuple[None, None]:
    response = requests.get(page_url)
    if response.status_code != 200:
        logger.error(f'Unable to access "{page_url}"')
        return (None, None)

    # make sure to use the correct encoding
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')

    collect = {}
    station_name = find_camera_title(soup)
    logger.info(f"Camera Name:, {station_name}")
    collect['name'] = station_name
    collect['url'] = page_url

    lat_lon = get_camera_coordinates(soup)

    img_url = get_latest_image_url(soup)

    img_data = retrieve_image(img_url)

    return img_data, img_url


def load_urls_from_file(config: CameraConfig) -> pd.DataFrame:
    """Load camera URLs from the camera locations file."""
    camera_locations_file = config.location_file
    if not camera_locations_file.exists():
        logger.error(f"Camera locations file does not exist: {camera_locations_file}")
        ds = pd.DataFrame(columns=["url", "location"])
    else:
        ds = load_camera_locations(camera_locations_file)
        if ds.empty:
            logger.error("No camera locations found.")

    return ds


def capture_all(all_urls: pd.DataFrame, config: CameraConfig) -> None:
    """Capture images from all cameras in the camera locations file."""
    images_root = config.image_save_path
    for index, row in all_urls.iterrows():
        url = row['url']
        location = row['location']
        logger.info(f"Capturing image for {location} at {url}")
        img_data, img_url = capture(url)
        if img_data:
            save_camera_image(img_data, images_root, location, suffix=Path(img_url).suffix)
        logger.info(f"Finished capturing image for {location}")


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


def print_sleep_message(seconds: int, periods: int, period: int, print_func=print) -> None:
    """
    Print a message indicating how long the program will sleep.
    """
    wait_time_msg = format_seconds_to_hours_minutes(seconds)
    msg = [f"Sleeping for {wait_time_msg}"]
    if periods > 1:
        msg.append(f"(period {period} of {periods})...")
    print_func(" ".join(msg))


def wait_until_next_capture(seconds: int, period_length: int = 3600, print_func=print) -> None:
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
    periods = (seconds // period_length)
    period = 1
    current_time = time()
    end_time = current_time + seconds
    while end_time > current_time:
        seconds_to_wait = min(seconds, period_length)
        try:
            print_sleep_message(seconds_to_wait, periods, period, print_func)
            sleep(seconds_to_wait)
        except KeyboardInterrupt:
            print_func(f"Sleep interrupted at period {period}.")
            raise EndCaptureException("Capture interrupted by user.")
        if periods > 1:
            print_func(f"Completed sleep period {period} of {periods}.")

        # synchronize with actual time, make sure not to overshoot the end time
        current_time = time()
        seconds = max(end_time - current_time, 0)
        if seconds > 1:
            period += 1


def capture_all_repeat(all_urls: pd.DataFrame, config: CameraConfig, capture_mode: int = CAPTURE_TODAY) -> bool:
    now = datetime.now()
    wait_period_length = 600    # 10 minutes, to allow for periodic updates
    day_end = now.replace(hour=config.end.hour, minute=config.end.minute, second=0, microsecond=0)
    success = False
    try:
        while True:
            capture_all(all_urls, config)
            sleep_time, capture_time = determine_delay_to_next_capture_time(config, now)
            if (capture_mode == CAPTURE_TODAY) and capture_time > day_end:
                logger.info("Capture finished for today.")
                success = True
                break
            logger.info(f'Next capture at {capture_time}; Press Ctrl+C to stop.')
            wait_until_next_capture(sleep_time, wait_period_length,
                                    print_func=print if config.verbose else (lambda *a, **k: None))
            now = datetime.now()
    except KeyboardInterrupt:
        logger.info("Stopping repeat capture.")
    except EndCaptureException:
        logger.info("Stopping repeat capture.")

    return success


def main():
    parser = cli_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = CameraConfig()  # Load the configuration

    if str(args.command).startswith('run'):
        all_urls = load_urls_from_file(config)
        if all_urls.empty:
            logger.error("No camera URLs found. Please check the camera locations file.")
            sys.exit(1)

    if args.verbose:
        config.verbose = True

    if args.command == 'run':
        logger.info("Capturing once.")
        capture_all(all_urls, config)
    elif args.command == 'run_repeat':
        logger.info("Capturing in one day repeat mode. Press Ctrl+C to stop.")
        capture_all_repeat(all_urls, config, CAPTURE_TODAY)
    elif args.command == 'run_repeat_no_limit':
        logger.info("Capturing in continuous repeat mode. Press Ctrl+C to stop.")
        capture_all_repeat(all_urls, config, NONSTOP_CAPTURE)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
