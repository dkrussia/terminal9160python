import ast
from datetime import datetime
from pprint import pprint

import aiomqtt as aiomqtt
import json

from base.mqtt_api import futures
from config import s as settings
from services.devices import device_service
from base.rmq_client import rabbit_mq


class ExceptionOnPublishMQTTMessage(Exception):
    pass


class ExceptionNoResponseMQTTReceived(Exception):
    pass


async def mqtt_consumer():
    async with aiomqtt.Client(hostname=settings.MQTT_HOST,
                              port=settings.MQTT_PORT,
                              username=settings.MQTT_USER,
                              password=settings.MQTT_PASSWORD) as client:
        async with client.messages() as messages:
            await client.subscribe("/_report/state")
            await client.subscribe("/_report/received")
            async for message in messages:
                payload_json = json.loads(message.payload.decode('utf-8'))

                if message.topic.matches("/_report/state"):
                    print(f"[/_report/state] {message.payload}")
                    await rabbit_mq.publish_message(f'ping_{payload_json["sn"]}',
                                                    json.dumps({'sn': payload_json["sn"]}))
                    await device_service.add_device(payload_json)

                if message.topic.matches("/_report/received"):
                    print(f"[/_report/received] {message.payload}")
                    print('\n')
                    print('***', datetime.now().strftime('%H:%M:%S'), '***')
                    pprint(payload_json)
                    print('*' * 16)

                    feature_key = f'command_{payload_json["operations"]["id"]}_{payload_json["devSn"]}'
                    result_future = futures.pop(feature_key, None)
                    if result_future:
                        result_future.set_result(payload_json)