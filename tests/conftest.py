import pytest


@pytest.fixture()
def base64_photo():
    with open('base64photo.txt', 'r') as f:
        return f.read()
