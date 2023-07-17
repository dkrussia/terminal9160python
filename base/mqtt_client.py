from datetime import datetime
from pprint import pprint
import threading
import paho.mqtt.client as mqtt
import json

import config
from config import MQTT_USER, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT
from base.log import logger
from services.devices import device_service
from base.rmq_client import rmq_publish_message


class ExceptionOnPublishMQTTMessage(Exception):
    pass


class ExceptionNoResponseMQTTReceived(Exception):
    pass


def get_mqtt_client():
    client = mqtt.Client("terminal_mqtt")
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    return client


class ResultEvent(object):
    def __init__(self):
        self.event = threading.Event()
        self.result = None


class MQTTClientWrapper:
    def __init__(self):
        self.client = get_mqtt_client()
        self.result_events = {}
        self.lock = threading.Lock()
        self.is_receiving = False

        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect
        self.client.user_data_set((self.result_events, self.lock))

    def _on_connect(self, client, userdata, flags, rc):
        print("Подключено: " + str(rc))
        client.subscribe("/_report/state")
        client.subscribe("/_report/received")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        payload_json = json.loads(payload)
        result_events, lock = userdata

        print('\n')
        print('***', datetime.now().strftime('%H:%M:%S'), '***')
        print(f'GOT MESSAGE ON {topic}')
        pprint(payload_json)
        print('*' * 16)

        if topic == "/_report/state":
            # Отправляем пинг устройства в очередь
            rmq_publish_message(
                queue=f'ping_{payload_json["sn"]}',
                exchange="",
                data={'sn': f'{payload_json["sn"]}'}
            )
            # Добавляем устройство
            device_service.add_device(payload_json["sn"])
            device_service.add_meta_on_state(payload=payload_json)
            return

        event_key = f'command_{payload_json["operations"]["id"]}_{payload_json["devSn"]}'
        with lock:
            result_event = result_events.get(event_key)
            if result_event:
                result_event.result = payload_json
                result_event.event.set()

    def publish_command(self, sn_device, payload: dict):
        print('***', datetime.now().strftime('%H:%M:%S'), '***')
        print("-----PUBLISH COMMAND TO MQTT------")
        print(f"---TO SN_DEVICE: {sn_device}--")
        print("-----       PAYLOAD      ------")
        pprint(payload)
        print("-----       PAYLOAD      ------")
        result, _ = self.client.publish(f"/_dispatch/command/{sn_device}", json.dumps(payload))
        print(result, _)
        if result != mqtt.MQTT_ERR_SUCCESS:
            print("--MQTT ERROR PUBLISH COMMAND--")
            logger.error(f'MQTT ERROR PUBLISH COMMAND, {payload}')
            raise ExceptionOnPublishMQTTMessage()
        print("--MQTT SUCCESS PUBLISH COMMAND--")

    def send_command_and_wait_result(self, command, timeout=config.TIMEOUT_MQTT_RESPONSE):
        result_event = ResultEvent()
        event_key = f'command_{command.id_command}_{command.sn_device}'

        with self.lock:
            self.result_events[event_key] = result_event

        self.publish_command(sn_device=command.sn_device, payload=command.payload)
        self.result_events[event_key].event.wait(timeout=timeout)
        result = result_event.result

        with self.lock:
            del self.result_events[event_key]

        if result is None:
            logger.error('MQTT NO RESPONSE BY TIMEOUT')
            raise ExceptionNoResponseMQTTReceived
        return result

    def start_receiving(self):
        if not self.is_receiving:
            self.is_receiving = True
            self.client.loop_start()

    def stop_receiving(self):
        if self.is_receiving:
            self.is_receiving = False
            self.client.loop_stop()

    def disconnect(self):
        self.stop_receiving()
        self.client.disconnect()


mqtt_client = MQTTClientWrapper()
