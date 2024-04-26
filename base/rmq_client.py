import asyncio
import json
import random
from datetime import datetime
from typing import Union

from aio_pika import connect_robust, IncomingMessage, Message
from aiormq import ChannelInvalidStateError

from base import mqtt_api
from config import s as settings

from base.log import logger


# {"id": 1, "firstName": "Sergey1", "lastName": "Kuz1", "picture": "1"}
# [{"id": 1, "firstName": "Sergey2", "lastName": "Kuz2", "picture": ""}]

async def command_rmq_handler(queue_name, message: IncomingMessage):
    """
    Типы команд
    1. user_update_biophoto -
    2. user_update -
    3. multiuser_update_biophoto +
    4. multiuser_update -
    5. user_delete +
    """
    i = random.randint(1000, 10000)
    print(f'{i}-{queue_name}-start', datetime.now())
    try:
        async with message.process():
            type_command = message.headers.get("command_type")
            reply_to = message.reply_to
            rmq_payload: Union[dict, list] = json.loads(message.body.decode('utf-8'))
            sn_device = queue_name.split("_")[-1]
            try:
                t1 = datetime.now()
                result = None

                if type_command == 'user_update_biophoto':
                    if rmq_payload["id"].isdigit():
                        result = await mqtt_api.create_or_update(
                            sn_device=sn_device,
                            id_person=int(rmq_payload["id"]),
                            firstName=rmq_payload["firstName"],
                            lastName=rmq_payload["lastName"],
                            photo=rmq_payload.get('picture', ""),
                            cardNumber=rmq_payload["cardNumber"]
                        )

                if type_command == 'multiuser_update_biophoto':
                    rmq_payload = list(filter(lambda p: p["id"].isdigit(), rmq_payload))
                    result = await mqtt_api.batch_create_or_update(sn_device=sn_device,
                                                                   persons=rmq_payload,
                                                                   batch_size=settings.BATCH_UPDATE_SIZE)

                if type_command == 'user_delete':
                    if rmq_payload["id"].isdigit():
                        result = await mqtt_api.delete_person(sn_device=sn_device,
                                                              id=int(rmq_payload["id"]))

                if type_command == 'multiuser_delete':
                    result = await mqtt_api.delete_person(sn_device=sn_device)

                error_result = {
                    "result": 'Error',
                    'Return': "-1",
                    'details': result.get("has_error", None) if result else 'Not details'
                }
                success_result = {
                    "result": 'Successful',
                    'Return': "0",
                    'details': result.get("has_error", None) if result else 'Not details'
                }

                if not result or result["has_error"]:
                    await rabbit_mq.publish_message(
                        q_name=reply_to,
                        reply_to=reply_to,
                        message=json.dumps(error_result),
                        correlation_id=message.correlation_id
                    )
                else:
                    await rabbit_mq.publish_message(
                        q_name=reply_to,
                        reply_to=reply_to,
                        message=json.dumps(success_result),
                        correlation_id=message.correlation_id
                    )
                t2 = datetime.now()

                print(f'Total: {type_command}-{(t2 - t1).total_seconds()}')
                logger.info(
                    f' [{len(rmq_payload) if type(rmq_payload) is list else 1}]'
                    f' ~{type_command}'
                    f' SN={sn_device} total={(t2 - t1).total_seconds()}s'
                    f' start={t1.strftime("%H:%M:%S")}'
                    f' end={t2.strftime("%H:%M:%S")}'
                )
                print(f'{i}-{queue_name}-end', datetime.now())
            except Exception as e:
                logger.error(f"Proces command when call command_rmq_handler error {e}")

    except ChannelInvalidStateError:
        # Reconnect consumer?
        logger.error(f"ChannelInvalidStateError => sn={sn_device} | type_command={type_command}")
    except Exception as e:
        logger.error(f"Not recognized when call command_rmq_handler() error {e}")


class RabbitMQClient:
    def __init__(self, amqp_url):
        self.amqp_url = amqp_url
        self.connection = None
        self.on_reconnect_rmq = None

    async def start(self, on_reconnect_rmq):
        self.on_reconnect_rmq = on_reconnect_rmq
        await self.connect()

    async def connect(self):
        while True:
            try:
                self.connection = await connect_robust(self.amqp_url)
                self.on_reconnect_rmq()
                print("Connected to RabbitMQ")
                break  # Exit the loop if connected successfully
            except Exception as e:
                print(f"Connection failed: {e}")
                await asyncio.sleep(5)  # Wait before attempting reconnection

    async def monitor_connection(self):
        while True:
            try:
                if self.connection:
                    await self.connection.ready()
            except Exception as e:
                print('Monitor connection reconnect')
                await self.connect()
            await asyncio.sleep(2)

    async def stop(self):
        if self.connection:
            await self.connection.close()

    async def publish_message(self, q_name, message, reply_to=None, correlation_id=None):
        # add timeout expired for ping queue
        async with self.connection.channel() as channel:
            if reply_to:
                await channel.default_exchange.publish(
                    Message(
                        message.encode(),
                        reply_to=reply_to,
                        correlation_id=correlation_id,
                        content_type='application/json'
                    ),
                    routing_key=reply_to,
                )
                return

            arguments = {}
            if q_name and 'ping' in q_name:
                arguments = {'x-message-ttl': 30 * 1000}

            queue = await channel.declare_queue(q_name, arguments=arguments, durable=True)

            await channel.default_exchange.publish(
                Message(
                    message.encode(),
                    content_type='application/json',
                    delivery_mode=2
                ),
                routing_key=queue.name,
            )

    async def start_queue_listener(self, queue_name, ):
        channel = await self.connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.consume(lambda msg: command_rmq_handler(queue_name, msg))


rabbit_mq = RabbitMQClient(
    f"amqp://{settings.RMQ_USER}:{settings.RMQ_PASSWORD}@{settings.RMQ_HOST}:{settings.RMQ_PORT}/")
