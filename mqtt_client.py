from pprint import pprint

import paho.mqtt.client as mqtt
import json

from main import MQTT_USER, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT


class ExceptionOnPublishMQTTMessage(Exception):
    pass


def get_mqtt_client():
    client = mqtt.Client("terminal_mqtt")
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    return client


mqtt_client = get_mqtt_client()


def mqtt_publish_command(sn_device, payload: dict):
    print("-----MQTT PUBLISH COMMAND------")
    print(f"---TO SN_DEVICE: {sn_device}--")
    print("-----       PAYLOAD      ------")
    pprint(payload)
    print("-----       PAYLOAD      ------")
    mqtt_client.loop_start()
    result, _ = mqtt_client.publish(f"/_dispatch/command/{sn_device}", json.dumps(payload))
    print(result, _)
    if result != mqtt.MQTT_ERR_SUCCESS:
        print("--MQTT ERROR PUBLISH COMMAND--")
        raise ExceptionOnPublishMQTTMessage()
    mqtt_client.loop_stop()
    print("--MQTT SUCCESS PUBLISH COMMAND--")


query_person_payload = {
    "type": 1000,
    "id": 1,
    "devSn": "YGKJ202107TR08EL0007",
    "feedbackUrl": "",
    "operations": {
        "emp_id": "",
        "keyword": "",
        "need_feature": False,
        "need_photo": False,
        "page_num": 1,
        "page_idx": 0
    }
}
