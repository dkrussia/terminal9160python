import threading
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, HTMLResponse
from starlette.staticfiles import StaticFiles

from config import (
    BASE_URL,
    BASE_DIR,
    PHOTO_URL,
    PHOTO_DIR,
    PHOTO_PATH,
    SERVER_PORT,
    SERVER_HOST,
    FIRMWARE_PATH,
    FIRMWARE_DIR,
)
from base.endpoints import device_router, person_router
from base.mqtt_client import mqtt_client
from base.rmq_client import rmq_global_chanel, rmq_start_consume

print("BASE URL: ", BASE_URL)
print("BASE DIR: ", BASE_DIR)
print("PHOTO URL: ", PHOTO_URL)
print("PHOTO DIR: ", PHOTO_DIR)
print("PHOTO_PATH: ", PHOTO_PATH)

app = FastAPI()

app.mount(PHOTO_PATH, StaticFiles(directory=PHOTO_DIR), name="photo")
app.mount(FIRMWARE_PATH, StaticFiles(directory=FIRMWARE_DIR), name="firmware")

app.include_router(person_router, tags=['Управление персонами'])
app.include_router(device_router, tags=['API for Device'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://192.168.129.153:9090'
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    '/static',
    StaticFiles(directory=f'{BASE_DIR}/dashboard/dist/static', ),
    name='static',
)


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

mqtt_client.start_receiving()

if __name__ == '__main__':
    threading.Thread(target=rmq_start_consume, args=(rmq_global_chanel,)).start()
    uvicorn.run(
        app=app,
        port=SERVER_PORT,
        host=SERVER_HOST,
    )
