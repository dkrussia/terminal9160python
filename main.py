import asyncio
import os
import pathlib
import sys
from datetime import datetime
from typing import List

from fastapi import FastAPI, Request, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html

from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from base.bookings.sync import sync_booking_all_devices
from base.bookings.viewer import device_booking_viewer
from config import s

from base.endpoints import device_router, person_router, device_push_router, sync_router
from base.mqtt_client import mqtt_consumer
from base.rmq_client import rabbit_mq

from config import (
    BASE_DIR,
    PHOTO_PATH,
    FIRMWARE_PATH,
    FIRMWARE_DIR,
    CORS,
    s as settings
)
from reports import make_report
from services.devices_storage import device_service
from services.mock import mock_run
from services.person_photo import PersonPhoto

loop = asyncio.new_event_loop()

if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()

pathlib.Path(settings.PHOTO_DIR).mkdir(parents=True, exist_ok=True)
pathlib.Path(FIRMWARE_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(docs_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(PHOTO_PATH, StaticFiles(directory=settings.PHOTO_DIR), name="photo")
app.mount(FIRMWARE_PATH, StaticFiles(directory=FIRMWARE_DIR), name="firmware")

app.include_router(person_router, tags=['Persons'])
app.include_router(device_router, tags=['API Device'])
app.include_router(device_push_router, tags=['Push From Device'])
app.include_router(device_booking_viewer, tags=['Booking History'])
app.include_router(sync_router, tags=['Booking Sync'])


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

app.mount(
    '/swagger',
    StaticFiles(directory=f'{BASE_DIR}/dashboard/swagger', ),
    name='swagger',
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="9160Terminal API",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/swagger/5.4.2_swagger-ui-bundle.js",
        swagger_css_url="/swagger/5.4.2_swagger-ui.css",
        swagger_favicon_url="/favicon.ico"
    )


@app.get('/pass_photo/{path:path}', )
async def pass_photo(path: str):
    full_path = os.path.abspath(os.path.join(BASE_DIR, "assets/pass_photo", path))
    if full_path.startswith(BASE_DIR) and os.path.exists(full_path):
        return FileResponse(full_path)
    return HTMLResponse(status_code=404)


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


@app.get('/report')
async def report(sn_device: str, featureThreshold: List[int] = Query(None)):
    origin_fs = device_service.devices_meta[sn_device]["config"]["featureThreshold"]
    await make_report(sn_device, featureThreshold, origin_fs)
    return FileResponse(f'{BASE_DIR}/assets/report.json')


print("BASE DIR: ", BASE_DIR)
print("PHOTO DIR: ", settings.PHOTO_DIR)
print("FIRMWARE DIR: ", FIRMWARE_DIR)
print("MQTT_PORT_FOR_TERMINAL: ", s.MQTT_PORT_FOR_TERMINAL)
print("HOST_FOR_TERMINAL: ", s.HOST_FOR_TERMINAL)
print("PORT_FOR_TERMINAL: ", s.PORT_FOR_TERMINAL)


def on_reconnect_rmq():
    device_service.devices = set()


@app.on_event("startup")
async def startup_event():
    await rabbit_mq.start(on_reconnect_rmq)
    asyncio.create_task(rabbit_mq.monitor_connection())

    if s.MOCK_DEVICE:
        asyncio.create_task(mock_run())
        return

    PersonPhoto.load_faces()
    asyncio.create_task(mqtt_consumer())
    asyncio.create_task(PersonPhoto.save_templates_to_file())

    # Синхронизация всех события при старте приложения
    from services.devices_storage import device_service
    asyncio.create_task(sync_booking_all_devices(device_service.all_sn_list, datetime.now(), ))


if __name__ == '__main__':
    # uvicorn.run(
    #     app=app,
    #     port=settings.SERVER_PORT,
    #     host=settings.SERVER_HOST,
    #     loop="asyncio"
    # )
    from uvicorn import Config, Server

    config = Config(
        app=app,
        port=settings.SERVER_PORT,
        host=settings.SERVER_HOST,
        loop=loop)
    server = Server(config)
    loop.run_until_complete(server.serve())
    # from hypercorn.config import Config
    # from hypercorn.asyncio import serve
    #
    # config = Config()
    # server = f'{settings.SERVER_HOST}:{settings.SERVER_PORT}'
    # config.bind = server
    # asyncio.run(serve(app, config))
