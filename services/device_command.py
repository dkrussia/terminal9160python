"""
Создание json-команд для терминалов 9160
Которые будут отправлены в MQTT[commands_$sn_device]
"""
import copy
import random
from datetime import datetime
from typing import Optional
from enum import Enum
from config import s as settings

from .person_photo import PersonPhoto as person_photo_service


class ControlAction(str, Enum):
    # Перезагрузка
    RESTART_SYSTEM = 'RESTART_SYSTEM'
    # Перезагрузка софта? (Не включился экран, не работает mqtt)
    RESTART_SOFTWARE = 'RESTART_SOFTWARE'
    # Открытие на проход(Загорается зеленная рамка)
    DOOR_OPEN = 'DOOR_OPEN'
    # Обновить прошивку
    UPDATE_SOFTWARE = 'UPDATE_SOFTWARE'
    #
    UPLOAD_DIAGNOSTIC = 'UPLOAD_DIAGNOSTIC'


class CreatePersonJsonException(Exception):
    pass


def create_person_json(
        id: int, lastName: str = "",
        firstName: str = "",
        cardNumber: int = None,
        face_str: str = ""):
    if not isinstance(id, int) or id < 1:
        raise CreatePersonJsonException
    # TODO: add faceUrl
    d = {
        "createBy": "",
        "createTime": 0,
        "deptId": 0,
        "id": id,
        "sex": 0,
        "status": 0,
        "updateBy": "",
        "userCode": str(id),
        "userName": "",
        "firstName": lastName,
        "lastName": firstName,
        "userPhone": "",
        "cardNum": str(cardNumber),
        "wiegandNum": str(cardNumber),
        "company": "",
        "department": "",
        "group": "",
        "remark": "",
        "expiry": ""
    }
    # "expiry": "2023-08-20 18:25:00,2023-08-20 19:06:00"
    if not face_str:
        return d

    if person_photo_service.get_face_template(id):
        d["feature"] = person_photo_service.get_face_template(id)
        return d

    if settings.MCI_PHOTO_MANAGER:
        d["faceUrl"] = person_photo_service.get_photo_url(person_id=id)
    else:
        photo_url = person_photo_service.base64_to_file(person_id=id, photo_base64=face_str)
        d["faceUrl"] = photo_url

    return d


def delete_person_json(id: int):
    return {
        "id": id,
        "params": {},
    }


def query_person_json(id, total: int = 3000):
    # ID int/empty string

    return {
        "emp_id": str(id),
        "keyword": "",
        "need_feature": False,
        "need_photo": False,
        "page_num": total,
        "page_idx": 0
    }


class BaseCommand:
    type = 0

    def __init__(self, sn_device: str, id_command: Optional[int] = None):
        if not id_command:
            # 1685446768.340883 -> 340883
            id_command = int(str(datetime.now().timestamp()).split('.')[1]) + random.randint(1,
                                                                                             100000000)

        self.sn_device = sn_device
        self.id_command = id_command

        self.payload: dict = {
            "type": self.type,
            "id": self.id_command,
            "devSn": self.sn_device,
            "feedbackUrl": "",
        }

    @property
    def key_id(self):
        return f'{self.id_command}_{self.sn_device}'

    def add_operation_in_list(self, data_json: dict):
        if not self.payload.get('operations', None):
            self.payload["operations"] = [data_json]
            return
        self.payload["operations"].append(data_json)

    def set_operation_as_dict(self, data_json: dict):
        self.payload["operations"] = data_json

    @property
    def log_payload(self):
        payload_logs = copy.deepcopy(self.payload)
        operations: dict | list = payload_logs.get('operations')
        keys_to_remove = ['createBy', 'deptId', 'sex',
                          'status', 'userName', 'userPhone',
                          'company', 'department',
                          'group', 'remark', 'createTime', 'updateBy']
        if operations:
            if isinstance(operations, list):
                for item in operations:
                    if item.get('feature'):
                        feature = item['feature']
                        item['feature'] = feature[:5] + '...' + feature[-5:]
                    for key in keys_to_remove:
                        item.pop(key, None)
            else:
                if operations.get('feature'):
                    feature = operations['feature']
                    operations['feature'] = feature[:5] + '...' + feature[-5:]
                    for key in keys_to_remove:
                        operations.pop(key, None)
        return payload_logs


class CommandCreatePerson(BaseCommand):
    type = 3

    def add_person(self, person_json: dict):
        self.add_operation_in_list(person_json)


class CommandUpdatePerson(BaseCommand):
    type = 4

    def update_person(self, person_json: dict):
        self.set_operation_as_dict(person_json)


class CommandDeletePerson(BaseCommand):
    type = 5

    # Удаление так же как и создание, можно выполнять списком
    def delete_person(self, id):
        payload = delete_person_json(id=id)
        self.add_operation_in_list(payload)


class CommandDeleteAllPerson(BaseCommand):
    type = 1007

    def delete_all_person(self, ):
        self.set_operation_as_dict({"deleteAll": True})


class CommandGetPerson(BaseCommand):
    type = 1000

    def search_person(self, id):
        payload = query_person_json(id)
        self.set_operation_as_dict(payload)


class CommandGetTotalPerson(CommandGetPerson):
    def get_total(self, ):
        payload = query_person_json("", total=1)
        self.set_operation_as_dict(payload)


class CommandControlTerminal(BaseCommand):
    type = 9

    def set_ntp(self, timeServer="", timeZone="", ntp=False, time=""):
        self.set_operation_as_dict({
            "devAction": 1,
            "timeServer": timeServer,
            "timeZone": timeZone,
            "ntp": ntp,
            "time": time,
            "id": self.sn_device
        })

    def restart_system(self):
        self.set_operation_as_dict({
            "devAction": 2,
            "apkUrl": "",
            "id": self.sn_device
        })

    def restart_software(self):
        self.set_operation_as_dict({
            "devAction": 3,
            "apkUrl": "",
            "id": self.sn_device
        })

    def open_door(self):
        self.set_operation_as_dict({
            "devAction": 4,
            "id": self.sn_device
        })

    def update_software(self, firmware_url):
        self.set_operation_as_dict({
            "devAction": 5,
            "apkUrl": firmware_url,
            "id": self.sn_device
        })

    def upload_logs(self, ):
        self.set_operation_as_dict({
            "devAction": 10,
            "id": self.sn_device
        })


class CommandUpdateConfig(BaseCommand):
    type = 8

    def update_config(self, payload):
        self.set_operation_as_dict(payload)


class CommandCheckFace(BaseCommand):
    type = 1004

    def check_face(self, photo_base64):
        self.set_operation_as_dict({
            "photo": photo_base64
        })


class CommandGetAccessLog(BaseCommand):
    type = 1008

    def find(self, startStamp, endStamp, keyword):
        self.set_operation_as_dict({
            "startStamp": startStamp,
            "endStamp": endStamp,
            "keyword": keyword
        })
