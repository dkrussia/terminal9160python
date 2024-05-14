import json
import asyncio
from asyncio import Future
from datetime import datetime, timedelta
import base64
from typing import Dict, List
import aiomqtt
from starlette.datastructures import UploadFile
from services.person_photo import PersonPhoto as person_photo_service

from config import s as settings
from base.log import logger, get_logger
from services import device_command as person_service
from services.device_command import CommandControlTerminal, ControlAction, CommandUpdateConfig, \
    CommandGetPerson, CommandCheckFace, CommandDeleteAllPerson, CommandGetTotalPerson, \
    CommandGetAccessLog
from services.persond_ids_storage import PersonStorage

mqtt_push_logger = get_logger('mqtt_publish_command')

FAILURE_CODES_REASON = {
    -2: 'Open photo failure',
    -3: 'Already in face library',
    -4: 'Insert database failure',
    -6: 'Extract feature value failure'
}

futures: Dict[str, asyncio.Future] = {}


def get_expiry_date(is_expiry=False):
    expiry_start = datetime(2000, 1, 1).strftime("%Y-%m-%d %H:%M:%S")
    expiry_end = datetime(2001, 1, 1).strftime("%Y-%m-%d %H:%M:%S")
    if not is_expiry:
        expiry_end = (datetime.now() + timedelta(days=365 * 40)).strftime("%Y-%m-%d %H:%M:%S")
    return f'{expiry_start},{expiry_end}'


async def publish_command_and_wait_result(command, timeout):
    print('***', datetime.now().strftime('%H:%M:%S'), '***')
    print("-----PUBLISH COMMAND TO MQTT------")
    print(f"---TO SN_DEVICE: {command.sn_device}--")
    print("-----       PAYLOAD      ------")
    # pprint(command.log_payload)
    print("-----       PAYLOAD      ------")
    future: Future = asyncio.get_running_loop().create_future()
    futures[command.key_id] = future

    try:
        async with aiomqtt.Client(hostname=settings.MQTT_HOST,
                                  port=settings.MQTT_PORT,
                                  username=settings.MQTT_USER,
                                  password=settings.MQTT_PASSWORD) as client:

            await client.publish(f"/_dispatch/command/{command.sn_device}",
                                 payload=json.dumps(command.payload))
    except Exception as e:
        mqtt_push_logger.error(e, exc_info=True)
        return None

    try:
        await asyncio.wait_for(future, timeout=timeout)
        return future.result()
    except asyncio.TimeoutError as e:
        return None
    except Exception as e:
        return None
    finally:
        f = futures.pop(command.key_id, None)


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


def save_person_ids_in_storage_from_answer(sn_device, answer):
    if answer:
        person_ids = []
        for created_person in answer["operations"]["result"]:
            if created_person["code"] == 0:
                person_ids.append(created_person["id"])
        PersonStorage.add(sn_device, person_ids)


def is_answer_has_error(command, answer):
    print(command.log_payload)
    errors = []
    if answer is None:
        logger.error(
            f'![+]ERROR Not receive answer from MQTT\n'
            f'\t\tCommand={json.dumps(command.log_payload)}'
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
                f'\n Command={json.dumps(command.log_payload)}'
                f'\n ERROR Operation={answer["operations"]}'
            )

    if command.type not in [
        CommandGetPerson.type,
        CommandControlTerminal.type,
        CommandUpdateConfig.type,
        CommandCheckFace.type,
        CommandDeleteAllPerson.type,
        CommandGetAccessLog.type

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
                        f'\n Command={json.dumps(command.log_payload)}'
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
                    f'\n Command={json.dumps(command.log_payload)}'
                    f'\n ERROR operation={answer["operations"]["result"]}'
                    f'\n Details = {FAILURE_CODES_REASON.get(answer["operations"]["result"]["code"], "Not details")} '
                )
            return errors

    return errors


async def create_or_update(
        sn_device,
        id_person,
        firstName,
        lastName,
        photo,
        cardNumber,
        timeout=settings.TIMEOUT_MQTT_RESPONSE
):
    r = await get_person(sn_device=sn_device, id_person=id_person, timeout=10)
    if not r.get('answer'):
        return r

    exp = get_expiry_date(is_expiry=False)
    if photo and isinstance(photo, UploadFile):
        photo = base64.b64encode(photo.file.read()).decode("utf-8")

    person_json = person_service.create_person_json(
        id=id_person,
        firstName=firstName,
        lastName=lastName,
        face_str=photo,
        cardNumber=cardNumber,
        expiry=exp
    )

    if 'users' in r['answer']['operations']:
        command = person_service.CommandUpdatePerson(sn_device=sn_device)
        command.update_person(person_json)
    else:
        command = person_service.CommandCreatePerson(sn_device=sn_device)
        command.add_person(person_json)

    answer = await publish_command_and_wait_result(command, timeout=timeout)
    save_template_from_answer(answer)
    save_person_ids_in_storage_from_answer(sn_device, answer)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def set_person_expired(
        sn_device,
        id_person,
        firstName,
        lastName,
        cardNumber,
        is_expiry=False,
        timeout=settings.TIMEOUT_MQTT_RESPONSE
):
    r = await get_person(sn_device=sn_device, id_person=id_person, timeout=10)
    if not r.get('answer'):
        return r

    exp = get_expiry_date(is_expiry)
    person_json = person_service.create_person_json(
        id=id_person,
        firstName=firstName,
        lastName=lastName,
        cardNumber=cardNumber,
        expiry=exp
    )
    command = person_service.CommandUpdatePerson(sn_device=sn_device)
    command.update_person(person_json)
    answer = await publish_command_and_wait_result(command, timeout=timeout)

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

    # Сохраняем шаблоны в память
    save_template_from_answer(answer)
    # Заносим ID персон в память
    save_person_ids_in_storage_from_answer(sn_device, answer)

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

    # Асинхронная обработка списка команд и сбор результатов
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
    all_person_ids = PersonStorage.get_person_ids(sn_device)

    if not all_person_ids:
        persons_result = await get_all_person(sn_device)
        if persons_result["has_error"]:
            # Не смогли получить людей(терминал не ответил -> прерываем выполнение)
            return persons_result

        all_person_ids = list(map(lambda user: int(user["id"]),
                                  persons_result["answer"]["operations"]["users"]))
        PersonStorage.add(sn_device, all_person_ids)

    person_for_create = []
    person_for_update = []
    errors = []

    for p in persons:
        if int(p["id"]) in all_person_ids:
            person_for_update.append(p)
        else:
            person_for_create.append(p)

    # 1. Отправка команды на создание всех людей <50 штук
    if person_for_create:
        person_create_result = await process_batch_create(sn_device, person_for_create, timeout=60)
        errors += person_create_result

    # 2. Запуск обновления людей по пачкам асинхронно
    if person_for_update:
        for i in range(0, len(person_for_update), batch_size):
            batch = person_for_update[i:i + batch_size]
            task = asyncio.create_task(process_batch_update(sn_device, batch, 3 * batch_size))
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


async def get_person(sn_device, id_person, timeout=settings.TIMEOUT_MQTT_RESPONSE):
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

    if not id:
        # ALL DELETE
        PersonStorage.clear(sn_device)
    else:
        # DELETE by ID
        person_photo_service.delete_template(id)
        PersonStorage.remove(sn_device, id)

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
    if action == ControlAction.UPLOAD_DIAGNOSTIC:
        command.upload_logs()

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


async def control_action_set_ntp_multi(
        payload, sn_devices: List[str],
        timeout=settings.TIMEOUT_MQTT_RESPONSE):
    result = {sn: None for sn in sn_devices}
    all_tasks = []
    task_sn_device: [asyncio.Task, str] = {}
    timeout_command = 5

    for sn_device in sn_devices:
        time_zone_task = asyncio.create_task(
            control_action_set_ntp(sn_device, payload, timeout=timeout), )
        task_sn_device[time_zone_task] = sn_device
        all_tasks.append(time_zone_task)

    if all_tasks:
        done_tasks, _ = await asyncio.wait(all_tasks, timeout=timeout_command * 2)
        for done_task in done_tasks:
            sn_device = task_sn_device[done_task]
            task_result = done_task.result()
            result[sn_device] = task_result["answer"]["operations"][
                                    "executeStatus"] == 1 if task_result.get(
                'answer') else None

    return result


async def update_config(sn_device, payload, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandUpdateConfig(sn_device=sn_device)
    command.update_config(payload)
    answer = await publish_command_and_wait_result(command, timeout=timeout)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def update_config_multi(payload, sn_devices: List[str],
        timeout=settings.TIMEOUT_MQTT_RESPONSE):
    result = {sn: None for sn in sn_devices}
    all_tasks = []
    task_sn_device: [asyncio.Task, str] = {}
    timeout_command = 5

    for sn_device in sn_devices:
        config_task = asyncio.create_task(update_config(sn_device, payload, timeout=timeout), )
        task_sn_device[config_task] = sn_device
        all_tasks.append(config_task)

    if all_tasks:
        done_tasks, _ = await asyncio.wait(all_tasks, timeout=timeout_command * 2)
        for done_task in done_tasks:
            sn_device = task_sn_device[done_task]
            task_result = done_task.result()
            result[sn_device] = task_result["answer"]["operations"] if task_result.get(
                'answer') else None

    return result


async def check_face(photo_base64, sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandCheckFace(sn_device=sn_device)
    command.check_face(photo_base64)
    answer = await publish_command_and_wait_result(command, timeout)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def get_total_person(sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE):
    command = CommandGetTotalPerson(sn_device=sn_device)
    command.get_total()
    answer = await publish_command_and_wait_result(command, timeout)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }


async def get_total_person_device(sn_device, timeout=settings.TIMEOUT_MQTT_RESPONSE) -> int:
    result = await get_total_person(sn_device=sn_device, timeout=timeout)
    if result.get('answer'):
        users = result['answer']['operations']['users']
        total = users[0]['total'] if users else 0
        return total
    return -1


async def get_total_person_all_devices(all_sn_devices):
    total_persons: Dict[str, int] = {}
    all_tasks = []
    task_sn_device: [asyncio.Task, str] = {}
    timeout_command = 5

    for sn_device in all_sn_devices:
        total_persons[sn_device] = -1  # Значение по умолчанию (Не смогли получить)

        total_task = asyncio.create_task(get_total_person(sn_device, timeout=timeout_command), )
        task_sn_device[total_task] = sn_device
        all_tasks.append(total_task)

    if all_tasks:
        done_tasks, pending_tasks = await asyncio.wait(all_tasks, timeout=timeout_command * 2)

        for done_task in done_tasks:
            result = done_task.result()
            sn_device = task_sn_device[done_task]
            if result.get('answer'):
                users = result['answer']['operations']['users']
                total = users[0]['total'] if users else 0
                total_persons[sn_device] = total

    return total_persons


async def access_log(sn_device, startStamp, endStamp, keyword):
    command = CommandGetAccessLog(sn_device=sn_device, )
    command.find(
        startStamp,
        endStamp,
        keyword
    )
    answer = await publish_command_and_wait_result(command, timeout=10)

    return {
        "answer": answer,
        "command": command.payload,
        "has_error": is_answer_has_error(command, answer)
    }
