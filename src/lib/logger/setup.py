import json
from logging.config import dictConfig


def setup_logging(path: str) -> None:
    with open(path, "rt") as f:
        config = json.load(f)
    dictConfig(config)
