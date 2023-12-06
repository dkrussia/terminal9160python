import logging
import pathlib

from config import BASE_DIR, LOG_DIR
from logging.handlers import RotatingFileHandler

pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


def get_logger(name):
    l = logging.getLogger(name)
    l.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(f'{BASE_DIR}/assets/logs/logfile_{name}.log',
                                       'a',
                                       1 * 1024 * 1024,
                                       10)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    l.addHandler(file_handler)
    return l


logger = get_logger('app')
