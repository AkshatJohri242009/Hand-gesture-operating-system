import json
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    name: str = "apex",
    level: str = "INFO",
    log_dir: str = "storage/logs",
    console: bool = True,
):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(
        log_path / f"{name}.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger
