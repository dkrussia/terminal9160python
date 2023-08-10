import json
import logging
from aio_pika import connect_robust, Message
from base.utils import catch_exceptions

from config import s as settings

logger = logging.getLogger('rmq_log')
logger.setLevel(logging.INFO)


async def process_rabbitmq_message(queue_name, message: Message):
    print(f"Received from queue {queue_name}: {message.body.decode()}")
    # Здесь вы можете обработать сообщение из RabbitMQ


class RabbitMQHandler:
    def __init__(self, amqp_url):
        self.amqp_url = amqp_url
        self.connection = None

    async def start(self):
        self.connection = await connect_robust(self.amqp_url)

    async def stop(self):
        if self.connection:
            await self.connection.close()

    async def publish_message(self, q_name, message):
        channel = await self.connection.channel()
        queue = await channel.declare_queue(q_name, auto_delete=True)
        await channel.default_exchange.publish(
            Message(message.encode(), content_type='application/json'),
            routing_key=queue.name,
        )

    async def start_queue_listener(self, queue_name, ):
        channel = await self.connection.channel()
        queue = await channel.declare_queue(queue_name)
        await queue.consume(lambda msg: process_rabbitmq_message(queue_name, msg))


rabbit_mq = RabbitMQHandler("amqp://guest:guest@127.0.0.1/", )


# async def start_queue_listener(self, queue_name):
#     channel = await self.connection.channel()
#     queue = await channel.declare_queue(queue_name)
#     await queue.consume(lambda msg: p


def create_connection():
    pass


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
    # Проверить chanel и сделать reconnect при необходимости
    # chanel.is_open
    rmq_global_chanel.start_consuming()


rmq_connect = None
rmq_global_chanel = None
