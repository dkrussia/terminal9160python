from starlette.testclient import TestClient
from config import TEST_ID_PERSON, TEST_SN_DEVICE
from main import app


def test_100_request_mqtt():
    with TestClient(app) as client:
        for _ in range(0, 100):
            client.get(f"/person")


def test_crud_on_device():
    with TestClient(app) as client:
        # Удаляем если "застрял" на каком то этапе
        client.delete(f"/person/{TEST_ID_PERSON}")

        response = client.get(f"/person/{TEST_ID_PERSON}")
        body = response.json()
        assert body["answer"]["operations"]["executeStatus"] == 2

        response = client.get(f"/person")
        body = response.json()
        assert body["answer"]["operations"]["executeStatus"] == 1
        count_users = len(body["answer"]["operations"]["users"])

        person = {
            "id": TEST_ID_PERSON,
            "firstName": "Mark",
            "lastName": "Mcgee",
        }
        response = client.post(f"/person/create", params=person, data={"photo": ""})
        body = response.json()
        assert body["answer"]["operations"]["executeStatus"] == 1

        response = client.get(f"/person")
        body = response.json()
        assert body["answer"]["operations"]["executeStatus"] == 1
        assert count_users + 1 == len(body["answer"]["operations"]["users"])

        response = client.get(f"/person/{TEST_ID_PERSON}", )
        body = response.json()
        assert body["answer"]["operations"]["executeStatus"] == 1

        response = client.delete(f"/person/{TEST_ID_PERSON}", )
        body = response.json()

        assert body["answer"]["operations"]["executeStatus"] == 1
