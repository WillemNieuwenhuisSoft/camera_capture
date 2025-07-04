from datetime import datetime
from pathlib import Path
import logging
import os
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def find_camera_name(soup: BeautifulSoup) -> str:
    comment = soup.find(string=lambda text: "InstanceBeginEditable name=\"locationinfo\"" in text)
    if comment:
        # Get the next sibling <h5> tag after the comment
        next_h5_tag = comment.find_next("h5")
        if next_h5_tag:
            return next_h5_tag.get_text(strip=True)
    return ''


def find_camera_title(soup: BeautifulSoup) -> str:
    comment = soup.find(string=lambda text: "InstanceBeginEditable name=\"webcamtitle\"" in text)
    if comment:
        # Get the next sibling <h3> tag after the comment
        next_h3_tag = comment.find_next("h3")
        if next_h3_tag:
            return next_h3_tag.get_text(strip=True)
    return ''


def find_camera_description(soup: BeautifulSoup) -> str:
    comment = soup.find(string=lambda text: "InstanceBeginEditable name=\"notes\"" in text)
    if comment:
        # Get the next sibling <p> tag after the comment
        next_p_tag = comment.find_next("p")
        if next_p_tag:
            return next_p_tag.get_text(strip=True)
    return ''


def dms_to_decimal(dms_str: str) -> float | None:
    """Convert DMS (Degrees, Minutes, Seconds) to decimal format."""
    match = re.match(r"(\d+)°(\d+)'([\d.]+)\"([NSEW])", dms_str)
    if not match:
        return None
    degrees, minutes, seconds, direction = match.groups()
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if direction in "SW":
        decimal = -decimal
    return decimal


def find_coordinates(soup: BeautifulSoup) -> tuple[tuple[str | None, str | None], tuple[float | None, float | None]]:
    coord_str = soup.find('h5', class_='mt-0 mb-2').find_next_sibling().text
    regex = r"(\d+°\d+'\d+\.\d+\"[NS])\s+(\d+°\d+'\d+\.\d+\"[EW])"
    coord = re.search(regex, coord_str)
    if coord:
        dms_lat, dms_lon = coord.groups()
        # Convert to decimal format
        decimal_lat = dms_to_decimal(dms_lat)
        decimal_lon = dms_to_decimal(dms_lon)
        return ((dms_lat, dms_lon), (decimal_lat, decimal_lon))
    return ((None, None), (None, None))


def retrieve_image(img_url: str) -> bytes | None:
    """Retrieve the image from the given URL."""
    if not img_url:
        return None

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(img_url, headers=headers)
    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
        return response.content
    else:
        logger.info(f"Url does not link to an image: '{img_url}'")
        return None


def save_camera_image(img_data: bytes, img_filename: str):
    """Save the camera image to a file."""
    with open(img_filename, 'wb') as f:
        f.write(img_data)
    logger.info(f"Image saved as {img_filename}")


def capture(url: str):
    # Step 1: Load the page
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Unable to access {url}")
        return

    # make sure to use the correct encoding
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')

    collect = {}
    station_name = find_camera_title(soup)
    logger.info(f"Camera Name:, {station_name}")
    collect['name'] = station_name
    collect['url'] = url

    # Step 2: Find all images and determine uploaded one
    img_tags = soup.find_all('img')

    for img_tag in img_tags:
        if 'src' in img_tag.attrs:
            img_url = urljoin(url, img_tag['src'])
            if 'upload' in img_url:
                logger.info(f"Found image: {img_url}")
                break

    # Step 3: Extract coordinates
    lat_lon, dms = find_coordinates(soup)
    if lat_lon[0]:
        logger.info(f"Coordinates (DMS): {lat_lon}")
        logger.info(f"Coordinates (Decimal): {dms}")
    else:
        logger.info("Coordinates not found.")

    # Step 4: get the image
    img_data = retrieve_image(img_url)
    if img_data is None:
        return

    # Step 5: Determine the local name and save the image
    # using the current system time, not the stamped time in the image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    img_filename = f"{station_name}_{timestamp}{Path(img_url).suffix}"
    save_camera_image(img_data, img_filename)


if __name__ == "__main__":
    capture(url="https://webcams.aeroclubea.com/Nairobi/nbo_wilsonE.html")
