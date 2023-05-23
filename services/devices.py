from services.mci import handle_mci_command
from services.rmq import rmq_channel


class Devices:
    devices = set()

    @classmethod
    def add_device(cls, sn_device):
        # Lock?
        if sn_device not in cls.devices:
            cls.devices.add(sn_device)
            with rmq_channel as channel:
                channel.consume_queue('commands_' + sn_device, handle_mci_command)

    def get_all_devices(self):
        return self.devices


device_service = Devices()
