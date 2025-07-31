import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

CAMERA_LOCATIONS_FILE = Path(__file__).parent / 'camera_locations.txt'


def load_camera_locations(file_path: str) -> pd.DataFrame:
    """
    Load camera locations from a CSV file.

    :param file_path: Path to the CSV file containing camera locations.
    :return: DataFrame containing camera locations.
    """
    try:
        df = pd.read_csv(file_path)
        if 'url' not in df.columns or 'location' not in df.columns:
            raise ValueError("Data file must contain 'url' and 'location' columns.")
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df = df.dropna()
        return df
    except Exception as e:
        logger.error(f"Error loading camera locations: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error
