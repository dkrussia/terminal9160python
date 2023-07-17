import logging

logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('../logfile.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# logger.debug('Это отладочное сообщение')
# logger.info('Это информационное сообщение')
# logger.warning('Это предупреждающее сообщение')
# logger.error('Это сообщение об ошибке')
