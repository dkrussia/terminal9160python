import time
from typing import Optional

from .person_photo import PersonPhoto as person_photo_service


class CreatePersonJsonException(Exception):
    pass


def create_person_json(id: int, lastName: str = "", firstName: str = "", face_str: str = ""):
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
        "cardNum": str(id),
        "wiegandNum": str(id),
        "company": "",
        "department": "",
        "group": "",
        "remark": "",
        "expiry": ""
    }
    if face_str:
        photo_url = person_photo_service.base64_to_file(person_id=id, photo_base64=face_str)
        d["faceUrl"] = photo_url
    return d


def delete_person_json(id: int):
    return {
        "id": id,
        "params": {},
    }


def query_person_json(id: int):
    return {
        "emp_id": str(id),
        "keyword": "",
        "need_feature": False,
        "need_photo": False,
        "page_num": 1000,
        "page_idx": 0
    }


class CommandForTerminal:
    type = 0

    def __init__(self, sn_device: str, id_command: Optional[int] = None):
        if not id_command:
            id_command = int(time.time())

        self.sn_device = sn_device
        self.id_command = id_command

        self.payload = {
            "type": self.type,
            "id": self.id_command,
            "devSn": self.sn_device,
            "feedbackUrl": "",
        }

    def result_json(self):
        return self.payload

    def add_operation_in_list(self, data_json: dict):
        if not self.payload.get('operations', None):
            self.payload["operations"] = [data_json]
            return
        self.payload["operations"].append(data_json)

    def set_operation_as_dict(self, data_json: dict):
        self.payload["operations"] = data_json


class CommandCreatePerson(CommandForTerminal):
    type = 3

    def add_person(self, person_json: dict):
        self.add_operation_in_list(person_json)


class CommandUpdatePerson(CommandForTerminal):
    type = 4

    def update_person(self, person_json: dict):
        self.set_operation_as_dict(person_json)


class CommandDeletePerson(CommandForTerminal):
    type = 5

    # Удаление так же как и создание, можно выполнять списком
    def delete_person(self, id):
        payload = delete_person_json(id=id)
        self.add_operation_in_list(payload)


class CommandGetPerson(CommandForTerminal):
    type = 1000

    def search_person(self, id):
        payload = query_person_json(id)
        self.set_operation_as_dict(payload)
