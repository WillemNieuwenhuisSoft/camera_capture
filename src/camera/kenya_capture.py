'''
kenya_capture.py
This module provides functions to scrape and extract camera information from web pages,
specifically for Kenya camera feeds. It includes utilities to find camera names, titles,
descriptions, Google Earth links, coordinates, and the latest image URLs from HTML content.
It also provides a main capture function to retrieve the latest image and its URL.
Functions:
    capture(page_url: str) -> tuple[bytes, str] | tuple[None, None]
        Main function to capture the latest image and its URL from a given camera page URL.
Internal functions:
    find_camera_name(soup: BeautifulSoup) -> str
        Extracts the camera name from the HTML soup by locating the appropriate comment and its following <h5> tag.
    find_camera_title(soup: BeautifulSoup) -> str
        Extracts the camera title from the HTML soup by locating the appropriate comment and its following <h3> tag.
    find_camera_description(soup: BeautifulSoup) -> str
        Extracts the camera description from the HTML soup by locating the appropriate comment and its following <p> tag.
    find_google_earth_link(soup: BeautifulSoup) -> str
        Finds and returns the Google Earth link from the HTML soup, if present.
    get_camera_coordinates(soup: BeautifulSoup) -> tuple[float, float] | None
        Retrieves the camera's latitude and longitude by expanding the Google Earth short link found in the HTML.
    get_latest_image_url(soup: BeautifulSoup) -> str
        Finds and returns the URL of the latest camera image from the HTML soup.
'''

import logging
import requests
from bs4 import BeautifulSoup
from camera.capture_functions import retrieve_image

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
