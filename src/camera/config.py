from dataclasses import dataclass, field
from datetime import datetime, time
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_FILE = Path.home() / 'camera.config'


@dataclass
class CameraConfig:
    image_save_path: Path = field(default_factory=lambda: Path.home() / 'camera_images')
    start: time = time(hour=6, minute=30)
    end: time = time(hour=18, minute=30)
    interval: int = 30  # in minutes
    location_file: Path = field(default_factory=lambda: Path.home() / 'camera_locations.txt')
    verbose: bool = False  # Whether to print verbose output

    # Add a mapping for user-friendly descriptions
    FIELD_DESCRIPTIONS = {
        "image_save_path": "Root folder where captured images are stored",
        "start": "Start time for capturing images (HH:MM)",
        "end": "End time for capturing images (HH:MM)",
        "interval": "Interval in minutes between captures (15 to 360 minutes)",
        "location_file": "Name of the file containing the names of camera locations and their URLs",
        "verbose": "Enable verbose output for debugging and information"
    }

    def __post_init__(self):
        self.load()

    def _create_default_config(self):
        '''Create a default configuration file; assumes itdoes not exist.'''
        save_folder = Path.home() / 'camera_images'
        location_file = Path.home() / 'camera_locations.txt'
        default_config = {
            'image_save_path': str(save_folder),
            'location_file': str(location_file)
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
            self.location_file = Path(config_data.get('locations_file'))
            self.start = time.fromisoformat(config_data.get('start', '06:30'))
            self.end = time.fromisoformat(config_data.get('end', '18:30'))
            self.interval = config_data.get('interval', 30)

    def save(self):
        config_data = {
            'image_save_path': str(self.image_save_path),
            'start': self.start.strftime('%H:%M'),
            'end': self.end.strftime('%H:%M'),
            'interval': self.interval,
            'locations_file': str(self.location_file)
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        logger.info(f"Configuration saved to '{CONFIG_FILE}'.")

    def fields(self):
        """Yield (field_name, value, description) for each config field.
           This is used to display configuration options in the CLI user interface.
        """
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            desc = self.FIELD_DESCRIPTIONS.get(field_name, "")
            yield field_name, value, desc
