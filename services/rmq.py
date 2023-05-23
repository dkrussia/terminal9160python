import json

import amqpstorm
from amqpstorm import Connection
from pydantic import typing

from config import RMQ_HOST, RMQ_USER, RMQ_PASSWORD, RMQ_PORT


class RMQChannel(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RMQChannel, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'connection'):
            self.connection = Connection(
                hostname=RMQ_HOST,
                username=RMQ_USER,
                password=RMQ_PASSWORD,
                port=RMQ_PORT,
            )
            self.channels = []

    def __enter__(self):
        channel = self.connection.channel()
        self.channels.append(channel)
        return channel

    def __exit__(self, exc_type, exc_value, traceback):
        for channel in self.channels:
            if channel:
                channel.close()

    def consume_queue(self, queue_name, func):
        channel = self.connection.channel()
        channel.queue.declare(queue_name)
        channel.basic.consume(func, queue_name, no_ack=True)
        channel.start_consuming()


rmq_channel = RMQChannel()


def rmq_publish_message(queue, exchange, data, headers=None):
    ttl = 30
    arguments = {'x-message-ttl': ttl * 1000} if 'ping' in queue else {}

    with rmq_channel as channel:
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
