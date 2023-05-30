import random
from typing import Optional, Literal

from faker import Faker
from pydantic import BaseModel, Field

from config import TEST_SN_DEVICE
from services.device_command import ControlAction

fake = Faker()


# id: int = random.randint(55555, 66666)
# firstName: str = fake.name().split(' ')[0]
# lastName: str = fake.name().split(' ')[1]
# snDevice: str = TEST_SN_DEVICE
# TODO: создавать значения по умолчанию на лету?
class PersonCreate(BaseModel):
    id: int = random.randint(55555, 66666)
    firstName: str = fake.name().split(' ')[0]
    lastName: str = fake.name().split(' ')[1]


class DeviceControl(BaseModel):
    action: ControlAction


class UpdateConfig(BaseModel):
    adminPassword: str = None
    brightness: Optional[int] = Field(ge=1, le=100)
    deviceVolume: Optional[int] = Field(ge=0, le=100)
    # featureThreshold
    living: Literal[1, 0] = None
    # recogizeInterval
    # minSize
    temperature: Literal[1, 0] = None
    playVoice: bool = None
    lowPower: bool = None
    # idleTime

    # Access
    # mode: 0: face / card / QR
    # code, 1: face + card
    passMethod: Literal[1, 0] = None
    # openDuration
    alarmEnabled: bool = None
    # alarmDuration
    cardNumDecimal: bool = None
    cardNumReverse: bool = None
