import os

HOST = os.getenv('HOST')

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080

#
BASE_URL = f"http://{HOST or SERVER_HOST}:{SERVER_PORT}"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CORS = ['*']

DEVICE_JSON_DATA_FILE = os.path.join(BASE_DIR, 'devices_db.json')

PHOTO_DIR = os.path.join(BASE_DIR, 'photo')
PHOTO_PATH = "/photo"
PHOTO_URL = f"{BASE_URL}{PHOTO_PATH}"

FIRMWARE_DIR = os.path.join(BASE_DIR, 'firmware')
FIRMWARE_PATH = "/firmware"
FIRMWARE_URL = f"{BASE_URL}{FIRMWARE_PATH}"
TEST_FIRMWARE = 'HR-FaceAC-L01.04.13-DM08.tar.gz'

RMQ_HOST = "localhost"
RMQ_USER = "guest"
RMQ_PASSWORD = "guest"
RMQ_PORT = 5672

# Для отправки в терминал
MQTT_HOST_FOR_TERMINAL = HOST or SERVER_HOST

# Для сервера
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "public"

TIMEOUT_MQTT_RESPONSE = 8

TEST_SN_DEVICE = "YGKJ202107TR08EL0007"
TEST_ID_PERSON = 999

MOCK_DEVICE = False
MOCK_DEVICE_AMOUNT = 31
MOCK_DEVICE_SUCCESS_CHANCE = 99
MOCK_DEVICE_SUCCESS_TIMEOUT = range(1, 2)
MOCK_DEVICE_ERROR_TIMEOUT = range(1, 2)

MAX_WORKERS_MCI_COMMAND = 8

with open(os.path.join(BASE_DIR, 'tests', 'base64photo.txt'), 'r') as f:
    TEST_MY_PHOTO = f.read()
