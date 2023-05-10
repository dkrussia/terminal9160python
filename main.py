import os
from pprint import pprint

import uvicorn
from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles

from services.devices import Devices

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PHOTO_DIR = f"{BASE_DIR}/photo"
SERVER_HOST = "192.168.1.130"
SERVER_PORT = 8080

app = FastAPI()
app.mount("/photo", StaticFiles(directory=PHOTO_DIR), name="photo")

print("BASE DIR: ", BASE_DIR)
print("PHOTO DIR: ", PHOTO_DIR)


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


@app.post("/")
async def index(request: Request):
    await print_request(request)
    return {}


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
    Devices.add_device(d["devSn"])
    return {
        "code": 0,
        "data": {
            "mqttUserName": "admin",
            "mqttPassword": "admin123",
            "mqttUrl": "tcp://192.168.1.130:8086",
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
