import json

from starlette.datastructures import UploadFile

from base.mqtt_client import ExceptionOnPublishMQTTMessage, ExceptionNoResponseMQTTReceived
from config import s as settings
from base.log import logger
from services import device_command as person_service
from services.device_command import CommandControlTerminal, ControlAction, CommandUpdateConfig, \
    CommandGetPerson
from services.devices import device_service

mqtt_client = None

FAILURE_CODES_REASON = {
    -2: 'Open photo failure',
    -3: 'Already in face library',
    -4: 'Insert database failure',
    -6: 'Extract feature value failure'
}


def is_answer_has_error(command, answer):
    if answer is None:
        logger.error(
            f' ![+]ERROR Not receive answer from MQTT '
            f'\n Command={command.payload}'
        )
        return True

    if command.type not in [
        CommandGetPerson.type,
        CommandControlTerminal.type,
        CommandUpdateConfig.type
    ]:

        if isinstance(answer["operations"]["result"], list):
            # Собрать все ошибки по каждой операции
            for operation in answer["operations"]["result"]:
                if operation["code"] < 0:
                    logger.error(
                        f' ![+]ERROR Some operations'
                        f'\n Answer= ${json.dumps(answer)}'
                        f'\n Command={command.payload}'
                        f'\n ERROR Operation={operation}'
                        f'\n Details = {FAILURE_CODES_REASON.get(operation["code"], "Not details")}'
                    )
                    return True

        if isinstance(answer["operations"]["result"], dict):
            if answer["operations"]["result"]["code"] < 0:
                logger.error(
                    f' ![+]ERROR Some operations'
                    f'\n Answer= ${json.dumps(answer)}'
                    f'\n Command={command.payload}'
                    f'\n ERROR operation={answer["operations"]["result"]}'
                    f'\n Details = {FAILURE_CODES_REASON.get(answer["operations"]["result"]["code"], "Not details")} '
                )
                return True

    return False


def create_or_update(sn_device, id_person, firstName, lastName, photo,
        timeout=settings.TIMEOUT_MQTT_RESPONSE):
    import base64
    if photo and isinstance(photo, UploadFile):
        photo = base64.b64encode(photo.file.read()).decode("utf-8")
    print(photo)
    person_json = person_service.create_person_json(
        id=id_person,
        firstName=firstName,
        lastName=lastName,
        face_str=photo
    )

    person_response = get_person(id_person=id_person, sn_device=sn_device)

    if person_response["answer"]["operations"]["executeStatus"] == 2:
        command = person_service.CommandCreatePerson(sn_device=sn_device)
        command.add_person(person_json)
    else:
        command = person_service.CommandUpdatePerson(sn_device=sn_device)
        command.update_person(person_json)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=timeout)
    except ExceptionOnPublishMQTTMessage:
        answer = None
    except ExceptionNoResponseMQTTReceived:
        answer = None

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


def get_all_person(sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = person_service.CommandGetPerson(sn_device=sn_device)
    command.search_person("")
    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=timeout)
    except ExceptionOnPublishMQTTMessage:
        answer = None
    except ExceptionNoResponseMQTTReceived:
        answer = None

    return {
        "command": command.payload,
        "answer": answer,
        "has_error": is_answer_has_error(command, answer)
    }


def get_person(id_person, sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = person_service.CommandGetPerson(sn_device=sn_device)
    command.search_person(id_person)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=timeout)
    except ExceptionOnPublishMQTTMessage:
        answer = None
    except ExceptionNoResponseMQTTReceived:
        answer = None

    return {
        "command": command.payload,
        "answer": answer,
        "has_error": is_answer_has_error(command, answer)
    }


def delete_person(sn_device: str, id: int = None, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    # TODO: Удалять фото также
    command = person_service.CommandDeletePerson(sn_device=sn_device)

    if not id:
        all_users_response = get_all_person(sn_device)
        if all_users_response['answer']:
            # Надо ли обрабатывать этот случай?
            for user in all_users_response['answer']['operations']['users']:
                command.delete_person(user['id'])
    else:
        command.delete_person(id)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=timeout)
    except ExceptionOnPublishMQTTMessage:
        answer = None
    except ExceptionNoResponseMQTTReceived:
        answer = None

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


def control_action(action, sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandControlTerminal(sn_device=sn_device)

    if action == ControlAction.RESTART_SYSTEM:
        command.restart_system()
    if action == ControlAction.RESTART_SOFTWARE:
        command.restart_software()
    if action == ControlAction.DOOR_OPEN:
        command.open_door()
    if action == ControlAction.UPDATE_SOFTWARE:
        command.update_software(firmware_url=f'{settings.FIRMWARE_URL}/{settings.FIRMWARE_FILE}')

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=timeout)
    except ExceptionOnPublishMQTTMessage:
        answer = None
    except ExceptionNoResponseMQTTReceived:
        answer = None

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


def update_config(payload, sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandUpdateConfig(sn_device=sn_device)
    command.update_config(payload)

    try:
        answer = mqtt_client.send_command_and_wait_result(command, timeout=timeout)
    except ExceptionOnPublishMQTTMessage:
        answer = None
    except ExceptionNoResponseMQTTReceived:
        answer = None

    if answer:
        device_service.update_meta_update_conf(sn_device, answer.get('operations'))

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }
