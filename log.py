import logging
import os


def get_logger(name=None):

    default = __name__

    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger(default)

    logger.setLevel("INFO")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%H:%M:%S"))
    logger.addHandler(handler)

    return logger