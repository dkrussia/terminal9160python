from datetime import datetime

from services.mci import subscribe_device_mci_command


class Devices:
    devices = set()
    devices_meta = {}

    @classmethod
    def add_device(cls, sn_device):
        if sn_device not in cls.devices:
            cls.devices.add(sn_device)
            subscribe_device_mci_command(sn_device)

    @classmethod
    def add_meta_on_login(cls):
        pass

    @classmethod
    def add_meta_update_conf(cls, sn_device, payload):
        if payload:
            d = cls.devices_meta.get(sn_device, {})
            d["config"] = payload
            d["config_update_time"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            cls.devices_meta[sn_device] = d

    @classmethod
    def add_meta_on_state(cls, payload):
        sn_device = payload["sn"]
        d = cls.devices_meta.get(sn_device, {})
        d["state"] = payload
        d["state_update_time"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        cls.devices_meta[sn_device] = d

    def get_all_devices(self):
        return self.devices


device_service = Devices()
