""" Logging utils """

import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def get_logger(name: str) -> logging.Logger:
    """Returns configured logger"""
    return logging.getLogger(name)
