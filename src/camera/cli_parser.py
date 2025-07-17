import argparse
from datetime import time
import logging
from pathlib import Path
from camera.config import CameraConfig, CONFIG_FILE

logger = logging.getLogger(__name__)


def list_cli(args):
    print(f'Configuration file at: {CONFIG_FILE}')
    cfg = CameraConfig()
    rows = list(cfg.fields())
    maxlen_name = max(len(name) for name, _, _ in rows)
    maxlen_value = max(len(str(value)) for _, value, _ in rows)
    for name, value, desc in rows:
        print(f"{name.ljust(maxlen_name)} : {str(value).ljust(maxlen_value)} # {desc}")


def update_cli(args):
    config = CameraConfig()
    if args.key == 'image_save_path':
        config.image_save_path = Path(args.value)
        config.save()
        logger.info(f"Configuration: Image save path updated to: {config.image_save_path}")
    if args.key == 'interval':
        try:
            config.capture_interval = int(args.value)
            if config.capture_interval < 15 or config.capture_interval > 6*60:
                logger.error("Allowed capture interval range: 15 to 360 minutes.")
                return
            config.save()
            logger.info(f"Configuration: Capture interval updated to: {config.capture_interval} minutes")
        except ValueError:
            logger.error("Invalid value for capture interval. Must be an integer.")
    if args.key == 'start' or args.key == 'end':
        try:
            hour, minute, *_ = map(int, args.value.split(':'))
            setattr(config, args.key, time(hour=hour, minute=minute))
            if config.start >= config.end:
                logger.error("Start time must be before end time.")
                return
            config.save()
            msg = f"Configuration: {args.key} time updated to: {getattr(config, args.key)}"
            logger.info(msg)
        except ValueError as e:
            msg = f"Invalid time for {args.key} time; {e}."
            logger.error(msg)


def cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Camera Capture CLI")
    subparsers = parser.add_subparsers(dest='command', required=False)

    # Run subcommands
    runonce_parser = subparsers.add_parser('run', help='Capture images from cameras')
    repeat_parser = subparsers.add_parser(
        'run_repeat_no_limit', help='Repeat capturing images from cameras at specified intervals indefinitely')
    repeat_day_parser = subparsers.add_parser(
        'run_repeat', help='Repeat capturing images from cameras at specified intervals for the current day')

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
