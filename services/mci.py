from datetime import datetime

from base import mqtt_api
from base.rmq_client import global_rmq_chanel, send_reply_to


def subscribe_device_mci_command(sn_device):
    queue = f'commands_{sn_device}'
    global_rmq_chanel.queue.declare(queue)
    global_rmq_chanel.basic.consume(handle_mci_command, queue)


def handle_mci_command(message):
    t1 = datetime.now()
    type_command = message.properties['headers'].get('command_type')
    reply_to = message.properties.get('reply_to')
    payload = message.json()
    sn_device = message.method["routing_key"].split("_")[-1]
    print(type_command, reply_to,)

    if type_command == 'user_update' or type_command == 'user_update_biophoto':
        photo = payload.get('picture', "")
        if photo:
            result = mqtt_api.create_or_update(
                sn_device=sn_device,
                id_person=int(payload["id"]),
                firstName=payload["firstName"],
                lastName=payload["lastName"],
                photo=photo,
            )

    if type_command == 'multiuser_update' or type_command == 'multiuser_update_biophoto':
        for user in payload:
            photo = user.get('picture', "")
            if photo:
                result = mqtt_api.create_or_update(
                    sn_device=sn_device,
                    id_person=int(user["id"]),
                    firstName=user["firstName"],
                    lastName=user["lastName"],
                    photo=photo,
                )

    if type_command == 'user_delete':
        result = mqtt_api.delete_person(int(payload["id"]))

    # if type_command == 'user_update_biophoto':
    #     pass
    #
    # if type_command == 'multiuser_update_biophoto':
    #     pass

    send_reply_to(
        reply_to=reply_to,
        data={"result": 'Successful', 'Return': "0"}
    )
    t2 = datetime.now()
    print(f'Total: {type_command}-{(t2 - t1).total_seconds()}')