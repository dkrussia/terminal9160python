import asyncio
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import config
from config import BASE_DIR
from base.log import get_logger
from base.rmq_client import rabbit_mq
from services.devices_storage import device_service
import base64

logger_booking = get_logger('booking')
logger_fail_booking = get_logger('booking_fail')
fail_booking_file = os.path.join(BASE_DIR, 'assets', 'fail_booking.json')


class BookingAddException(Exception):
    pass


def get_booking_photo_head(sn_device, id_user, passDateTime, ):
    # file name
    f = os.path.join(
        sn_device,
        passDateTime.strftime("%Y-%m-%d"),
        f'{id_user}-{passDateTime.strftime("%Y-%m-%dT%H-%M-%S")}.jpg'
    )
    return f


def save_head_booking(sn_device: str, id_user: str, passDateTime: datetime, head: str):
    directory = os.path.join(config.BASE_DIR, 'assets', 'pass_photo', )
    f_name = get_booking_photo_head(sn_device, id_user, passDateTime, )
    full_path = os.path.join(directory, f_name)

    d = Path(full_path)
    d.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, "wb") as photo:
        decoded_data = base64.b64decode(head)
        photo.write(decoded_data)


async def add_booking_to_rmq(payload: dict, logger=logger_booking):
    log_uuid = str(uuid.uuid4())

    sn_device = payload["devSn"]
    id_user = payload["devUserId"]
    atType = payload.get('atType', 0)
    passDateTime = datetime.strptime(
        payload['passageTime'], '%Y-%m-%d %H:%M:%S'
    )
    passDateTimeString = passDateTime.strftime('%Y-%m-%dT%H:%M:%S')
    head = payload.get('head')

    if head:
        try:
            save_head_booking(
                sn_device,
                id_user,
                passDateTime,
                head)
        except Exception:
            logger.error(f"Pass photo not save {sn_device} {passDateTimeString}")

    if id_user < 1:
        return

    # TO RMQ
    if device_service.is_access_mode(sn_device):
        atType = 3
        if sn_device in device_service.devices_function_arrive:
            atType = 2

    max_attempt = 3
    attempt = 1
    sleep_between_attempt = 2

    while attempt <= max_attempt:
        try:
            await rabbit_mq.publish_message(
                q_name=f'events_{sn_device}',
                message=json.dumps({
                    'sn': f'events_{sn_device}',
                    'time': passDateTimeString,
                    'status': str(atType),
                    "pin": str(id_user),
                })
            )
            logger.info(f'Booking {sn_device} {passDateTimeString} {atType} {id_user}')
            return 200
        except Exception as e:
            logger.error(
                f'{log_uuid} Booking append error {sn_device} {passDateTimeString} {atType} {id_user}'
                f'ATTEMPT#{attempt} of {max_attempt}. Error: {e}'
            )
        attempt += 1
        await asyncio.sleep(sleep_between_attempt)

    logger.error(
        f'{log_uuid} Booking was not added {sn_device} {passDateTimeString} {atType} {id_user}')

    raise BookingAddException
