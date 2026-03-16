"""
Centralized logging setup for the project.

Usage — call once at the very start of any entry point:

    from utils.logger import setup_logging
    setup_logging()

Then in any module just use:

    import logging
    logger = logging.getLogger(__name__)
    logger.info("...")
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# ── Constants ──────────────────────────────────────────────────────────────────
LOG_DIR  = Path("logs")
LOG_FMT  = "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_dir: Path = LOG_DIR,
    filename: str | None = None,
) -> None:
    """
    Configure root logger to stream to both terminal and a rotating log file.

    Args:
        level:    logging level (default: INFO)
        log_dir:  directory where log files are stored (default: logs/)
        filename: log file name (default: YYYY-MM-DD_HH-MM-SS.log)
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"

    log_path = log_dir / filename

    formatter = logging.Formatter(fmt=LOG_FMT, datefmt=DATE_FMT)

    # ── Terminal handler ───────────────────────────────────────────────────────
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    # ── File handler ───────────────────────────────────────────────────────────
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # ── Root logger ────────────────────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(level)

    # Avoid adding duplicate handlers if called more than once
    if not root.handlers:
        root.addHandler(stream_handler)
        root.addHandler(file_handler)
    else:
        root.handlers.clear()
        root.addHandler(stream_handler)
        root.addHandler(file_handler)

    logging.info("Logging initialised → %s", log_path)