import argparse
import logging
from pathlib import Path
from camera.config import CameraConfig, CONFIG_FILE

logger = logging.getLogger(__name__)


def list_cli(args):
    print(f'Configuration file at: {CONFIG_FILE}')
    storage = CameraConfig().image_save_path
    print(f'Root folder for image storage: {storage}')


def update_cli(args):
    config = CameraConfig()
    if args.key == 'root_path':
        config.image_save_path = Path(args.value)
        config.save()
        logger.info(f"Configuration: Image save path updated to: {config.image_save_path}")


def cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Camera Capture CLI")
    subparsers = parser.add_subparsers(dest='command', required=False)

    # Run subcommand
    run_parser = subparsers.add_parser('run', help='Capture images from cameras')

    # Config subcommand
    config_parser = subparsers.add_parser('config', help='Manage configuration settings')
    config_subparsers = config_parser.add_subparsers(dest='config_action', required=True)

    # config list
    list_parser = config_subparsers.add_parser('list', help='List current configuration settings')
    list_parser.set_defaults(func=list_cli)

    # config update
    update_parser = config_subparsers.add_parser('update', help='Update a configuration setting')
    update_parser.add_argument('key', type=str, help='Configuration key to update')
    update_parser.add_argument('value', type=str, help='New value for the configuration key')
    update_parser.set_defaults(func=update_cli)

    return parser
