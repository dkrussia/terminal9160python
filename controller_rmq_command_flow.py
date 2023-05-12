from services import person as person_service
from mqtt_client import mqtt_publish_command

# Получить сообщение из RMQ
with open('tests/base64photo.txt', 'r') as f:
    base64_photo = f.read()
sn_device = "YGKJ202107TR08EL0007"

command = person_service.CommandCreatePerson(sn_device=sn_device)
person_json = person_service.create_person_json(
    1000,
    firstName="Sergey",
    lastName="Kuznetsov",
    face_str=base64_photo
)
command.add_person(person_json)
mqtt_publish_command(sn_device=sn_device, payload=command.result_json())

