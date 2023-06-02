import pytest
from pytest_rabbitmq import factories

rabbitmq_proc = factories.rabbitmq_proc(port=5674, node="test2")
rabbitmq = factories.rabbitmq("rabbitmq_proc")



@pytest.fixture()
def base64_photo():
    with open('base64photo.txt', 'r') as f:
        return f.read()
