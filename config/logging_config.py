from loguru import logger
import sys

logger.remove()  # delete default logger

# app config
logger.add(
    sys.stdout,
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {file} - {line} - {level} - {message}",
    filter=lambda record: record["extra"].get("name") == "app",
    enqueue=True,
)

logger.add(
    "logs/app_debug.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {file} - {line} - {level} - {message}",
    rotation="50 MB",
    retention=5,
    filter=lambda record: record["extra"].get("name") == "app",
    enqueue=True,
)

logger.add(
    "logs/app_error.log",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {file} - {line} - {level} - {message}",
    rotation="5 MB",
    retention=5,
    filter=lambda record: record["extra"].get("name") == "app",
    enqueue=True,
)

# tests config
logger.add(
    sys.stdout,
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {file} - {line} - {level} - {message}",
    filter=lambda record: record["extra"].get("name") == "tests",
    enqueue=True,
)

logger.add(
    "logs/tests_debug.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {file} - {line} - {level} - {message}",
    rotation="50 MB",
    retention=5,
    filter=lambda record: record["extra"].get("name") == "tests",
    enqueue=True,
)

logger.add(
    "logs/tests_error.log",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {file} - {line} - {level} - {message}",
    rotation="5 MB",
    retention=5,
    filter=lambda record: record["extra"].get("name") == "tests",
    enqueue=True,
)
