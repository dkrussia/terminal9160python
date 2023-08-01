import json
import logging
import time
import amqpstorm
from amqpstorm import AMQPChannelError, AMQPConnectionError
from base.utils import catch_exceptions

from config import s as settings

logger = logging.getLogger('rmq_log')
logger.setLevel(logging.INFO)


# TODO: обработка случая когда RabbitMQ включен\выключен


def create_connection():
    attempts = 0
    connection = None
    max_retries = 3
    while True:
        attempts += 1
        try:
            connection = amqpstorm.Connection(
                hostname=settings.RMQ_HOST,
                username=settings.RMQ_USER,
                password=settings.RMQ_PASSWORD,
                port=settings.RMQ_PORT,
            )
            break
        except amqpstorm.AMQPError as why:
            logger.error(why)
            if max_retries and attempts > max_retries:
                break
            time.sleep(1)
        except KeyboardInterrupt:
            break
    return connection


class MyChannel(object):
    def __init__(self):
        self.connection = create_connection()

    def __enter__(self):
        return self.connection.channel()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()


@catch_exceptions(cancel_on_failure=False)
def rmq_publish_message(queue, exchange, data, headers=None):
    ttl = 30
    arguments = {'x-message-ttl': ttl * 1000} if 'ping' in queue else {}

    with MyChannel() as channel:
        if queue:
            channel.queue.declare(queue, arguments=arguments)
        prop = {
            'delivery_mode': 2,
            'headers': headers,
            'content_type': 'application/json'
        }
        channel.basic.publish(
            routing_key=queue,
            exchange=exchange,
            body=json.dumps(data),
            properties=prop,
        )


@catch_exceptions(cancel_on_failure=False)
def rmq_send_reply_to(reply_to, data):
    with MyChannel() as channel:
        logger.info(f'Ответ на {reply_to} отправлен.')
        channel.basic.publish(
            routing_key=reply_to,
            body=json.dumps(data),
            properties={
                'content_type': 'application/json'
            },
        )


def rmq_subscribe_on_mci_command(sn_device, func):
    queue = f'commands_{sn_device}'
    rmq_global_chanel.queue.declare(queue)
    rmq_global_chanel.basic.consume(func, queue, no_ack=True)


def rmq_start_consume():
    while True:
        try:
            # Проверить chanel и сделать reconnect при необходимости
            # chanel.is_open
            rmq_global_chanel.start_consuming()
        except AMQPChannelError as why:
            time.sleep(3)
            print(why)
        except AMQPConnectionError as why:
            time.sleep(3)
            print(why)


rmq_connect = create_connection()
rmq_global_chanel = rmq_connect.channel()
