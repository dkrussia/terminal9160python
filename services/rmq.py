import json

import amqpstorm

from config import RMQ_HOST, RMQ_USER, RMQ_PASSWORD, RMQ_PORT


class RMQChannel(object):
    def __init__(self):
        self.connection = amqpstorm.Connection(
            hostname=RMQ_HOST,
            username=RMQ_USER,
            password=RMQ_PASSWORD,
            port=RMQ_PORT,
        )

    def __enter__(self):
        return self.connection.channel()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()


def publish_request(queue, exchange, data, headers=None):
    ttl = 30
    arguments = {}
    if 'ping' in queue:
        arguments = {'x-message-ttl': ttl * 1000}

    with RMQChannel() as channel:
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
