import paho.mqtt.client as mqtt
import json


class ExceptionOnPublishMQTTMessage(Exception):
    pass


def get_mqtt_client():
    client = mqtt.Client("terminal_mqtt")
    client.username_pw_set('admin', 'admin123')
    return client


mqtt_client = get_mqtt_client()


def mqtt_publish_command(sn_device, payload: dict):
    mqtt_client.loop_start()
    result = mqtt_client.publish(f"/_dispatch/command/{sn_device}", json.dumps(payload))
    if result != mqtt.MQTT_ERR_SUCCESS:
        raise ExceptionOnPublishMQTTMessage()
    mqtt_client.loop_stop()


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
