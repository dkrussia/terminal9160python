import json
import logging
from datetime import datetime

from aio_pika import connect_robust, IncomingMessage, Message

from base import mqtt_api
from config import s as settings

logger = logging.getLogger('rmq_log')
logger.setLevel(logging.INFO)


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
    async with message.process():
        type_command = message.headers.get("command_type")
        reply_to = message.reply_to
        payload = json.loads(message.body.decode('utf-8'))
        print(payload, type_command)

        sn_device = queue_name.split("_")[-1]

        t1 = datetime.now()
        result = None

        if type_command == 'user_update_biophoto':
            photo = payload.get('picture', "")
            if photo:
                result = await mqtt_api.create_or_update(
                    sn_device=sn_device,
                    id_person=int(payload["id"]),
                    firstName=payload["firstName"],
                    lastName=payload["lastName"],
                    photo=photo,
                )

        if type_command == 'multiuser_update_biophoto':
            for user in payload:
                photo = user.get('picture', "")
                if photo:
                    # TODO: Сделать Сумму результатов + ID персон которые с ошибкой.
                    #  commands = [create_command, *update_commands]

                    result = await mqtt_api.create_or_update(
                        sn_device=sn_device,
                        id_person=int(user["id"]),
                        firstName=user["firstName"],
                        lastName=user["lastName"],
                        photo=photo,
                    )

        if type_command == 'user_delete':
            result = await mqtt_api.delete_person(sn_device=sn_device, id=int(payload["id"]))

        error_result = {"result": 'Error', 'Return': "-1"}
        success_result = {"result": 'Successful', 'Return': "0"}

        if not result or result["has_error"]:
            await rabbit_mq.publish_message(
                q_name=None,
                reply_to=reply_to,
                message=json.dumps(error_result)
            )
        else:
            await rabbit_mq.publish_message(
                q_name=queue_name,
                reply_to=reply_to,
                message=json.dumps(success_result)
            )
        t2 = datetime.now()
        print(f'Total: {type_command}-{(t2 - t1).total_seconds()}')
    # type_command == 'user_update' or
    # type_command == 'multiuser_update' or
    # if type_command == 'user_update_biophoto':
    # if type_command == 'multiuser_update_biophoto':


class RabbitMQClient:
    def __init__(self, amqp_url):
        self.amqp_url = amqp_url
        self.connection = None

    async def start(self):
        self.connection = await connect_robust(self.amqp_url)

    async def stop(self):
        if self.connection:
            await self.connection.close()

    async def publish_message(self, q_name, message, reply_to=None, ):
        # add timeout expired for ping queue
        channel = await self.connection.channel()
        if reply_to:
            # TODO: need test
            await channel.publish(
                Message(message.encode(), reply_to=reply_to, content_type='application/json'),
                routing_key=reply_to
            )
            return
        queue = await channel.declare_queue(q_name, auto_delete=True)
        await channel.default_exchange.publish(
            Message(message.encode(), content_type='application/json'),
            routing_key=queue.name,
        )

    async def start_queue_listener(self, queue_name, ):
        channel = await self.connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(queue_name)
        await queue.consume(lambda msg: command_rmq_handler(queue_name, msg))


rabbit_mq = RabbitMQClient(
    f"amqp://{settings.RMQ_USER}:{settings.RMQ_PASSWORD}@{settings.RMQ_HOST}:{settings.RMQ_PORT}/")
