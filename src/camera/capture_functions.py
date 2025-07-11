from html import unescape
import logging
from pathlib import Path
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from camera.camera_locations import load_camera_locations

logger = logging.getLogger(__name__)


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


def find_google_earth_link(soup: BeautifulSoup) -> str:
    """
    Find the Google Earth link in the HTML soup.
    The link is expected to be in a <a> tag within a div with class 'mt-0 mb-1'.
    The div tag contains the text "View on".
    the <a> tag has the text "Google Earth".
    <div class="mt-0 mb-1">View on <a href="https://earth.app.goo.gl/ncGPi9" target="_blank"><img src="../images/Logos/New-Google-Earth-logo.png" width="40" height="40" alt="">Google Earth </a></div>
    """
    # look for all <a> tags and extract the link when the text is "Google Earth"
    a_tags = soup.find_all('a')
    for a_tag in a_tags:
        if a_tag.get_text(strip=True) == "Google Earth":
            if a_tag.has_attr('href'):
                return a_tag['href']

    return ''


def get_camera_coordinates(soup: BeautifulSoup) -> tuple[float, float] | None:
    """
    Get the camera coordinates from the current page.
    Look for a google link; assume it is a google earth short link, such as
    example: https://earth.app.goo.gl/g2XVph
    Then expand the link to get the full URL, which contains the coordinates.

    :param soup: webscraper object.
    :return: coordinate tuple or None.
    """

    # first look for the google earth link
    link = find_google_earth_link(soup)
    if not link:
        logger.warning("No Google Earth link found.")
        return None

    # expand the shortened URL to get the full URL
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.head(link, allow_redirects=True, headers=headers)

    # find the coordinates in the expanded URL
    params = response.url.split('@')
    parts = params[1].split(',')
    if len(parts) >= 2:
        lat = parts[0]
        lon = parts[1]
        logger.info(f"Coordinates (decimal): {lat=}, {lon=}")

        return (lat, lon)

    logger.warning("Unable to detect coordinates.")
    return None


def get_latest_image_url(soup: BeautifulSoup) -> str:
    img_tags = soup.find_all('img')

    img_url = None
    for img_tag in img_tags:
        if 'src' in img_tag.attrs:
            img_url = img_tag['src']
            if ('upload' in img_url) or ('stream' in img_url):
                logger.info(f"Found image: {img_url}")
                break

    if img_url is None:
        logger.info(f"No image found")

    return img_url


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


def save_camera_image(img_data: bytes, img_filename: Path):
    """Save the camera image to a file."""
    with open(img_filename, 'wb') as f:
        f.write(img_data)
    logger.info(f"Image saved as {img_filename}")
