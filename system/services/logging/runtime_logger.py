"""Runtime logging setup for NeXa ToTem."""

import logging
from pathlib import Path


def setup_runtime_logger(name="nexa_totem", log_dir="var/log", console=True, level=logging.INFO):
    """Create a logger that can write to var/log and optionally to the console."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path / f"{name}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
