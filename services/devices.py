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
    def add_meta(cls):

        pass

    def get_all_devices(self):
        return self.devices


device_service = Devices()
