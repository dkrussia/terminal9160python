import logging
import pathlib

from config import BASE_DIR, LOG_DIR
from logging.handlers import RotatingFileHandler

pathlib.Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = RotatingFileHandler(f'{BASE_DIR}/assets/logs/logfile.log', 'a', 1 * 1024 * 1024, 10)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
