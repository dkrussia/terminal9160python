from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from base import mqtt_api
from base.rmq_client import rmq_send_reply_to

from config import MAX_WORKERS_MCI_COMMAND


def command_thread_handler(type_command, sn_device, payload, reply_to):
    """
    Типы команд
    1. user_update_biophoto -
    2. user_update -
    3. multiuser_update_biophoto +
    4. multiuser_update -
    5. user_delete +
    """
    t1 = datetime.now()
    result = None

    if type_command == 'user_update_biophoto':
        photo = payload.get('picture', "")
        if photo:
            result = mqtt_api.create_or_update(
                sn_device=sn_device,
                id_person=int(payload["id"]),
                firstName=payload["firstName"],
                lastName=payload["lastName"],
                photo=photo,
            )

    if type_command == 'multiuser_update_biophoto':
        for user in payload:
            photo = user.get('picture', "")
            if photo:
                # TODO: Сделать Сумму результатов + ID персон которые с ошибкой.
                #  commands = [create_command, *update_commands]

                result = mqtt_api.create_or_update(
                    sn_device=sn_device,
                    id_person=int(user["id"]),
                    firstName=user["firstName"],
                    lastName=user["lastName"],
                    photo=photo,
                )

    if type_command == 'user_delete':
        result = mqtt_api.delete_person(sn_device=sn_device, id=int(payload["id"]))

    error_result = {"result": 'Error', 'Return': "-1"}
    success_result = {"result": 'Successful', 'Return': "0"}

    if not result:
        rmq_send_reply_to(
            reply_to=reply_to,
            data=error_result
        )
    elif result["has_error"]:
        rmq_send_reply_to(
            reply_to=reply_to,
            data=error_result
        )
    else:
        rmq_send_reply_to(
            reply_to=reply_to,
            data=success_result
        )

    t2 = datetime.now()
    print(f'Total: {type_command}-{(t2 - t1).total_seconds()}')

    # type_command == 'user_update' or
    # type_command == 'multiuser_update' or
    # if type_command == 'user_update_biophoto':
    # if type_command == 'multiuser_update_biophoto':


executor = ThreadPoolExecutor(max_workers=MAX_WORKERS_MCI_COMMAND)


def callback_on_get_mci_command(message):
    type_command = message.properties['headers'].get('command_type')
    reply_to = message.properties.get('reply_to')
    payload = message.json()
    sn_device = message.method["routing_key"].split("_")[-1]

    executor.submit(command_thread_handler,
                    type_command=type_command,
                    sn_device=sn_device,
                    payload=payload,
                    reply_to=reply_to)

    # TODO: Добавить подтверждение о принятии сообщения
    # channel.basic_ack(delivery_tag=method.delivery_tag)
