import logging

# Создание логгера с именем 'my_logger'
logger = logging.getLogger('app')

# Конфигурация логгера
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Создание обработчика для записи в файл
file_handler = logging.FileHandler('logfile.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Добавление обработчика к логгеру
logger.addHandler(file_handler)

# Пример использования
logger.debug('Это отладочное сообщение')
logger.info('Это информационное сообщение')
logger.warning('Это предупреждающее сообщение')
logger.error('Это сообщение об ошибке')