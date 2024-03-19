from datetime import datetime
from os import path
from typing import List, Union

from fastapi import APIRouter
from sqlalchemy import select, Column, Integer, String, DateTime, and_
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from pydantic import BaseModel, ConfigDict, TypeAdapter, computed_field

from base import mqtt_api
from config import BASE_DIR, s as settings

SQLALCHEMY_DATABASE_URL = path.join(BASE_DIR, 'assets', 'sql_app.db')
engine = create_async_engine(f'sqlite+aiosqlite:///{SQLALCHEMY_DATABASE_URL}',
                             connect_args={"check_same_thread": False})

ASession = async_sessionmaker(autocommit=False,
                              autoflush=False, bind=engine,
                              class_=AsyncSession,
                              expire_on_commit=False
                              )
Base = declarative_base()

device_booking_viewer = APIRouter(prefix='/api/devices/booking/view')


class BookingHistory(Base):
    __tablename__ = "booking_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    internal_id = Column(Integer, )
    devUserId = Column(Integer, )
    head = Column(String, )
    devSn = Column(String, )
    devName = Column(String, )
    firstName = Column(String, )
    lastName = Column(String, )
    passageTime = Column(DateTime, )


async def init_db_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all,)


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


class BookingHistorySchema(BookingHistorySchemaBase):
    internal_id: int
    head: str


class BookingHistorySchemaDev(BookingHistorySchemaBase):
    id: int


async def add_booking_report(booking):
    if booking["devUserId"] < 0 and not settings.BOOKING_HISTORY_STRANGER:
        return
    b = BookingHistory(
        internal_id=booking.get("id"),
        head=booking.get("head", ""),
        devSn=booking["devSn"],
        devUserId=booking["devUserId"],
        devName=booking["devName"],
        firstName=booking["firstName"],
        lastName=booking["lastName"],
        passageTime=datetime.strptime(
            booking['passageTime'], '%Y-%m-%d %H:%M:%S'
        )
    )
    async with ASession() as session:
        async with session.begin():
            session.add(b)
        await session.commit()


BookingHistoryListDB = TypeAdapter(List[BookingHistorySchema])
BookingHistoryListDEVICE = TypeAdapter(List[BookingHistorySchemaDev])


async def fetch_booking_history(session, sn_device, date_start, date_end, stranger):
    query = select(BookingHistory).where(
        and_(
            BookingHistory.passageTime.between(date_start, date_end),
            BookingHistory.devSn == sn_device
        )
    ).order_by(BookingHistory.passageTime.desc())

    if not stranger:
        query = query.where(BookingHistory.devUserId != -1)

    result = await session.execute(query)
    return result.scalars().all()


@device_booking_viewer.get('/')
async def get_booking_history(
        sn_device: str,
        date_start: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        date_end: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        stranger: bool = False,
        from_db: bool = False
) -> Union[List[BookingHistorySchema], List[BookingHistorySchemaDev]]:
    if from_db:
        async with ASession() as session:
            async with session.begin():
                bookings = await fetch_booking_history(session,
                                                       sn_device,
                                                       date_start,
                                                       date_end,
                                                       stranger)
                return BookingHistoryListDB.validate_python(bookings, )

    r = await mqtt_api.access_log(sn_device,
                                  startStamp=int(date_start.timestamp()),
                                  endStamp=int(date_end.timestamp()),
                                  keyword="")
    result_list = r['answer']['operations'].get('result', []) if r['answer'] else []
    return BookingHistoryListDEVICE.validate_python(result_list)


@device_booking_viewer.get('/head')
async def get_head_if_exist(id: int, devUserId: int, passageTime: datetime, devSn: str):
    async with ASession() as session:
        async with session.begin():
            query = select(BookingHistory).filter(
                and_(
                    BookingHistory.internal_id == id,
                    BookingHistory.passageTime == passageTime,
                    BookingHistory.devSn == devSn,
                    BookingHistory.devUserId == devUserId,
                )
            )
            try:
                record = await session.execute(query)
                record = record.scalars().one()
                return {'head': record.head}
            except NoResultFound:
                return {'head': None}
