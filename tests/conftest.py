import pytest
import amqpstorm
from pytest_rabbitmq import factories

rabbitmq_my = factories.rabbitmq('rabbitmq_my_proc')


@pytest.fixture
def amqp_connection(rabbitmq_amqpstorm):
    connection = rabbitmq_amqpstorm.get_connection()
    yield connection
    connection.close()


@pytest.fixture()
def base64_photo():
    with open('base64photo.txt', 'r') as f:
        return f.read()


@pytest.fixture
def amqp_connection():
    connection = rabbitmq_my.get_connection()
    yield connection
    connection.close()
