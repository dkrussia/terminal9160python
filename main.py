import asyncio
import os
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from config import s
from base.endpoints import device_router, person_router, device_push_router
from base.mqtt_client import mqtt_consumer
from base.rmq_client import rabbit_mq

from config import (
    BASE_DIR,
    PHOTO_DIR,
    PHOTO_PATH,
    FIRMWARE_PATH,
    FIRMWARE_DIR,
    CORS,
    s as settings
)
from services.mock import mock_run

if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(PHOTO_PATH, StaticFiles(directory=PHOTO_DIR), name="photo")
app.mount(FIRMWARE_PATH, StaticFiles(directory=FIRMWARE_DIR), name="firmware")

app.include_router(person_router, tags=['Управление персонами'])
app.include_router(device_router, tags=['M API for Device'])
app.include_router(device_push_router, tags=['Push API Device'])


def parse_pydantic_validation_error(errors):
    data = {}
    for filed in errors:
        if len(filed['loc']) > 1:
            field = filed['loc'][-1]
        else:
            field = filed['loc'][0]
        data[field] = filed['msg']
    return data


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    response = parse_pydantic_validation_error(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(response),
    )


app.mount(
    '/static',
    StaticFiles(directory=f'{BASE_DIR}/dashboard/dist/static', ),
    name='static',
)


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(BASE_DIR, 'dashboard', 'favicon.ico'))


# Маршрут для отображения SPA-приложения на префиксном пути
@app.get('/dashboard/{path:path}', response_class=HTMLResponse)
def dashboard_index(path: str):
    return FileResponse(f'{BASE_DIR}/dashboard/dist/index.html')


# Корневая страница
@app.get('/', response_class=HTMLResponse)
def index():
    return FileResponse(f'{BASE_DIR}/dashboard/index.html')


# Test
# При добавлении персон в терминал, надо дождаться результата выполнения
# и затем уже отправлять снова.
# Если надо загрузить много персон сразу, то делаем это пачками по 100 человек.
print("BASE DIR: ", BASE_DIR)
print("PHOTO URL: ", s.PHOTO_URL)
print("PHOTO DIR: ", PHOTO_DIR)
print("PHOTO_PATH: ", PHOTO_PATH)
print("MQTT_PORT_FOR_TERMINAL: ", s.MQTT_PORT_FOR_TERMINAL)
print("HOST_FOR_TERMINAL: ", s.HOST_FOR_TERMINAL)
print("PORT_FOR_TERMINAL: ", s.PORT_FOR_TERMINAL)


@app.on_event("startup")
async def startup_event():
    await rabbit_mq.start()

    if s.MOCK_DEVICE:
        asyncio.create_task(mock_run())
        return

    asyncio.create_task(mqtt_consumer())

if __name__ == '__main__':
    uvicorn.run(
        app=app,
        port=settings.SERVER_PORT,
        host=settings.SERVER_HOST,
    )
