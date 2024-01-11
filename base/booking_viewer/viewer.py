from datetime import datetime
from os import path
from typing import List

from fastapi import APIRouter
from sqlalchemy import create_engine, Column, Integer, String, DateTime, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pydantic import BaseModel, ConfigDict, TypeAdapter

from config import BASE_DIR, s as settings

SQLALCHEMY_DATABASE_URL = path.join(BASE_DIR, 'assets', 'sql_app.db')
engine = create_engine(f'sqlite:///{SQLALCHEMY_DATABASE_URL}',
                       connect_args={"check_same_thread": False})
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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


BookingHistory.__table__.create(engine, checkfirst=True)


class BookingHistorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    internal_id: int
    devUserId: int
    head: str
    devSn: str
    devName: str
    firstName: str
    lastName: str
    passageTime: datetime


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
    with Session() as session:
        session.add(b)
        session.commit()


BookingHistoryList = TypeAdapter(List[BookingHistorySchema])


@device_booking_viewer.get('/')
async def get_booking_history(
        sn_device: str,
        date_start: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        date_end: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        stranger: bool = False,
) -> List[BookingHistorySchema]:
    with Session() as session:
        query = session.query(BookingHistory).filter(
            and_(BookingHistory.passageTime.between(date_start, date_end),
                 BookingHistory.devSn == sn_device)
        )
        if not stranger:
            query = query.filter(BookingHistory.devUserId != -1)
        r = query.all()
        return BookingHistoryList.validate_python(r)
