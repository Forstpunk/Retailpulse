import logging
import sys


def get_logger(
    name: str,
) -> logging.Logger:
    """
    Create or retrieve a configured
    application logger.
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(
        sys.stdout
    )

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(message)s"
        ),
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logger.propagate = False

    return logger