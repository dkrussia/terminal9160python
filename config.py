import os

from pydantic.v1 import BaseSettings

CORS = ['*']
MAX_WORKERS_MCI_COMMAND = 8

SERVER_MODE = os.getenv("SERVER_MODE", "local")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'assets/logs')
FIRMWARE_DIR = os.path.join(BASE_DIR, 'assets/firmware')

PHOTO_PATH = "/photo"
FIRMWARE_PATH = "/firmware"

DEVICE_JSON_DATA_FILE = os.path.join(BASE_DIR, 'assets/devices_db.json')
FACE_TEMPLATES_FILE = os.path.join(BASE_DIR, 'assets/face_template_cache.json')

try:
    with open(os.path.join(BASE_DIR, 'utils', 'base64photo.txt'), 'r') as f:
        TEST_MY_PHOTO = f.read()
except FileExistsError:
    TEST_MY_PHOTO = ""


class Settings(BaseSettings):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8888
    #
    #
    RMQ_HOST: str = "localhost"
    RMQ_PORT: int = 5672
    # RABBIT CREDENTIALS
    RMQ_USER: str = "guest"
    RMQ_PASSWORD: str = "guest"
    #
    #
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    # MQTT CREDENTIALS
    MQTT_USER: str = "admin"
    MQTT_PASSWORD: str = "public"

    # FOR TERMINAL
    # TERMINAL SHOULD KNOW MAIN HOST, PORT and MQTT PORT
    MQTT_PORT_FOR_TERMINAL: int = 1883
    HOST_FOR_TERMINAL: str = "localhost"
    PORT_FOR_TERMINAL: int = 8888

    FIRMWARE_FILE = 'HR-FaceAC-L01.04.13-DM08.tar.gz'

    TIMEOUT_MQTT_RESPONSE: int = 8
    BATCH_UPDATE_SIZE = 10

    MOCK_DEVICE = False
    MOCK_DEVICE_AMOUNT: int = 31
    MOCK_DEVICE_SUCCESS_CHANCE: int = 99
    MOCK_DEVICE_SUCCESS_TIMEOUT = range(1, 2)
    MOCK_DEVICE_ERROR_TIMEOUT = range(1, 2)

    PHOTO_DIR = os.path.join(BASE_DIR, 'assets/photo')

    FIRMWARE_URL: str = None
    PHOTO_URL: str = None

    MCI_PHOTO_MANAGER: bool = False

    class Config:
        env_file = f"{BASE_DIR}/.env.{SERVER_MODE}"


s = Settings()
s.FIRMWARE_URL = f"http://{s.HOST_FOR_TERMINAL}:{s.PORT_FOR_TERMINAL}{FIRMWARE_PATH}"
s.PHOTO_URL = f"http://{s.HOST_FOR_TERMINAL}:{s.PORT_FOR_TERMINAL}{PHOTO_PATH}"
