from pprint import pprint

import uvicorn
from fastapi import FastAPI, Request

app = FastAPI()


# Test
# При добавлении персон в терминал, надо дождатся результата вполнения
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
    # 
    return {
        "code": 0,
        "data": {
            "mqttUserName": "admin",
            "mqttPassword": "admin123",
            "mqttUrl": "tcp://192.168.1.130:8086",
            "token": "token",
        },
        "desc": "123",
        "success": False
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
        port=8080,
        host='192.168.1.130',
    )
