@echo off
if not exist ".env.local" (
    echo SERVER_HOST = localhost >> ".env.local"
    echo SERVER_PORT = 8888 >> ".env.local"
    echo. >> ".env.local"
    echo RMQ_HOST = localhost >> ".env.local"
    echo RMQ_PORT = 5672 >> ".env.local"
    echo RMQ_USER = guest >> ".env.local"
    echo RMQ_PASSWORD = guest >> ".env.local"
    echo. >> ".env.local"
    echo MQTT_HOST = localhost >> ".env.local"
    echo MQTT_PORT = 1883 >> ".env.local"
    echo MQTT_USER = admin >> ".env.local"
    echo MQTT_USER = public >> ".env.local"
    echo. >> ".env.local"
    echo MQTT_PORT_FOR_TERMINAL = 1883 >> ".env.local"
    echo HOST_FOR_TERMINAL = localhost >> ".env.local"
    echo PORT_FOR_TERMINAL = 8888 >> ".env.local"
    echo. >> ".env.local"
    echo FIRMWARE_FILE = HR-FaceAC-L01.04.13-DM08.tar.gz >> ".env.local"
    echo. >> ".env.local"
    echo TIMEOUT_MQTT_RESPONSE = 10 >> ".env.local"
    echo BATCH_UPDATE_SIZE = 10 >> ".env.local"

    echo MCI_PHOTO_MANAGER = False >> ".env.local"
)

notepad .env.local