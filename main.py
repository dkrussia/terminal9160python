import threading
import uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from config import (
    BASE_URL,
    BASE_DIR,
    PHOTO_URL,
    PHOTO_DIR,
    PHOTO_PATH,
    SERVER_PORT,
    SERVER_HOST
)
from base.endpoints import device_router, person_router
from base.mqtt_client import mqtt_client
from base.rmq_client import global_rmq_chanel, start_rmq_consume

print("BASE URL: ", BASE_URL)
print("BASE DIR: ", BASE_DIR)
print("PHOTO URL: ", PHOTO_URL)
print("PHOTO DIR: ", PHOTO_DIR)
print("PHOTO_PATH: ", PHOTO_PATH)

app = FastAPI()
app.mount(PHOTO_PATH, StaticFiles(directory=PHOTO_DIR), name="photo")
app.include_router(person_router, tags=['Управление персонами'])
app.include_router(device_router, tags=['API for Device'])
# TODO: firmware url + generate Enum firmware file

# Test
# При добавлении персон в терминал, надо дождаться результата выполнения
# и затем уже отправлять снова.
# Если надо загрузить много персон сразу, то делаем это пачками по 100 человек.

if __name__ == '__main__':
    mqtt_client.start_receiving()
    threading.Thread(target=start_rmq_consume, args=(global_rmq_chanel,)).start()
    uvicorn.run(
        app=app,
        port=SERVER_PORT,
        host=SERVER_HOST,
    )
