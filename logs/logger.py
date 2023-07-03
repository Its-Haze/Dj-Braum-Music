import logging.config
import os

import yaml


def setup_logging(path: str = "config.yaml"):
    """
    Sets up a logger from a configuration file.
    """
    # Directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Path to the configuration file
    config_path = os.path.join(script_dir, path)

    with open(config_path, "rt", encoding="utf-8") as file:
        config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)
