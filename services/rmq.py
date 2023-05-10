import amqpstorm

RMQ_HOST = ""
RMQ_USER = ""
RMQ_PASSWORD = ""
RMQ_PORT = 0


class RMQChannel(object):
    def __init__(self):
        self.connection = amqpstorm.Connection(
            hostname=RMQ_HOST,
            username=RMQ_USER,
            password=RMQ_PASSWORD,
            port=RMQ_PORT,
        )

    def __enter__(self):
        return self.connection.channel()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()
