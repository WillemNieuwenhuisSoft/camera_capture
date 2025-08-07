from datetime import datetime
import logging
from pathlib import Path
import requests
import sys
import pandas as pd
from time import sleep, time
from bs4 import BeautifulSoup
from camera.config import CameraConfig
from camera.camera_locations import load_urls_from_file
from camera.kenya_capture import capture
from camera.capture_functions import save_camera_image
from camera.timing_functions import determine_delay_to_next_capture_time, wait_until_next_capture
from camera.timing_functions import EndCaptureException
from camera.cli_parser import cli_parser

CAPTURE_TODAY = 1
NONSTOP_CAPTURE = 2


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
