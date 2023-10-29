import asyncio
import os
import pathlib
import sys

import uvicorn

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html

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
from services.person_photo import PersonPhoto

if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

pathlib.Path(PHOTO_DIR).mkdir(parents=True, exist_ok=True)
pathlib.Path(FIRMWARE_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(docs_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(PHOTO_PATH, StaticFiles(directory=PHOTO_DIR), name="photo")
app.mount(FIRMWARE_PATH, StaticFiles(directory=FIRMWARE_DIR), name="firmware")

app.include_router(person_router, tags=['Persons'])
app.include_router(device_router, tags=['API Device'])
app.include_router(device_push_router, tags=['Push From Device'])


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


print("BASE DIR: ", BASE_DIR)
print("PHOTO DIR: ", PHOTO_DIR)
print("PHOTO DIR: ", FIRMWARE_DIR)
print("MQTT_PORT_FOR_TERMINAL: ", s.MQTT_PORT_FOR_TERMINAL)
print("HOST_FOR_TERMINAL: ", s.HOST_FOR_TERMINAL)
print("PORT_FOR_TERMINAL: ", s.PORT_FOR_TERMINAL)


@app.on_event("startup")
async def startup_event():
    await rabbit_mq.start()

    if s.MOCK_DEVICE:
        asyncio.create_task(mock_run())
        return

    PersonPhoto.load_faces()
    asyncio.create_task(mqtt_consumer())
    asyncio.create_task(PersonPhoto.save_templates_to_file())


if __name__ == '__main__':
    uvicorn.run(
        app=app,
        port=settings.SERVER_PORT,
        host=settings.SERVER_HOST,
    )
