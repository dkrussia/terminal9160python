from datetime import datetime
from pprint import pprint
from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from starlette import status
from base.schema import PersonCreate
from config import MQTT_USER, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT, TEST_SN_DEVICE
from base import mqtt_api
from services.rmq import rmq_publish_message

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
    if not id:
        return mqtt_api.get_all_user()
    return mqtt_api.get_person(id_person=id)


@base_router.delete("/person")
@base_router.delete("/person/{id}")
def delete_person(id: int = None):
    return mqtt_api.delete_person(id)


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
        photo: Optional[UploadFile] = File(None),
):
    """
    Endpoint создает или обновляет пользователя.
    Возвращает результат ответа Device через MQTT.
    Таймаут ожидания 5 секунд.
    Фотография не обязательна.
    """
    return mqtt_api.create_or_update(
        sn_device=TEST_SN_DEVICE,
        id_person=id,
        firstName=person_payload.firstName,
        lastName=person_payload.lastName,
        photo=photo
    )


@base_router.get('/registered_devices')
def all_devices_has_registered():
    pass


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
    # device_service.add_device(d["devSn"])
    return {
        "code": 0,
        "data": {
            "mqttUserName": MQTT_USER,
            "mqttPassword": MQTT_PASSWORD,
            "mqttUrl": f"tcp://{MQTT_HOST}:{MQTT_PORT}",
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
    payload = await request.json()
    sn_device = payload["devSn"]
    rmq_publish_message(
        data={
            'sn': f'events_{sn_device}',
            'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'status': '1',
            "pin": payload["id"],
        },
        queue=f'events_{sn_device}',
        exchange=""
    )
    return {}
