from dataclasses import dataclass
from datetime import datetime
from typing import List
import aioodbc
from fastapi import APIRouter
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, ConfigDict, TypeAdapter, computed_field

import config
from base import mqtt_api
from base.bookings.booking import get_booking_photo_head
from config import s as settings


Base = declarative_base()
device_booking_viewer = APIRouter(prefix='/api/devices/booking/view')


class BookingHistorySchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    devUserId: int
    devSn: str
    devName: str
    firstName: str
    lastName: str
    passageTime: datetime

    @computed_field
    @property
    def matrix_head(self) -> str:
        return f'{settings.PHOTO_URL}/{self.devUserId}.jpg'

    @computed_field
    @property
    def device_head(self) -> str:
        return (f"{config.s.PHOTO_PASS}/pass_photo/"
                f"{get_booking_photo_head(self.devSn, self.devUserId, self.passageTime, )}")


class BookingHistorySchema(BookingHistorySchemaBase):
    internal_id: int
    head: str


class BookingHistorySchemaDev(BookingHistorySchemaBase):
    id: int


BookingHistoryListDEVICE = TypeAdapter(List[BookingHistorySchemaDev])


@dataclass
class MatrixBooking:
    passageTime: datetime


async def fetch_booking_from_matrix(sn_device, date_start, date_end):
    SQL_QUERY_BOOKING_DEVICE = """
    SELECT terminalInfo.shortname,DATEADD(second,DATE_TIME_UTC/1000,'1970-01-01 00:00:00') as passageTime
    FROM matrix.matrix.BAS_BOOKING_VIEW b
    inner join matrix.TM_DEVICE_INFO terminalInfo ON b.terminalNumber = terminalInfo.number_
    where bookingTerminalEventTypeLang='en'
    and terminalInfo.shortname='{device_sn}'
    and DATEADD(second,DATE_TIME_UTC/1000,'1970-01-01 00:00:00') >= '{date_start} 00:00:00' 
    and DATEADD(second,DATE_TIME_UTC/1000,'1970-01-01 00:00:00') <= '{date_end} 23:59:59' 
    order by DATE_TIME_UTC desc
    """

    connection_string = (
        "DRIVER=ODBC Driver 17 for SQL Server;"
        f"SERVER={settings.MATRIX_SQL_HOST},{settings.MATRIX_SQL_PORT};"
        "DATABASE=matrix;"
        f"UID={settings.MATRIX_SQL_LOGIN};PWD={settings.MATRIX_SQL_PASSWORD}"
    )
    cnxn = await aioodbc.connect(dsn=connection_string, )
    crsr = await cnxn.cursor()
    await crsr.execute(
        SQL_QUERY_BOOKING_DEVICE.format(
            device_sn=sn_device,
            date_start=date_start.strftime('%Y-%m-%d'),
            date_end=date_end.strftime('%Y-%m-%d'))
    )
    rows = await crsr.fetchall()
    await cnxn.close()
    bookings = [MatrixBooking(passageTime=r[1]) for r in rows]
    return bookings


async def get_booking_history_device(sn_device, date_start, date_end):
    r = await mqtt_api.access_log(sn_device,
                                  startStamp=int(date_start.timestamp()),
                                  endStamp=int(date_end.timestamp()),
                                  keyword="")
    result_list = r['answer']['operations'].get('result', []) if r['answer'] else []
    return BookingHistoryListDEVICE.validate_python(result_list)


@device_booking_viewer.get('/')
async def get_booking_history(
        sn_device: str,
        date_start: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        date_end: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
):
    device = await get_booking_history_device(sn_device, date_start, date_end)
    matrix = await fetch_booking_from_matrix(sn_device, date_start, date_end)

    return {
        "device": device,
        "matrix": list(map(lambda x: x.passageTime, matrix))
    }
