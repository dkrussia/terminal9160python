# MOCK обработчик commands_test_* для устройств-заглушек
# MOCK обработчик ping_test_* для  устройств-заглушек

import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import config
from base.rmq_client import rmq_global_chanel, rmq_send_reply_to


executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS_MCI_COMMAND)


def mock_command_thread_handler(type_command, sn_device, payload, reply_to):
    t1 = datetime.now()
    random_number = random.randint(0, 99)

    if random_number < config.MOCK_DEVICE_SUCCESS_CHANCE:
        time.sleep(random.choice(config.MOCK_DEVICE_SUCCESS_TIMEOUT))
        rmq_send_reply_to(
            reply_to=reply_to,
            data={"result": 'Successful', 'Return': "0"}
        )

    else:
        time.sleep(random.choice(config.MOCK_DEVICE_ERROR_TIMEOUT))
        rmq_send_reply_to(
            reply_to=reply_to,
            data={"result": 'Error', 'Return': "1"}
        )

    t2 = datetime.now()
    print(f'MOCK Total Device ${sn_device}: {type_command}-{(t2 - t1).total_seconds()}')


def mock_callback_on_get_mci_command(message):
    type_command = message.properties['headers'].get('command_type')
    reply_to = message.properties.get('reply_to')
    payload = None
    sn_device = message.method["routing_key"].split("_")[-1]

    executor.submit(mock_command_thread_handler,
                    type_command=type_command,
                    sn_device=sn_device,
                    payload=payload,
                    reply_to=reply_to)


def mock_ping_to_mock_devices():
    while True:
        for p_mock_sn in range(1, config.MOCK_DEVICE_AMOUNT):
            p_q_name = f'ping_MCI_Test_{p_mock_sn}'
            rmq_global_chanel.queue.declare(
                p_q_name,
                arguments={'x-message-ttl': 30 * 1000}
            )
            prop = {
                'delivery_mode': 2,
                'headers': None,
                'content_type': 'application/json'
            }
            rmq_global_chanel.basic.publish(
                routing_key=p_q_name,
                exchange="",
                properties=prop,
                body=json.dumps({'sn': f'MCI_Test_{p_mock_sn}'}),
            )
            print(f"[*] Ping run p_q_name {p_mock_sn}")
        time.sleep(20)


def handle_commands_from_mock_devices():
    for mock_sn in range(1, config.MOCK_DEVICE_AMOUNT):
        q_name = f'commands_MCI_Test_{mock_sn}'
        rmq_global_chanel.queue.declare(q_name)
        rmq_global_chanel.basic.consume(mock_callback_on_get_mci_command, q_name)
