import os

from starlette.testclient import TestClient

from main import app, PHOTO_PATH, PHOTO_DIR
from services.person_photo import PersonPhoto


def test_save_file_from_base_base64(base64_photo):
    PersonPhoto.remove_photo(0)
    PersonPhoto.base64_to_file(0, base64_photo)
    assert os.path.exists(f"{PHOTO_DIR}/0.jpg") is True
    PersonPhoto.remove_photo(0)


def test_check_photo_url(base64_photo):
    PersonPhoto.base64_to_file(0, base64_photo)
    with TestClient(app) as client:
        print(client.base_url)
        response = client.get(f"{PHOTO_PATH}/0.jpg")
        assert response.status_code == 200
    PersonPhoto.remove_photo(0)
