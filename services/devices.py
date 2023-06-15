"""
Модуль хранит данные об устройствах
"""
import json
from datetime import datetime

from base import mqtt_api
from base.rmq_client import rmq_subscribe_on_mci_command
from config import DEVICE_JSON_DATA_FILE
from services.mci import callback_on_get_mci_command


class Devices:
    """
    devices_meta
    {
        sn_device: {
            config: {},
            config_update_time: datetime,
            state: {},
            state_update_time: datetime,
            ip_address: 0.0.0.0
        }
    }
    """

    devices = set()
    devices_meta = {}
    devices_observed = []

    def __new__(cls):
        d = cls.read_from_json()
        cls.devices_meta = d.get('meta', {})
        cls.devices_observed = d.get('observed', [])
        return object.__new__(cls)

    @classmethod
    def add_device_to_observed(cls, sn):
        if sn not in cls.devices_observed:
            cls.devices_observed.append(sn)
            cls.write_to_json()
        return cls.devices_observed

    @classmethod
    def remove_device_from_observed(cls, sn):
        if sn in cls.devices_observed:
            cls.devices_observed.remove(sn)
            cls.write_to_json()
        return cls.devices_observed

    @classmethod
    def write_to_json(cls):
        d = {
            'meta': cls.devices_meta,
            'observed': list(cls.devices_observed)
        }
        with open(DEVICE_JSON_DATA_FILE, 'w') as f:
            json.dump(d, f)

    @classmethod
    def read_from_json(cls):
        try:
            with open(DEVICE_JSON_DATA_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @classmethod
    def add_device(cls, sn_device):
        if sn_device not in cls.devices:
            cls.devices.add(sn_device)
            rmq_subscribe_on_mci_command(sn_device, callback_on_get_mci_command)

    @classmethod
    def add_ip_address(cls, sn_device, ip):
        d = cls.devices_meta.get(sn_device, {})
        d["ip"] = ip
        cls.devices_meta[sn_device] = d

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
