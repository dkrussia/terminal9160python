from services.rmq import RMQChannel


class Devices:
    devices = set()

    @classmethod
    def add_device(cls, sn_device):
        # Lock?
        if sn_device not in cls.devices:
            cls.devices.add(sn_device)
            # cls.bind_rmq_broadcast(sn_device=sn_device)

    @classmethod
    def bind_rmq_broadcast(cls, sn_device):
        with RMQChannel() as channel:
            channel.queue.declare(queue='commands_' + sn_device)
            channel.exchange.declare(exchange='broadcast')
            channel.queue.bind(exchange='broadcast', queue='commands_' + sn_device)

    def get_all_devices(self):
        return self.devices


device_service = Devices()
