# MOCK обработчик commands_test_* для устройств-заглушек
# MOCK обработчик ping_test_* для  устройств-заглушек
import asyncio
import json
import random
import time
from datetime import datetime

from aio_pika import IncomingMessage

from base.rmq_client import rabbit_mq
from config import s


async def mock_commands_handler(queue_name, message: IncomingMessage):
    t1 = datetime.now()
    async with message.process():
        type_command = message.headers.get("command_type")
        reply_to = message.reply_to
        random_number = random.randint(0, 99)

        if random_number < s.MOCK_DEVICE_SUCCESS_CHANCE:
            await asyncio.sleep(random.choice(s.MOCK_DEVICE_SUCCESS_TIMEOUT))
            await rabbit_mq.publish_message(
                reply_to=reply_to,
                data=json.dumps({"result": 'Successful', 'Return': "0"})
            )

        else:
            await asyncio.sleep(random.choice(s.MOCK_DEVICE_ERROR_TIMEOUT))
            await rabbit_mq.publish_message(
                reply_to=reply_to,
                data=json.dumps({"result": 'Error', 'Return': "1"})
            )

    t2 = datetime.now()
    print(f'MOCK Total Device ${queue_name}: {type_command}-{(t2 - t1).total_seconds()}')


async def mock_ping_to_mock_devices():
    while True:
        for p_mock_sn in range(1, s.MOCK_DEVICE_AMOUNT):
            p_q_name = f'ping_MCI_Test_{p_mock_sn}'
            await rabbit_mq.publish_message(q_name=p_q_name,
                                            message=json.dumps({'sn': f'MCI_Test_{p_mock_sn}'}))
            print(f"[*] Ping run p_q_name {p_mock_sn}")
        await asyncio.sleep(20)


async def handle_commands_from_mock_devices():
    for mock_sn in range(1, s.MOCK_DEVICE_AMOUNT):
        channel = await rabbit_mq.connection.channel()
        queue_name = f'commands_MCI_Test_{mock_sn}'
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(queue_name)
        await queue.consume(lambda msg: mock_commands_handler(queue_name, msg))
