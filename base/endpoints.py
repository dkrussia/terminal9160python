from pprint import pprint
from typing import Optional

from fastapi import APIRouter, Request, UploadFile, File, Form, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from starlette import status

from base.mqtt_client import mqtt_client, ExceptionOnPublishMQTTMessage
from base.schema import PersonCreate
from config import MQTT_USER, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT, TEST_SN_DEVICE, \
    TIMEOUT_WAIT_MQTT_ANSWER
from services import person as person_service

base_router = APIRouter()


def get_all_user(sn_device=TEST_SN_DEVICE):
    command = person_service.CommandGetPerson(sn_device=sn_device)
    command.search_person("")
    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
        "command": command.result_json(),
        "answer": answer,
    }


def get_person(id_person, sn_device=TEST_SN_DEVICE):
    command = person_service.CommandGetPerson(sn_device=TEST_SN_DEVICE)
    command.search_person(id_person)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
        "command": command.result_json(),
        "answer": answer,
    }


async def print_request(request: Request):
    h = request.headers.items()
    c = request.cookies.items()
    d = await request.json()

    pprint(c)
    pprint(h)
    pprint(d)


@base_router.get("/person/{id}")
@base_router.get("/person")
def _get_person(id: Optional[int] = ""):
    if not id:
        return get_all_user()
    return get_person(id_person=id)


@base_router.delete("/person")
@base_router.delete("/person/{id}")
def delete_person(id: int = None):
    command = person_service.CommandDeletePerson(sn_device=TEST_SN_DEVICE)

    if not id:
        all_users_response = get_all_user()
        if all_users_response['answer']:
            # Надо ли обрабатывать этот случай?
            for user in all_users_response['answer']['operations']['users']:
                command.delete_person(user['id'])
    else:
        command.delete_person(id)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
        "answer": answer,
        "command": command.result_json()
    }


def checker(person_payload: str = Form(...)):
    try:
        model = PersonCreate.parse_raw(person_payload)
    except ValidationError as e:
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return model


@base_router.post("/person/{id}")
@base_router.post("/person/create")
async def person_create_or_update(
        id: int = 0,
        person_payload: PersonCreate = Depends(),
        file: Optional[UploadFile] = File(None),
):
    import base64

    """
    Endpoint создает или обновляет пользователя.
    Возвращает результат ответа Device через MQTT.
    Таймаут ожидания 5 секунд.
    Фотография не обязательна.
    """
    person_json = person_service.create_person_json(
        person_payload.id,
        firstName=person_payload.firstName,
        lastName=person_payload.lastName,
        face_str=base64.b64encode(file.file.read()).decode("utf-8") if file else ""

    )

    person_response = get_person(id_person=id)
    if person_response["answer"]["operations"]["executeStatus"] == 2:
        command = person_service.CommandCreatePerson(sn_device=TEST_SN_DEVICE)
        command.add_person(person_json)
    else:
        command = person_service.CommandUpdatePerson(sn_device=TEST_SN_DEVICE)
        command.update_person(person_response)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
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
