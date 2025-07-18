from datetime import datetime, timedelta
import logging
from pathlib import Path
import requests
import sys
import time
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


def capture_all():
    """Capture images from all cameras listed in the camera locations file."""
    ds = load_camera_locations('camera_locations.txt')
    if ds.empty:
        logger.error("No camera locations found.")
        sys.exit(1)

    config = CameraConfig()
    images_root = config.image_save_path
    for index, row in ds.iterrows():
        url = row['url']
        location = row['location']
        logger.info(f"Capturing image for {location} at {url}")
        img_data, img_url = capture(url)
        if img_data:
            save_camera_image(img_data, images_root, location, suffix=Path(img_url).suffix)
        logger.info(f"Finished capturing image for {location}")


def delay_to_next_capture_time(config: CameraConfig) -> tuple[int, datetime]:
    """ Determine the initial start time based on the current time and the configured start time.
        Capture time is calculated at regular intervals since the start time.
        Example: If the start time is 06:30, the interval is 30 minutes and the current time is 07:13,
        the next capture will be at 07:30 (6:30 + 2 * 30).
        Return the seconds to wait before actually starting the capture.
    """
    now = datetime.now()
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
        if remain > 0 and remain < config.interval * 60:
            periods += 1
        target = dt_start + timedelta(minutes=(periods) * config.interval)
        return (target - now).seconds, target


def wait_until_next_capture(seconds: int):
    """
        Wait until the next capture time, allowing for keyboard interrupts.
        Once per hour report remaining time.
    """
    period = 0
    periods = seconds // 3600
    while seconds > 0:
        to_wait = min(seconds+1, 3600)
        try:
            st = time.time()
            if periods > 1:
                print(f"Sleeping for one hour (period {period + 1} of {periods})...")
            time.sleep(to_wait - int(time.time() - st))
        except KeyboardInterrupt:
            print(f"Sleep interrupted at period {period + 1}.")
            raise EndCaptureException("Capture interrupted by user.")
        if periods > 1:
            print(f"Completed sleep period {period + 1} of {periods}.")
        seconds -= to_wait
        period += 1


def capture_all_repeat(capture_mode: int = CAPTURE_TODAY):
    config = CameraConfig()
    day_end = datetime.now().replace(hour=config.end.hour, minute=config.end.minute, second=0, microsecond=0)
    try:
        while True:
            capture_all()
            sleep_time, capture_time = delay_to_next_capture_time(config)
            if (capture_mode == CAPTURE_TODAY) and capture_time > day_end:
                logger.info("Capture finished for today.")
                break
            logger.info(f'Next capture at {capture_time}; Press Ctrl+C to stop.')
            wait_until_next_capture(sleep_time)
    except KeyboardInterrupt:
        logger.info("Stopping repeat capture.")
    except EndCaptureException:
        logger.info("Stopping repeat capture.")


def main():
    parser = cli_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'run':
        logger.info("Capturing once.")
        capture_all()
    elif args.command == 'run_repeat':
        logger.info("Capturing in one day repeat mode. Press Ctrl+C to stop.")
        capture_all_repeat(CAPTURE_TODAY)
    elif args.command == 'run_repeat_no_limit':
        logger.info("Capturing in continuous repeat mode. Press Ctrl+C to stop.")
        capture_all_repeat(NONSTOP_CAPTURE)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
