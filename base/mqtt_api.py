import json
import asyncio
from asyncio import Future
from datetime import datetime
from pprint import pprint
from typing import Dict
import aiomqtt
from starlette.datastructures import UploadFile
from services.person_photo import PersonPhoto as person_photo_service

from config import s as settings
from base.log import logger
from services import device_command as person_service
from services.device_command import CommandControlTerminal, ControlAction, CommandUpdateConfig, \
    CommandGetPerson, CommandCheckFace, CommandDeleteAllPerson

FAILURE_CODES_REASON = {
    -2: 'Open photo failure',
    -3: 'Already in face library',
    -4: 'Insert database failure',
    -6: 'Extract feature value failure'
}

futures: Dict[str, asyncio.Future] = {}


async def publish_command_and_wait_result(command, timeout):
    async with aiomqtt.Client(hostname=settings.MQTT_HOST,
                              port=settings.MQTT_PORT,
                              username=settings.MQTT_USER,
                              password=settings.MQTT_PASSWORD) as client:

        # ADD
        # except ExceptionOnPublishMQTTMessage:
        # except ExceptionNoResponseMQTTReceived
        print('***', datetime.now().strftime('%H:%M:%S'), '***')
        print("-----PUBLISH COMMAND TO MQTT------")
        print(f"---TO SN_DEVICE: {command.sn_device}--")
        print("-----       PAYLOAD      ------")
        pprint(command.payload)
        print("-----       PAYLOAD      ------")

        await client.publish(f"/_dispatch/command/{command.sn_device}",
                             payload=json.dumps(command.payload))

        future: Future = asyncio.get_running_loop().create_future()
        futures[command.key_id] = future
        try:
            await asyncio.wait_for(future, timeout=timeout)
            return future.result()
        except asyncio.TimeoutError as e:
            return None
        except Exception as e:
            return None
        finally:
            futures.pop(command.key_id, None)


def save_template_from_answer(answer):
    if answer:
        for created_person in answer["operations"]["result"]:
            if created_person["code"] == 0:
                person_photo_service.save_person_template_if_not_exist(
                    created_person["id"],
                    created_person["feature"],
                )


def delete_template_from_answer(answer):
    if answer and answer["operations"].get('result'):
        for deleted_person in answer["operations"]["result"]:
            if deleted_person["code"] == 0:
                person_photo_service.delete_template(
                    deleted_person["id"],
                )


def is_answer_has_error(command, answer):
    errors = []
    if answer is None:
        logger.error(
            f' ![+]ERROR Not receive answer from MQTT '
            f'\n Command={command.payload}'
        )
        errors.append({
            'reason': "ERROR Not receive answer from MQTT",
            'details': 'See Python site logs',
            'operations': 'Operations',
        })
        return errors

    if answer["operations"].get('executeStatus'):
        # CommandDeleteAllPerson
        if answer["operations"].get('executeStatus') == 2:
            logger.error(
                f' ![+]ERROR Some operations'
                f'\n Answer= ${json.dumps(answer)}'
                f'\n Command={command.payload}'
                f'\n ERROR Operation={answer["operations"]}'
            )

    if command.type not in [
        CommandGetPerson.type,
        CommandControlTerminal.type,
        CommandUpdateConfig.type,
        CommandCheckFace.type,
        CommandDeleteAllPerson.type

    ]:
        if isinstance(answer["operations"]["result"], list):
            # Собрать все ошибки по каждой операции
            for operation in answer["operations"]["result"]:
                if operation["code"] < 0:
                    errors.append({
                        'reason': 'operation failed',
                        'details': FAILURE_CODES_REASON.get(operation["code"], "Not details"),
                        'operation': operation
                    })
                    logger.error(
                        f' ![+]ERROR Some operations'
                        f'\n Answer= ${json.dumps(answer)}'
                        f'\n Command={command.payload}'
                        f'\n ERROR Operation={operation}'
                        f'\n Details = {FAILURE_CODES_REASON.get(operation["code"], "Not details")}'
                    )
            return errors

        if isinstance(answer["operations"]["result"], dict):
            if answer["operations"]["result"]["code"] < 0:
                errors.append({
                    'reason': 'operation failed',
                    'details': FAILURE_CODES_REASON.get(answer["operations"]["result"]["code"],
                                                        "Not details"),
                    'operation': {answer["operations"]}
                })
                logger.error(
                    f' ![+]ERROR Some operations'
                    f'\n Answer= ${json.dumps(answer)}'
                    f'\n Command={command.payload}'
                    f'\n ERROR operation={answer["operations"]["result"]}'
                    f'\n Details = {FAILURE_CODES_REASON.get(answer["operations"]["result"]["code"], "Not details")} '
                )
            return errors

    return errors


async def create_or_update(sn_device, id_person, firstName, lastName, photo, cardNumber,
        timeout=settings.TIMEOUT_MQTT_RESPONSE):
    import base64
    if photo and isinstance(photo, UploadFile):
        photo = base64.b64encode(photo.file.read()).decode("utf-8")

    person_json = person_service.create_person_json(
        id=id_person,
        firstName=firstName,
        lastName=lastName,
        face_str=photo,
        cardNumber=cardNumber
    )

    person_response = await get_person(id_person=id_person, sn_device=sn_device, )

    if person_response["answer"]["operations"]["executeStatus"] == 2:
        command = person_service.CommandCreatePerson(sn_device=sn_device)
        command.add_person(person_json)
    else:
        command = person_service.CommandUpdatePerson(sn_device=sn_device)
        command.update_person(person_json)

    answer = await publish_command_and_wait_result(command, timeout=timeout)

    save_template_from_answer(answer)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def process_batch_create(sn_device, batch_persons, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    # Для создания людей используем одну задачу

    command = person_service.CommandCreatePerson(sn_device=sn_device)

    for person in batch_persons:
        person_json = person_service.create_person_json(
            id=int(person["id"]),
            firstName=person["firstName"],
            lastName=person["lastName"],
            face_str=person["picture"],
            cardNumber=person["cardNumber"]
        )
        command.add_person(person_json)
    answer = await publish_command_and_wait_result(command, timeout=timeout)

    # Заносим созданные шаблоны в наш список
    save_template_from_answer(answer)

    return is_answer_has_error(command, answer)


async def process_batch_update(sn_device, batch_persons, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    # Для обновления людей используем несколько асинхронных задач
    print(f'batch {len(batch_persons)}')
    all_commands = []

    for person in batch_persons:
        person_json = person_service.create_person_json(
            id=int(person["id"]),
            firstName=person["firstName"],
            lastName=person["lastName"],
            face_str=person["picture"],
            cardNumber=person["cardNumber"]
        )

        command_update = person_service.CommandUpdatePerson(sn_device=sn_device)
        command_update.update_person(person_json)
        all_commands.append(command_update)

    map_commands_task = {c.key_id: c for c in all_commands}

    all_commands_tasks = [
        asyncio.create_task(publish_command_and_wait_result(command, timeout=timeout),
                            name=command.key_id)
        for command in all_commands]

    done_tasks, _ = await asyncio.wait(all_commands_tasks)
    errors = []
    for done_task in done_tasks:
        command = map_commands_task[done_task.get_name()]
        errors += is_answer_has_error(command, done_task.result())
    return errors


async def batch_create_or_update(
        sn_device,
        persons, batch_size=2,
        timeout=settings.TIMEOUT_MQTT_RESPONSE
):
    persons_result = await get_all_person(sn_device)

    if persons_result["has_error"]:
        return persons_result

    all_person_ids = list(map(lambda user: int(user["id"]),
                              persons_result["answer"]["operations"]["users"]))
    person_for_create = []
    person_for_update = []

    for p in persons:
        if int(p["id"]) in all_person_ids:
            person_for_update.append(p)
        else:
            person_for_create.append(p)

    errors = []

    if person_for_create:
        person_create_result = await process_batch_create(sn_device, person_for_create)
        errors += person_create_result

    for i in range(0, len(person_for_update), batch_size):
        batch = person_for_update[i:i + batch_size]
        task = asyncio.create_task(process_batch_update(sn_device, batch, timeout))
        errors += await task

    print(f'Batch create {len(person_for_create)}')
    print(f'Batch update {len(person_for_update)}')

    return {
        "command": persons,
        "answer": "",
        "has_error": errors
    }


async def get_all_person(sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = person_service.CommandGetPerson(sn_device=sn_device)
    command.search_person("")
    answer = await publish_command_and_wait_result(command, timeout=timeout)

    return {
        "command": command.payload,
        "answer": answer,
        "has_error": is_answer_has_error(command, answer)
    }


async def get_person(id_person, sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = person_service.CommandGetPerson(sn_device=sn_device)
    command.search_person(id_person)
    answer = await publish_command_and_wait_result(command, timeout=timeout)

    return {
        "command": command.payload,
        "answer": answer,
        "has_error": is_answer_has_error(command, answer)
    }


async def delete_person(sn_device: str, id: int = None, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    # TODO: Удалять фото также

    if not id:
        command = person_service.CommandDeleteAllPerson(sn_device=sn_device)
        command.delete_all_person()
    else:
        command = person_service.CommandDeletePerson(sn_device=sn_device)
        command.delete_person(id)

    answer = await publish_command_and_wait_result(command, timeout=timeout)

    delete_template_from_answer(answer)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def control_action(action, sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandControlTerminal(sn_device=sn_device)

    if action == ControlAction.RESTART_SYSTEM:
        command.restart_system()
    if action == ControlAction.RESTART_SOFTWARE:
        command.restart_software()
    if action == ControlAction.DOOR_OPEN:
        command.open_door()
    if action == ControlAction.UPDATE_SOFTWARE:
        command.update_software(firmware_url=f'{settings.FIRMWARE_URL}/{settings.FIRMWARE_FILE}')

    answer = await publish_command_and_wait_result(command, timeout=timeout)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def control_action_set_ntp(sn_device, payload, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandControlTerminal(sn_device=sn_device)
    command.set_ntp(**payload)
    answer = await publish_command_and_wait_result(command, timeout=timeout)
    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def update_config(payload, sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandUpdateConfig(sn_device=sn_device)
    command.update_config(payload)
    answer = await publish_command_and_wait_result(command, timeout=timeout)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def check_face(photo_base64, sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandCheckFace(sn_device=sn_device)
    command.check_face(photo_base64)
    answer = await publish_command_and_wait_result(command, timeout)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }
