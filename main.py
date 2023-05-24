import threading
import time

import uvicorn
from amqpstorm import AMQPChannelError
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
from base.endpoints import base_router
from base.mqtt_client import mqtt_client
from services.rmq import global_rmq_chanel

print("BASE URL: ", BASE_URL)
print("BASE DIR: ", BASE_DIR)
print("PHOTO URL: ", PHOTO_URL)
print("PHOTO DIR: ", PHOTO_DIR)
print("PHOTO_PATH: ", PHOTO_PATH)

app = FastAPI()
app.mount(PHOTO_PATH, StaticFiles(directory=PHOTO_DIR), name="photo")
app.include_router(base_router, tags=['API'])


# Test
# При добавлении персон в терминал, надо дождаться результата выполнения
# и затем уже отправлять снова.
# Если надо загрузить много персон сразу, то делаем это пачками по 100 человек.

def start_consume(chanel):
    while True:
        try:
            chanel.start_consuming()
        except AMQPChannelError as e:
            time.sleep(1)
            print(e)


if __name__ == '__main__':
    mqtt_client.start_receiving()
    threading.Thread(target=start_consume, args=(global_rmq_chanel,)).start()
    uvicorn.run(
        app=app,
        port=SERVER_PORT,
        host=SERVER_HOST,
    )
