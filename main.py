import threading
import uvicorn
from fastapi import FastAPI
from starlette.responses import FileResponse
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

try:
    app.mount(
        '/dashboard',
        StaticFiles(directory=f'{BASE_DIR}/dashboard/dist', html=True),
        name='static',
    )
except RuntimeError:
    "Директория не существует dist"
    pass


# Маршрут для отображения SPA-приложения на префиксном пути
@app.get('/dashboard/{path:path}')
def index(path: str):
    return FileResponse(f'{BASE_DIR}/dashboard/dist/index.html')


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
