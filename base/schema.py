import random
from typing import Optional, Literal

from faker import Faker
from pydantic import BaseModel, Field

from services.device_command import ControlAction

fake = Faker()


class PersonCreate(BaseModel):
    id: int = random.randint(55555, 66666)
    firstName: str = fake.name().split(' ')[0]
    lastName: str = fake.name().split(' ')[1]
    cardNumber: int = None


class DeviceControl(BaseModel):
    action: ControlAction


class NtpTime(BaseModel):
    timeServer: str = ""
    timeZone: str = ""
    ntp: bool = False
    time: str = ""


class UpdateConfig(BaseModel):
    adminPassword: str = None

    company: str = None
    deviceName: str = None
    devicePos: str = None

    miniWnd: Literal[0, 1, 3] = None

    brightness: Optional[int] = Field(ge=1, le=100, default=None)
    deviceVolume: Optional[int] = Field(ge=0, le=100, default=None)
    featureThreshold: int = None
    living: Literal[1, 0] = None
    maskDetection: Literal[1, 0] = None

    doorBellEnable: bool = None
    doorSensorEnable: bool = None

    gateTimeout: int = Field(ge=0, le=20, default=None)
    relayCtrlDuration: int = Field(ge=0, le=20, default=None)
    relayDelayDuration: int = Field(ge=0, le=20, default=None)

    recogizeInterval: int = None
    minSize: int = None
    temperature: Literal[1, 0] = None
    playVoice: bool = None
    lowPower: bool = None
    idleTime: int = None
    businessTrip: list = None
    passMethod: Literal[1, 0] = None
    openDuration: int = None
    alarmEnabled: bool = None
    alarmDuration: int = None
    cardNumDecimal: bool = None
    cardNumReverse: bool = None
    wiegandFmt: Literal[26, 32, 34] = None
    recgSuccessText: str = None
    recgFailedText: str = None
    passScene: bool = None
    passHeadPhoto: bool = None
    recordStranger: bool = None
    fillLight: Literal[0, 1, 2] = None
    recordLimitTime: int = None
    recordLimitNumber: int = None
    attendance: bool = None
    attendanceBtn: bool = None
