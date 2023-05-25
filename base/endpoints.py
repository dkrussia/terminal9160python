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
from base.rmq_client import rmq_publish_message

device_router = APIRouter(prefix='/api/devices')
person_router = APIRouter(prefix='/person')


async def print_request(request: Request):
    h = request.headers.items()
    c = request.cookies.items()
    d = await request.json()

    pprint(c)
    pprint(h)
    pprint(d)


def checker(person_payload: str = Form(...)):
    try:
        model = PersonCreate.parse_raw(person_payload)
    except ValidationError as e:
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return model


@person_router.get("/{id}", description="Получение пользователя по ID")
@person_router.get("", description="Получение всех пользователей")
def get_person(id: Optional[int] = ""):
    if not id:
        return mqtt_api.get_all_user()
    return mqtt_api.get_person(id_person=id)


@person_router.delete("/{id}", description="Удаление пользователя по ID")
@person_router.delete("", description="Удаление всех пользователей")
def delete_person(id: int = None):
    return mqtt_api.delete_person(id)


@person_router.post("/{id}", description="Создание или обновление пользователя по ID")
@person_router.post("/create", description="Создание или обновление нового пользователя")
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


@device_router.get('/all')
def all_devices_has_registered():
    pass


@device_router.post("/login")
async def device_login(request: Request):
    """
        Example request payload:
        {
            'base_routerVersionCode': 10415,
             'base_routerVersionName': '1.4.15C_DBG',
             'devLanguage': 'english',
             'devName': 'YGKJ202107TR08EL0007',
             'devSn': 'YGKJ202107TR08EL0007',
             'loginName': 'admin',
             'model': '9160-K5',
             'networkIp': '192.168.1.100',
             'networkType': 1,
             'onlineStatus': 0,
             'romVersion': ''
        }
    """
    await print_request(request)
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


@device_router.post("/updateConfig")
async def dconfig(request: Request):
    await print_request(request)
    return {}


@device_router.post("/passRecord/addRecord")
async def pass_face(request: Request):
    """
        Example request payload:
        {
            'atType': 2,
            'devName': 'YGKJ202107TR08EL0007',
            'devSn': 'YGKJ202107TR08EL0007',
            'devUserDeptId': 0,
            'devUserId': 20964,
            'facemask': 0,
            'firstName': '',
            'id': 66,
            'lastName': '',
            'passStatus': 0,
            'passType': 0,
            'passageTime': '2023-05-25 18:31:22',
            'remark': '',
            'temperature': 0,
            'userName': ''
        }
    """
    await print_request(request)
    payload = await request.json()
    sn_device = payload["devSn"]
    id_user = payload["devUserId"]
    passageTime = payload["passageTime"].replace(" ", "T")
    if id_user > 0:
        # datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        rmq_publish_message(
            data={
                'sn': f'events_{sn_device}',
                'time': passageTime,
                'status': '1',
                "pin": id_user,
            },
            queue=f'events_{sn_device}',
            exchange=""
        )
    return {}
