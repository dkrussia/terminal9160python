from services import person as person_service
from mqtt_client import MQTTClientWrapper

# Получить персону
# command = person_service.CommandGetPerson(sn_device=sn_device)
# command.search_person(1000)
# mqtt_publish_command(sn_device=sn_device, payload=command.result_json())
#

# Добавить персону
#
# command = person_service.CommandCreatePerson(sn_device=sn_device)
# person_json = person_service.create_person_json(
#     1000,
#     firstName="Sergey",
#     lastName="Kuznetsov",
#     face_str=base64_photo
# )
# command.add_person(person_json)
# mqtt_publish_command(sn_device=sn_device, payload=command.result_json())


# Обновить персону
# command = person_service.CommandUpdatePerson(sn_device=sn_device)
# person_json = person_service.create_person_json(
#     1000,
#     firstName="Sergey",
#     lastName="Kuznetsov",
#     face_str=base64_photo
# )
# command.update_person(person_json)
# mqtt_publish_command(sn_device=sn_device, payload=command.result_json())
#

# Удалить персону
# command = person_service.CommandDeletePerson(sn_device=sn_device)
# command.delete_person(1000)
# mqtt_publish_command(sn_device=sn_device, payload=command.result_json())
