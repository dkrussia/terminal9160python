from starlette.testclient import TestClient
from services import devices as devices_service
from main import app


def test_register_devices():
    with TestClient(app) as client:
        response = client.post("/api/devices/login", json={"devSn": "XYZ"})
        assert response.status_code == 200
        assert "XYZ" in devices_service.Devices.devices
