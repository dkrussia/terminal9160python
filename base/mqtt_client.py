import ast
from datetime import datetime
from pprint import pprint
import threading

import aiomqtt as aiomqtt
import paho.mqtt.client as mqtt
import json

from config import s as settings
from base.log import logger
from services.devices import device_service
from base.rmq_client import rabbit_mq


class ExceptionOnPublishMQTTMessage(Exception):
    pass


class ExceptionNoResponseMQTTReceived(Exception):
    pass


class ResultEvent(object):
    def __init__(self):
        self.event = threading.Event()
        self.result = None


async def mqtt_consumer():
    async with aiomqtt.Client("localhost",
                              port=settings.MQTT_PORT,
                              username=settings.MQTT_USER,
                              password=settings.MQTT_PASSWORD) as client:
        async with client.messages() as messages:
            await client.subscribe("/_report/state")
            await client.subscribe("/_report/received")
            async for message in messages:
                if message.topic.matches("/_report/state"):
                    payload_json = ast.literal_eval(message.payload.decode('utf-8'))
                    await rabbit_mq.publish_message(f'ping_{payload_json["sn"]}',
                                                    json.dumps({'sn': payload_json["sn"]}))
                    await device_service.add_device(payload_json["sn"])

                if message.topic.matches("/_report/received"):
                    print(f"[/_report/received] {message.payload}")

#
# class MQTTClientWrapper:
#     def _on_message(self, client, userdata, msg):
#         topic = msg.topic
#         payload = msg.payload.decode("utf-8")
#         payload_json = json.loads(payload)
#         result_events, lock = userdata
#
#         print('\n')
#         print('***', datetime.now().strftime('%H:%M:%S'), '***')
#         print(f'GOT MESSAGE ON {topic}')
#         pprint(payload_json)
#         print('*' * 16)
#
#         event_key = f'command_{payload_json["operations"]["id"]}_{payload_json["devSn"]}'
#         with lock:
#             result_event = result_events.get(event_key)
#             if result_event:
#                 result_event.result = payload_json
#                 result_event.event.set()
#
#     def publish_command(self, sn_device, payload: dict):
#         print('***', datetime.now().strftime('%H:%M:%S'), '***')
#         print("-----PUBLISH COMMAND TO MQTT------")
#         print(f"---TO SN_DEVICE: {sn_device}--")
#         print("-----       PAYLOAD      ------")
#         pprint(payload)
#         print("-----       PAYLOAD      ------")
#         result, _ = self.client.publish(f"/_dispatch/command/{sn_device}", json.dumps(payload))
#         print(result, _)
#         if result != mqtt.MQTT_ERR_SUCCESS:
#             print("--MQTT ERROR PUBLISH COMMAND--")
#             logger.error(f'MQTT ERROR PUBLISH COMMAND, {payload}')
#             raise ExceptionOnPublishMQTTMessage()
#         print("--MQTT SUCCESS PUBLISH COMMAND--")
#
#     def send_command_and_wait_result(self, command, timeout=settings.TIMEOUT_MQTT_RESPONSE):
#         result_event = ResultEvent()
#         event_key = f'command_{command.id_command}_{command.sn_device}'
#
#         with self.lock:
#             self.result_events[event_key] = result_event
#
#         self.publish_command(sn_device=command.sn_device, payload=command.payload)
#         self.result_events[event_key].event.wait(timeout=timeout)
#         result = result_event.result
#
#         with self.lock:
#             del self.result_events[event_key]
#
#         if result is None:
#             logger.error('MQTT NO RESPONSE BY TIMEOUT')
#             raise ExceptionNoResponseMQTTReceived
#         return result
#
#
# mqtt_client = MQTTClientWrapper()
