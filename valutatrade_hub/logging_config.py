
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "actions.log"

LOG_FORMAT = (
    "%(levelname)s %(asctime)s "
    "%(message)s"
)

def setup_logging(level=logging.INFO):
    logger = logging.getLogger("valutatrade")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
