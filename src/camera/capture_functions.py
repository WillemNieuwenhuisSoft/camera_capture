from datetime import datetime, date
import logging
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


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


def update_folder_tree(images_root: Path, station_name: str) -> Path:
    ''' Images are saved using a hierarchy by station/year/month/day
        This function ensures that the folder structure exists.

        :param station_name: name of the station location for the tree
    '''
    today = date.today()
    tree_path = images_root / station_name / str(today.year) / str(today.month) / str(today.day)
    if not tree_path.exists():
        tree_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created image folder: {tree_path}")

    return tree_path


def save_camera_image(img_data: bytes, images_root: Path, station: str, suffix: str) -> None:
    """Save the camera image to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    img_folder = update_folder_tree(images_root, station)
    img_filename = img_folder / f"{station}_{timestamp}{suffix}"

    with open(img_filename, 'wb') as f:
        f.write(img_data)
    logger.info(f"Image saved as {img_filename}")
