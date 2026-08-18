import logging
from pathlib import Path

from app.config import settings


# =========================================================
# CONFIG
# =========================================================

LOG_DIR = Path(
    settings.log_dir
)

LOG_FILE = (
    LOG_DIR
    / "app.log"
)


# =========================================================
# SETUP LOGGING
# =========================================================

def setup_logging() -> None:

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                LOG_FILE,
                encoding="utf-8",
            ),
        ],
        force=True,
    )