from services.device_command import CommandControlTerminal


def test_create_control_command():
    control_command = CommandControlTerminal(id_command=1, sn_device="XYZ")
    assert control_command.type == 9
    control_command.restart_system()

    assert control_command.payload["operations"] == {
        "devAction": 2,
        "id": "XYZ"
    }

    control_command.restart_software()

    assert control_command.payload["operations"] == {
        "devAction": 3,
        "id": "XYZ"
    }

    control_command.open_door()
    assert control_command.payload["operations"] == {
        "devAction": 4,
        "id": "XYZ"
    }

    control_command.update_software(firmware_url="http://firm.ru/update.bin")
    assert control_command.payload["operations"] == {
        "devAction": 5,
        "apkUrl": "http://firm.ru/update.bin",
        "id": "XYZ",
    }