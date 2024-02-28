import asyncio
from datetime import datetime
from pprint import pprint
from typing import Optional, Literal, List
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from starlette import status

from base.booking import add_booking, BookingAddException
from base.booking_viewer.viewer import add_booking_report
from base.mqtt_api import get_total_person_all_devices, get_total_person_device
from base.schema import PersonCreate, UpdateConfig, NtpTime, CheckPhoto
from config import BASE_DIR
from config import s as settings
from base import mqtt_api
from services.device_command import ControlAction
from services.devices_storage import device_service

# TODO: Разделить то что пушит девайс, и свои роуты
from services.person_photo import PersonPhoto

device_push_router = APIRouter(prefix='/api/devices')

device_router = APIRouter(prefix='/api/devices/my')
person_router = APIRouter(prefix='/api/devices/my/person')


# TODO: Добавить во все вызовы API серийный номер устройства

async def print_request(request: Request):
    h = request.headers.items()
    c = request.cookies.items()
    d = await request.json()

    pprint(c)
    pprint(h)
    pprint(d)


def checker(person_payload: str = Form(...)):
    print(1)
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
async def get_person(sn_device: str, id: Optional[int] = ""):
    if not id:
        r = await mqtt_api.update_config(sn_device, {})
        if r["answer"]:
            device_service.save_config(sn_device, r["answer"].get('operations'))

        resp = await mqtt_api.get_all_person(sn_device=sn_device)
        if resp.get('answer'):
            for person in resp["answer"]["operations"]["users"]:
                person.update({"faceUrl": PersonPhoto.get_photo_url(person["id"])})
                person.update(
                    {"_face_template": "OK" if PersonPhoto.get_face_template(
                        person["id"]) else "NOT FOUND"}
                )
        return resp
    return await mqtt_api.get_person(id_person=id, sn_device=sn_device)


@person_router.delete("/{id}", description="Удаление пользователя по ID")
@person_router.delete("", description="Удаление всех пользователей")
async def delete_person(sn_device: str, id: int = None):
    return await mqtt_api.delete_person(sn_device=sn_device, id=id)


@person_router.post("/self", description="Добавить себя")
async def add_self_person(
        sn_device: str,
):
    with open(f'{BASE_DIR}/tests/base64photo.txt', 'r') as f:
        p = f.read()
    return await mqtt_api.create_or_update(
        sn_device=sn_device,
        id_person=999,
        firstName="Сергей",
        lastName="Кузнецов",
        photo=p,
        cardNumber=None,
    )


@person_router.post("/{id}", description="Создание или обновление пользователя по ID")
@person_router.post("/create", description="Создание или обновление нового пользователя")
async def person_create_or_update(
        sn_device: str,
        id: int = 0,
        person_payload: PersonCreate = Depends(),
        photo: Optional[UploadFile] = File(None),
):
    """
    Endpoint создает или обновляет пользователя.
    Возвращает результат ответа Device через MQTT.
    Таймаут ожидания указан в конфиге {TIMEOUT_MQTT_RESPONSE}.
    Фотография не обязательна.
    """
    return await mqtt_api.create_or_update(
        sn_device=sn_device,
        id_person=id,
        firstName=person_payload.firstName,
        lastName=person_payload.lastName,
        photo=photo,
        cardNumber=person_payload.cardNumber
    )


@device_router.get('/all')
async def all_devices_registered():
    for sn_device in device_service.devices:
        if sn_device in device_service.devices_meta.keys() \
                and 'config' not in device_service.devices_meta[sn_device].keys():
            # Вызвать это для получения конфига с сервера с пустой нагрузкой
            r = await mqtt_api.update_config(sn_device, {}, )
            if r["answer"]:
                device_service.save_config(sn_device, r["answer"].get('operations'))
    return {
        'meta': device_service.devices_meta,
        'observed': device_service.devices_observed,
        'function_arrive': device_service.devices_function_arrive
    }


@device_router.get('/total_persons')
async def get_total_devices():
    sn_list = device_service.all_sn_list
    all_sn_devices = [sn_device for sn_device in sn_list]
    result = await get_total_person_all_devices(all_sn_devices)
    return result


@device_router.get('/total_persons/{sn_device}')
async def get_total_persons_on_device(sn_device: Optional[str]):
    sn_list = device_service.all_sn_list

    if sn_device not in sn_list:
        raise HTTPException(status_code=404, detail="Device not found")
    total = await get_total_person_device(sn_device, timeout=5)
    return {"total": total}


@device_push_router.post("/login")
async def device_login(request: Request):
    """
    TERMINAL отдает данные сюда в формате:
    Example request payload:
    {
        "base_routerVersionCode": 10415,
        "base_routerVersionName": "1.4.15C_DBG",
        "devLanguage": "english",
        "devName": "YGKJ202107TR08EL0007",
        "devSn": "YGKJ202107TR08EL0007",
        "loginName": "admin",
        "model": "9160-K5",
        "networkIp": "192.168.1.100",
        "networkType": 1,
        "onlineStatus": 0,
        "romVersion": ""
    }
    """
    await print_request(request)

    payload = await request.json()
    sn_device = payload["devSn"]
    device_service.add_ip_address(sn_device, payload["networkIp"])

    r = {
        "code": 0,
        "data": {
            "mqttUserName": settings.MQTT_USER,
            "mqttPassword": settings.MQTT_PASSWORD,
            "mqttUrl": f"tcp://{settings.HOST_FOR_TERMINAL}:{settings.MQTT_PORT_FOR_TERMINAL}",
            "token": "token",
        },
        "desc": "123",
        "success": True
    }
    print(r)
    return r


@device_push_router.post("/updateConfig")
async def dconfig(request: Request):
    """
    Устройство отдает данные конфигурации сюда
    """
    await print_request(request)
    d = await request.json()

    sn_device = d["devSn"]
    # device_service.add_ip_address(sn_device, request.client.host)
    device_service.save_config(sn_device, d)
    return {}


@device_push_router.post("/passRecord/addRecord")
async def pass_face(request: Request):
    """
    TERMINAL отдает данные сюда в формате:
    Example request payload:
    atType:
        IN: 2
        OUT: 3
        TRIP: 4 + REMARK
    {
        "atType": 2,
        "devName": "YGKJ202107TR08EL0007",
        "devSn": "YGKJ202107TR08EL0007",
        "devUserDeptId": 0,
        "devUserId": 20964,
        "facemask": 0,
        "firstName": "",
        "id": 66,
        "lastName": "",
        "passStatus": 0,
        "passType": 0,
        "passageTime": "2023-05-25 18:31:22",
        "remark": "",
        "temperature": 0,
        "userName": ""
    }
    """
    payload = await request.json()
    try:
        await add_booking(payload)
        # return {
        #     "code": 0,
        #     "desc": "成功",
        #     "success": True,
        #     "data": {
        #         "params": {},
        #         "id": payload['id']
        #     }
        # }
    except BookingAddException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    finally:
        asyncio.create_task(add_booking_report(payload))


@device_router.post("/control/set_ntp_time", )
async def set_ntp_time(sn_device: str, payload: NtpTime):
    """
    timeServer: 1.ntp.org \n
    timeZone: timeZone \n
    ntp: bool \n
    time: 2021-01-31 12:00:00 \n
    """
    return await mqtt_api.control_action_set_ntp(sn_device=sn_device, payload=payload.model_dump())


@device_router.post("/control/set_ntp_time/selected", )
async def update_config(ntp_time: NtpTime, sn_devices: List[str], ):
    # check
    r = await mqtt_api.control_action_set_ntp_multi(ntp_time.dict(exclude_none=True),
                                                    sn_devices=sn_devices)
    return {sn_device: bool(r[sn_device]) for sn_device in sn_devices}


@device_router.post("/control/{action}", )
async def send_control_action(
        action: ControlAction,
        sn_device: str,
):
    """
    Отправить действие на терминал: \n
    RESTART_SYSTEM = 2 \n
    RESTART_SOFTWARE = 3 \n
    DOOR_OPEN = 4 \n
    UPDATE_SOFTWARE = 5 \n
    """
    return await mqtt_api.control_action(action, sn_device=sn_device)


@device_router.post("/config", )
async def update_config(device_config: UpdateConfig, sn_device: str, ):
    """
    Обновить настройки конфигурации на терминале
    adminPassword	String	Device login password\n
    brightness	Int	Screen backlight brightness [1,100]\n
    deviceVolume	Int	Device volume [0,100]\n
    featureThreshold	Int	Face recognition threshold\n
    living	Int	Living body detection switch (0=Off,1=On)\n
    recogizeInterval	Int	Repeat the recognition interval. After recognition is successful,
    you need to wait for the recogizeInterval before recognition is successful again
    minSize	Int	Minimum face size for recognition（pixel）\n
    temperature	Int	Temperature detection switch (0=Off,1=On)\n
    playVoice	Bool	Voice broadcast prompt switch\n
    lowPower	Bool	When the low-power enable switch is turned on, when the proximity sensor does
    not detect an object for a continuous idletime, the device turns off the fill light, infrared
    light and NFC module, and stops the face detection function to reduce power consumption.
    idleTime	Int	Idle time before entering low power consumption\n
    passMethod	Int	Access mode: 0: face / card / QR code, 1: face + card\n
    openDuration	Int	Relay opening time\n
    alarmEnabled	Bool	Alarm function when the door is not closed after opening (it needs the support\n
    of access control hardware to enable the equipment to sense the opening / closing state of the door)\n
    alarmDuration	Int	Alarm duration\n
    cardNumDecimal	Bool	Decimal card number\n
    cardNumReverse	Bool	Reverse sequence card number\n
    """
    r = await mqtt_api.update_config(sn_device, device_config.dict(exclude_none=True), )
    if r.get("answer"):
        device_service.save_config(sn_device, r["answer"].get('operations'))
    return r


@device_router.post("/config/selected", )
async def update_config(device_config: UpdateConfig, sn_devices: List[str], ):
    # check
    r = await mqtt_api.update_config_multi(device_config.dict(exclude_none=True),
                                           sn_devices=sn_devices)
    device_service.save_config_multi(r)
    return {sn_device: bool(r[sn_device]) for sn_device in sn_devices}


@device_router.post("/to_observed", )
async def add_to_observed(sn_device: str, ):
    return device_service.add_device_to_observed(sn_device)


@device_router.post("/unobserved", )
async def unobserved(sn_device: str, ):
    return device_service.remove_device_from_observed(sn_device)


@device_router.post("/access_control", )
async def access_mode_set_function(sn_device: str, function: Literal["arrive", "depart"]):
    return device_service.set_function(sn_device, function)


@device_router.post("/face_already_existing", )
async def check_face_already_existing(sn_device: str, payload: CheckPhoto):
    return await mqtt_api.check_face(payload.photo_base64, sn_device)


@device_router.get("/access_log", )
async def access_log(
        sn_device: str,
        date_start: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        date_end: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), keyword: str = ""
):
    return await mqtt_api.access_log(sn_device,
                                     startStamp=int(date_start.timestamp()),
                                     endStamp=int(date_end.timestamp()),
                                     keyword=keyword)
