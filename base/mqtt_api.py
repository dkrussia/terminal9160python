from fastapi import UploadFile
from base.mqtt_client import mqtt_client, ExceptionOnPublishMQTTMessage
from config import TIMEOUT_WAIT_MQTT_ANSWER, TEST_SN_DEVICE
from services import device_command as person_service
from services.device_command import CommandControlTerminal, ControlAction


def create_or_update(sn_device, id_person, firstName, lastName, photo):
    import base64
    if photo and isinstance(photo, UploadFile):
        photo = base64.b64encode(photo.file.read()).decode("utf-8")

    person_json = person_service.create_person_json(
        id=id_person,
        firstName=firstName,
        lastName=lastName,
        face_str=photo
    )

    person_response = get_person(id_person=id_person)

    if person_response["answer"]["operations"]["executeStatus"] == 2:
        command = person_service.CommandCreatePerson(sn_device=sn_device)
        command.add_person(person_json)
    else:
        command = person_service.CommandUpdatePerson(sn_device=sn_device)
        command.update_person(person_json)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
        "answer": answer,
        "command": command.result_json()
    }


def get_all_user(sn_device=TEST_SN_DEVICE):
    command = person_service.CommandGetPerson(sn_device=sn_device)
    command.search_person("")
    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
        "command": command.result_json(),
        "answer": answer,
    }


def get_person(id_person, sn_device=TEST_SN_DEVICE):
    command = person_service.CommandGetPerson(sn_device=sn_device)
    command.search_person(id_person)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
        "command": command.result_json(),
        "answer": answer,
    }


def delete_person(id: int = None):
    # TODO: Удалять фото также
    command = person_service.CommandDeletePerson(sn_device=TEST_SN_DEVICE)

    if not id:
        all_users_response = get_all_user()
        if all_users_response['answer']:
            # Надо ли обрабатывать этот случай?
            for user in all_users_response['answer']['operations']['users']:
                command.delete_person(user['id'])
    else:
        command.delete_person(id)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
        "answer": answer,
        "command": command.result_json()
    }


def control_action(action, sn_device=TEST_SN_DEVICE):

    command = CommandControlTerminal(sn_device=sn_device)

    print(action, type(action))

    if action == ControlAction.RESTART_SYSTEM:
        command.restart_system()
    if action == ControlAction.RESTART_SOFTWARE:
        command.restart_software()
    if action == ControlAction.DOOR_OPEN:
        command.open_door()
    # TODO: Update Software
    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=TIMEOUT_WAIT_MQTT_ANSWER)
    except ExceptionOnPublishMQTTMessage:
        answer = None

    return {
        "answer": answer,
        "command": command.result_json()
    }
