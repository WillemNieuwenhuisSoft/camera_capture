import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def create_default_config(profile_dir: Path, config_path: Path):
    save_folder = profile_dir / 'camera_images'
    default_config = {
        'image_save_path': str(save_folder)
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4)
    logger.info(f"Captured images will be stored in '{save_folder}'.")


def load_config() -> dict:
    """
    Load configuration from 'camera.config' in the user's profile directory.
    Returns the config as a dict, or an empty dict if not found.
    The dict contains at least the location of the root folder to save all images to.
    """
    profile_dir = os.environ.get('USERPROFILE') or os.environ.get('HOME')
    config_path = Path(profile_dir) / 'camera.config'
    if not config_path.exists():
        logger.warning(f"Config file '{config_path}' does not exist. Creating default config.")
        create_default_config(profile_dir, config_path)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        logger.warning(f"Could not load config file '{config_path}': {e}")
        return {}
