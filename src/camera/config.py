from dataclasses import dataclass, field
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_FILE = Path.home() / 'camera.config'


@dataclass
class CameraConfig:
    image_save_path: Path = field(default_factory=lambda: Path.home() / 'camera_images')

    def __post_init__(self):
        self.load()

    def _create_default_config(self):
        '''Create a default configuration file; assumes itdoes not exist.'''
        save_folder = Path.home() / 'camera_images'
        default_config = {
            'image_save_path': str(save_folder)
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        logger.info(f"Captured images will be stored in '{save_folder}'.")

    def load(self):
        if not CONFIG_FILE.exists():
            logger.warning(f"Config file '{CONFIG_FILE}' does not exist. Creating default config.")
            self._create_default_config()

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            self.image_save_path = Path(config_data.get('image_save_path'))

    def save(self):
        config_data = {
            'image_save_path': str(self.image_save_path)
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        logger.info(f"Configuration saved to '{CONFIG_FILE}'.")
