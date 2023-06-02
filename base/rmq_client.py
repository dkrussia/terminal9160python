import json
import logging
import time
import amqpstorm

from amqpstorm import AMQPChannelError

from config import (
    RMQ_HOST,
    RMQ_USER,
    RMQ_PASSWORD,
    RMQ_PORT
)

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
                hostname=RMQ_HOST,
                username=RMQ_USER,
                password=RMQ_PASSWORD,
                port=RMQ_PORT,
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


class Channel(object):
    def __init__(self):
        self.connection = create_connection()

    def __enter__(self):
        return self.connection.channel()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()


def rmq_publish_message(queue, exchange, data, headers=None):
    ttl = 30
    arguments = {'x-message-ttl': ttl * 1000} if 'ping' in queue else {}

    with Channel() as channel:
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


def rmq_send_reply_to(reply_to, data):
    with Channel() as channel:
        logger.info(f'Ответ на {reply_to} отправлен.')
        channel.basic.publish(
            routing_key=reply_to,
            body=json.dumps(data),
            properties={
                'content_type': 'application/json'
            },
        )


def rmq_start_consume(chanel):
    while True:
        try:
            chanel.start_consuming()
        except AMQPChannelError as e:
            time.sleep(1)
            print(e)


rmq_connect = create_connection()
rmq_global_chanel = rmq_connect.channel()


def rmq_subscribe_on_mci_command(sn_device, func):
    queue = f'commands_{sn_device}'
    rmq_global_chanel.queue.declare(queue)
    rmq_global_chanel.basic.consume(func, queue)
