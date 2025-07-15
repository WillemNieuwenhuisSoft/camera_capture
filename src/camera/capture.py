from datetime import datetime
import logging
from pathlib import Path
import requests
from urllib.parse import urljoin
import sys
from bs4 import BeautifulSoup
from camera.config import CameraConfig
from camera.camera_locations import load_camera_locations
from camera.capture_functions import find_camera_title, get_camera_coordinates
from camera.capture_functions import get_latest_image_url, retrieve_image, save_camera_image

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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


def main():
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


if __name__ == "__main__":
    main()
