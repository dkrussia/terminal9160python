import os

SERVER_HOST = "192.168.129.153"
SERVER_PORT = 8080

BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

PHOTO_DIR = f"{BASE_DIR}/photo"
PHOTO_PATH = "/photo"
PHOTO_URL = f"{BASE_URL}{PHOTO_PATH}"

FIRMWARE_DIR = f"{BASE_DIR}/firmware"
FIRMWARE_PATH = "/firmware"
FIRMWARE_URL = f"{BASE_URL}{FIRMWARE_PATH}"
TEST_FIRMWARE = 'HR-FaceAC-L01.04.13-DM08.tar.gz'

RMQ_HOST = "151.248.125.126"
RMQ_USER = "admin"
RMQ_PASSWORD = "Dormakaba2020"
RMQ_PORT = 5672

MQTT_HOST = SERVER_HOST
MQTT_PORT = 8086
MQTT_USER = "admin"
MQTT_PASSWORD = "admin123"

TIMEOUT_MQTT_RESPONSE = 5

TEST_SN_DEVICE = "YGKJ202107TR08EL0007"
TEST_ID_PERSON = 999

MAX_WORKERS_MCI_COMMAND = 8

with open(f'{BASE_DIR}/tests/base64photo.txt', 'r') as f:
    TEST_MY_PHOTO = f.read()
