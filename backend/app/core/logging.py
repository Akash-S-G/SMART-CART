import logging
import logging.config
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": (
                "%(asctime)s | %(levelname)s | "
                "%(name)s | %(message)s"
            )
        },
        "access": {
            "format": (
                "%(asctime)s | %(levelname)s | "
                "%(clientip)s | %(request_line)s | %(status_code)s"
            )
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "formatter": "default",
        },
    },
    "loggers": {
        # Suppress uvicorn/watchfiles reload spam like:
        # "watchfiles.main | 1 change detected"
        "watchfiles.main": {
            "level": "WARNING",
            "propagate": False,
        },
        # (Optional) also reduce uvicorn noise if present.
        "uvicorn.error": {
            "level": "WARNING",
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": [
            "console",
            "file",
        ],
        "level": "INFO",
    },
}


logging.config.dictConfig(LOGGING_CONFIG)


logger = logging.getLogger("smartcart")