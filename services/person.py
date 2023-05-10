class CreatePersonJsonException(Exception):
    pass


def create_person_json(id: int, lastName: str = "", firstName: str = "", ):
    if not isinstance(id, int) or id < 1:
        raise CreatePersonJsonException
    return {
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


def delete_person_json(id: int):
    return {
        "id": id,
        "params": {},
    }


class CommandForTerminal:
    type = 0

    def __init__(self, *, id_command: int, sn_device: str):
        self.payload = {
            "type": CommandCreatePerson.type,
            "id": id_command,
            "devSn": sn_device,
            "feedbackUrl": "",
        }

    def result(self):
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
    def add_person(self, person_json):
        self.add_operation_in_list(person_json)
