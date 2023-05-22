import os

SERVER_HOST = "192.168.1.68"
SERVER_PORT = 8080

BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

PHOTO_DIR = f"{BASE_DIR}/photo"
PHOTO_PATH = "/photo"
PHOTO_URL = f"{BASE_URL}{PHOTO_PATH}"

MQTT_HOST = SERVER_HOST
MQTT_PORT = 8086
MQTT_USER = "admin"
MQTT_PASSWORD = "admin123"

TEST_SN_DEVICE = "YGKJ202107TR08EL0007"

with open(f'{BASE_DIR}/tests/base64photo.txt', 'r') as f:
    TEST_MY_PHOTO = f.read()
