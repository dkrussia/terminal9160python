from pprint import pprint
from typing import Optional

from fastapi import APIRouter, Request
from base.mqtt_client import mqtt_client, ExceptionOnPublishMQTTMessage
from base.schema import PersonCreate
from config import MQTT_USER, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT, TEST_SN_DEVICE, \
    TIMEOUT_WAIT_MQTT_ANSWER
from services import person as person_service

base_router = APIRouter()


async def print_request(request: Request):
    h = request.headers.items()
    c = request.cookies.items()
    d = await request.json()

    pprint(c)
    pprint(h)
    pprint(d)


@base_router.get("/person/{id}")
@base_router.get("/person")
def get_person(id: Optional[int] = ""):
    command = person_service.CommandGetPerson(sn_device=TEST_SN_DEVICE)
    command.search_person(id)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
        result = True
    except ExceptionOnPublishMQTTMessage:
        answer = None
        result = False

    return {
        "result": result,
        "answer": answer,
        "command": command.result_json()
    }


@base_router.delete("/person")
@base_router.delete("/person/{id}")
def delete_person(id: int = None):
    command = person_service.CommandDeletePerson(sn_device=TEST_SN_DEVICE)
    command.delete_person(id)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
        result = True
    except ExceptionOnPublishMQTTMessage:
        answer = None
        result = False

    return {
        "result": result,
        "answer": answer,
        "command": command.result_json()
    }


@base_router.post("/person/create")
def person_create_or_update(
        person_payload: PersonCreate,
        # file: Optional[UploadFile] = File(...),
):
    """
    Endpoint создает или обновляет пользователя.
    Возвращает результат ответа Device через MQTT.
    Таймаут ожидания 5 секунд.
    Фотография не обязательна.
    """
    # TODO: check if created yet
    person_json = person_service.create_person_json(
        person_payload.id,
        firstName=person_payload.firstName,
        lastName=person_payload.lastName,
    )
    command = person_service.CommandCreatePerson(sn_device=TEST_SN_DEVICE)
    command.add_person(person_json)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
        result = True
    except ExceptionOnPublishMQTTMessage:
        answer = None
        result = False

    return {
        "result": result,
        "answer": answer,
        "command": command.result_json()
    }


@base_router.post("/api/devices/login")
async def device_login(request: Request):
    await print_request(request)
    d = await request.json()
    # {
    # 'base_routerVersionCode': 10415,
    #  'base_routerVersionName': '1.4.15C_DBG',
    #  'devLanguage': 'english',
    #  'devName': 'YGKJ202107TR08EL0007',
    #  'devSn': 'YGKJ202107TR08EL0007',
    #  'loginName': 'admin',
    #  'model': '9160-K5',
    #  'networkIp': '192.168.1.100',
    #  'networkType': 1,
    #  'onlineStatus': 0,
    #  'romVersion': ''
    #  }
    #
    # Devices.add_device(d["devSn"])
    return {
        "code": 0,
        "data": {
            "mqttUserName": MQTT_USER,
            "mqttPassword": MQTT_PASSWORD,
            "mqttUrl": F"tcp://{MQTT_HOST}:{MQTT_PORT}",
            "token": "token",
        },
        "desc": "123",
        "success": True
    }


@base_router.post("/api/devices/updateConfig")
async def dconfig(request: Request):
    await print_request(request)
    return {}


@base_router.post("/api/devices/passRecord/addRecord")
async def pass_face(request: Request):
    await print_request(request)
    return {}
