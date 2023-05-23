import random
from faker import Faker
from pydantic import BaseModel

from config import TEST_SN_DEVICE

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
    snDevice: str = TEST_SN_DEVICE
