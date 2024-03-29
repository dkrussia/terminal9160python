"""
Модуль хранит данные об устройствах в памяти
"""
import json
from datetime import datetime
from typing import Literal

from base.rmq_client import rabbit_mq
from config import DEVICE_JSON_DATA_FILE


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
    devices_function_arrive = []

    # TODO: Хранить списки ids person которые присутствуют на
    #  Терминале, что бы не делать person is_exist

    def __new__(cls):
        d = cls.read_from_json()
        cls.devices_meta = d.get('meta', {})
        cls.devices_observed = d.get('observed', [])
        cls.devices_function_arrive = d.get('function_arrive', [])
        return object.__new__(cls)

    @property
    def all_sn_list(self):
        return list(self.devices_meta.keys())

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
            'observed': list(cls.devices_observed),
            'function_arrive': list(cls.devices_function_arrive)
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
    async def add_device(cls, payload):
        sn_device = payload["sn"]
        cls.add_meta_on_state(payload)

        if sn_device not in cls.devices:
            cls.devices.add(sn_device)
            await rabbit_mq.start_queue_listener(f'commands_{sn_device}')

    @classmethod
    def add_ip_address(cls, sn_device, ip):
        d = cls.devices_meta.get(sn_device, {})
        d["ip"] = ip
        cls.devices_meta[sn_device] = d
        cls.write_to_json()

    @classmethod
    def add_meta_on_login(cls):
        pass

    @classmethod
    def set_meta_config(cls, sn_device, payload):
        if payload:
            d = cls.devices_meta.get(sn_device, {})
            d["config"] = payload
            d["config_update_time"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            cls.devices_meta[sn_device] = d

    @classmethod
    def save_config(cls, sn_device, payload):
        cls.set_meta_config(sn_device, payload)
        cls.write_to_json()

    @classmethod
    def save_config_multi(cls, payloads: dict):
        # payload {sn_devices: conf | None}
        for sn_device, conf in payloads.items():
            if conf:
                cls.set_meta_config(sn_device, conf)
        cls.write_to_json()

    @classmethod
    def add_meta_on_state(cls, payload):
        sn_device = payload["sn"]
        d = cls.devices_meta.get(sn_device, {})
        d["state"] = payload
        d["state_update_time"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        cls.devices_meta[sn_device] = d
        cls.write_to_json()

    def get_all_devices(self):
        return self.devices

    @classmethod
    def is_access_mode(cls, sn_device):
        if not cls.devices_meta[sn_device].get("config"):
            return False
        return cls.devices_meta[sn_device]["config"]["attendance"] is False

    @classmethod
    def set_function(cls, sn_device, function: Literal["arrive", "depart"]):
        if not cls.is_access_mode(sn_device):
            return

        if function == "arrive":
            cls.devices_function_arrive.append(sn_device)

        if function == "depart":
            try:
                cls.devices_function_arrive.remove(sn_device)
            except ValueError:
                pass

        cls.devices_function_arrive = list(set(cls.devices_function_arrive))

        cls.write_to_json()


device_service = Devices()
