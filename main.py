from pprint import pprint
import uvicorn
from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles

from config import BASE_URL, BASE_DIR, PHOTO_URL, PHOTO_DIR, PHOTO_PATH, TEST_SN_DEVICE, \
    SERVER_PORT, SERVER_HOST, MQTT_USER, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT
from services import person as person_service

from mqtt_client import MQTTClientWrapper, ExceptionOnPublishMQTTMessage
from services.devices import Devices

print("BASE URL: ", BASE_URL)
print("BASE DIR: ", BASE_DIR)
print("PHOTO URL: ", PHOTO_URL)
print("PHOTO DIR: ", PHOTO_DIR)

app = FastAPI()
app.mount(PHOTO_PATH, StaticFiles(directory=PHOTO_DIR), name="photo")

mqtt_client = MQTTClientWrapper()
mqtt_client.start_receiving()


# Test
# При добавлении персон в терминал, надо дождаться результата выполнения
# и затем уже отправлять снова.
# Если надо загрузить много персон сразу, то делаем это пачками по 100 человек.


async def print_request(request: Request):
    h = request.headers.items()
    c = request.cookies.items()
    d = await request.json()

    pprint(c)
    pprint(h)
    pprint(d)


@app.get("/")
def index():
    command = person_service.CommandCreatePerson(sn_device=TEST_SN_DEVICE)
    person_json = person_service.create_person_json(
        1000,
        firstName="Sergey",
        lastName="Kuznetsov",
    )
    command.add_person(person_json)
    try:
        r = mqtt_client.send_command_and_wait_result(command, timeout=5)
    except ExceptionOnPublishMQTTMessage:
        return {"result": False}
    return {"result": True, "payload": r}


@app.post("/api/devices/login")
async def device_login(request: Request):
    await print_request(request)
    d = await request.json()
    # {
    # 'appVersionCode': 10415,
    #  'appVersionName': '1.4.15C_DBG',
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


@app.post("/api/devices/updateConfig")
async def dconfig(request: Request):
    await print_request(request)
    return {}


@app.post("/api/devices/passRecord/addRecord")
async def dconfig(request: Request):
    await print_request(request)
    return {}

if __name__ == '__main__':
    uvicorn.run(
        app=app,
        port=SERVER_PORT,
        host=SERVER_HOST,
    )
