import base64
import os
from datetime import datetime

from starlette.testclient import TestClient

import config

from faker import Faker
from base import mqtt_api
from main import app
from services.person_photo import PersonPhoto

fake = Faker()


def data_set(number=10):
    mqtt_api.delete_person(sn_device=config.TEST_SN_DEVICE)

    personFullName = fake.name()
    firstName = personFullName.split(' ')[0]
    lastName = personFullName.split(' ')[1]
    faceset_path = f'{config.PHOTO_DIR}/faceset'
    with TestClient(app) as client:
        def get_photo_url(person_id):
            return f'{client.base_url}{config.PHOTO_PATH}/{person_id}.jpg'

        PersonPhoto.get_photo_url = get_photo_url

        for id_person, photo_file in enumerate(os.listdir(faceset_path)[:number]):
            with open(f"{faceset_path}/{photo_file}", "rb") as image_file:
                photo_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            result = mqtt_api.create_or_update(
                sn_device=config.TEST_SN_DEVICE,
                id_person=id_person + 1,
                firstName=firstName,
                lastName=lastName,
                photo=photo_base64,
            )

    mqtt_api.delete_person(sn_device=config.TEST_SN_DEVICE)


def test_data_set_10():
    t1 = datetime.now()
    data_set(10)
    t2 = datetime.now()
    print(f'Total: 10 Person - {(t2 - t1).total_seconds()}')


def test_data_set_100():
    t1 = datetime.now()
    data_set(10)
    t2 = datetime.now()
    print(f'Total: 100 Person - {(t2 - t1).total_seconds()}')


def test_rabbit(rabbitmq):
    print("checking first channel")
    channel = rabbitmq.channel()
    assert channel.is_open
    print(rabbitmq)
