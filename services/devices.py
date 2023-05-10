class Devices:
    devices = []

    @classmethod
    def add_device(cls, sn_device):
        # Lock?
        if sn_device not in cls.devices:
            cls.devices.append(sn_device)
            cls.bind_rmq_broadcast(sn_device=sn_device)

    @classmethod
    def bind_rmq_broadcast(cls, sn_device):
        #
        pass

