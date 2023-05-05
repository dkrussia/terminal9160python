import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client("my_client")
client.username_pw_set('admin', 'admin123')
client.connect("192.168.1.130", 8086, 60)
client.loop_start()

create_person_payload = {
    "type": 3,
    "id": 7778,
    "devSn": "YGKJ202107TR08EL0007",
    "feedbackUrl": "http://192.168.1.130:8080",
    "operations":
        [
            {
                "createBy": "",
                "createTime": 1602843134000,
                "deptId": 104,
                "id": 10,
                "sex": 0,
                "status": 0,
                "updateBy": "",
                "userCode": "003",
                "userName": "John",
                "firstName": "Sergey",
                "lastName": "Kuznetsov",
                "userPhone": "15575681394",
                "cardNum": "ABCD",
                "wiegandNum": "100",
                "company": "1",
                "department": "1",
                "group": "1",
                "remark": "1",
                "expiry": ""
            }
        ]

}

update_person_payload = {
    "type": 4,
    "id": 11,
    "devSn": "YGKJ202107TR08EL0007",
    "feedbackUrl": "",
    "operations":
        [
            {
                "createBy": "",
                "deptId": 104,
                "id": 10,
                "sex": 0,
                "status": 0,
                "updateBy": "",
                "userCode": "003",
                "userName": "John",
                "firstName": "John",
                "lastName": "John",
                "userPhone": "15575681394",
                "cardNum": "ABCD",
                "wiegandNum": "100",
                "company": "",
                "department": "",
                "group": "",
                "remark": "",
                "expiry": ""
            }
        ]

}

query_person_payload = {
    "type": 1000,
    "id": 1,
    "devSn": "YGKJ202107TR08EL0007",
    "feedbackUrl": "",
    "operations": {
        "emp_id": "003",
        "keyword": "",
        "need_feature": False,
        "need_photo": False,
        "page_num": 1,
        "page_idx": 0
    }
}

delete_person_payload = {
    "devSn": "YGKJ202107TR08EL0007",
    "id": 1,
    "operations":
        [{
            "id": 10,
            "params": {}
        }],
    "type": 5
}

# client.publish("/_dispatch/command/YGKJ202107TR08EL0007", json.dumps(create_person_payload))
# time.sleep(1)
client.publish("/_dispatch/command/YGKJ202107TR08EL0007", json.dumps(query_person_payload))
time.sleep(1)
client.publish("/_dispatch/command/YGKJ202107TR08EL0007", json.dumps(update_person_payload))
time.sleep(1)

# client.publish("/_dispatch/command/YGKJ202107TR08EL0007", json.dumps(query_person_payload))
# time.sleep(1)
#
# client.publish("/_dispatch/command/YGKJ202107TR08EL0007", json.dumps(delete_person_payload))
# time.sleep(1)
# client.loop_stop()

