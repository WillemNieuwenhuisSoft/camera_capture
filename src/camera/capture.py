from datetime import time
import logging
from pathlib import Path
import requests
import sys
from bs4 import BeautifulSoup
from camera.config import CameraConfig
from camera.camera_locations import load_camera_locations
from camera.capture_functions import find_camera_title, get_camera_coordinates
from camera.capture_functions import get_latest_image_url, retrieve_image, save_camera_image
from camera.cli_parser import cli_parser

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


def main():
    parser = cli_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'run':
        capture_all()
    elif args.command == 'run_repeat':
        logger.info("Running in repeat mode. Press Ctrl+C to stop.")
        config = CameraConfig()
        interval = config.interval * 60  # Convert minutes to seconds
        try:
            while True:
                start = time.time()
                capture_all()
                elapsed = time.time() - start
                to_sleep = max(0, interval - elapsed)
                time.sleep(to_sleep)
        except KeyboardInterrupt:
            logger.info("Stopping repeat capture.")
    else:
        args.func(args)


if __name__ == "__main__":
    main()
