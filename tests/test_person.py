import os

import pytest
from starlette.testclient import TestClient

from main import BASE_URL, app, PHOTO_URL
from services import person as person_service
from services.person import CreatePersonJsonException


def test_person_create_json(base64_photo):
    test1_json = {
        "createBy": "",
        "createTime": 0,
        "deptId": 0,
        "id": 1000,
        "sex": 0,
        "status": 0,
        "updateBy": "",
        "userCode": "1000",
        "faceUrl": f"{PHOTO_URL}/1000.jpg",
        "userName": "",
        "firstName": "Sergey",
        "lastName": "Kuznetsov",
        "cardNum": "1000",
        "wiegandNum": "1000",
        "userPhone": "",
        "company": "",
        "department": "",
        "group": "",
        "remark": "",
        "expiry": ""
    }
    json = person_service.create_person_json(1000, 'Sergey', 'Kuznetsov', face_str=base64_photo)
    assert json == test1_json

    with TestClient(app) as client:
        response = client.get("/photo/1000.jpg")
        assert response.status_code == 200

    test2_json = {
        "createBy": "",
        "createTime": 0,
        "deptId": 0,
        "id": 1000,
        "sex": 0,
        "status": 0,
        "updateBy": "",
        "userCode": "1000",
        "userName": "",
        "firstName": "",
        "lastName": "",
        "cardNum": "1000",
        "wiegandNum": "1000",
        "userPhone": "",
        "company": "",
        "department": "",
        "group": "",
        "remark": "",
        "expiry": ""
    }
    json = person_service.create_person_json(1000, '', '',  face_str="")
    assert json == test2_json

    with pytest.raises(CreatePersonJsonException):
        person_service.create_person_json(0)
    with pytest.raises(CreatePersonJsonException):
        person_service.create_person_json(-1)


def test_command_base():
    person_command = person_service.CommandForTerminal(id_command=1, sn_device="XYZ")
    assert person_command.payload["id"] == 1
    assert person_command.payload["devSn"] == "XYZ"


def test_command_create_persons():
    person_command = person_service.CommandCreatePerson(id_command=1, sn_device="XYZ")
    assert person_command.type == 3

    person_json = person_service.create_person_json(1, "Sergey", "Kuznetsov")
    person_command.add_person(person_json)
    person_command.add_person(person_json)

    assert len(person_command.payload["operations"]) == 2


def test_command_update_person():
    person_command = person_service.CommandUpdatePerson(id_command=1, sn_device="XYZ")
    assert person_command.type == 4

    person_json = person_service.create_person_json(1, "Sergey", "Kuznetsov")
    person_command.update_person(person_json)

    assert isinstance(person_command.payload["operations"], dict)


def test_command_delete_persons():
    person_command = person_service.CommandDeletePerson(id_command=1, sn_device="XYZ")
    assert person_command.type == 5
    person_delete = person_service.delete_person_json(1)
    test_json = {"id": 1, "params": {}}
    assert person_delete == test_json
