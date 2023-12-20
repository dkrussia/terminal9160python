import asyncio
import json
import os
import uuid
from datetime import datetime
from config import BASE_DIR
from base.log import get_logger
from base.rmq_client import rabbit_mq
from services.devices_storage import device_service

logger_booking = get_logger('booking')
logger_fail_booking = get_logger('booking_fail')
fail_booking_file = os.path.join(BASE_DIR, 'assets', 'fail_booking.json')


class BookingAddException(Exception):
    pass


async def task_try_send_fail_bookings():
    while True:
        print('start task_try_send_fail_bookings')
        fail_bookings = []

        if os.path.exists(fail_booking_file):
            with open(fail_booking_file, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    fail_bookings = data

        print(f'fails bookings={len(data)} found')

        write_fail_bookings([])

        for fail_b in fail_bookings:
            try:
                await add_booking(payload=fail_b, logger=logger_fail_booking)
            except BookingAddException:
                pass
        print('end task_try_send_fail_bookings')

        await asyncio.sleep(60)


def write_fail_bookings(data):
    with open(fail_booking_file, 'w') as file:
        json.dump(data, file, indent=4)


def put_fail_booking_to_file(booking_payload):
    if os.path.exists(fail_booking_file):
        with open(fail_booking_file, 'r') as file:
            data = json.load(file)
            if isinstance(data, list):
                data.append(booking_payload)
            else:
                data = [booking_payload]
    else:
        data = [booking_payload]

    write_fail_bookings(data)


async def add_booking(payload: dict, logger=logger_booking):
    max_attempt = 3
    attempt = 1
    sleep_between_attempt = 3

    log_uuid = str(uuid.uuid4())

    sn_device = payload["devSn"]
    id_user = payload["devUserId"]
    atType = payload.get('atType', 0)
    passDateTime = datetime.strptime(
        payload['passageTime'], '%Y-%m-%d %H:%M:%S'
    ).strftime('%Y-%m-%dT%H:%M:%S')

    while attempt <= max_attempt:
        try:
            if device_service.is_access_mode(sn_device):
                atType = 3
                if sn_device in device_service.devices_function_arrive:
                    atType = 2
            if id_user > 0:
                await rabbit_mq.publish_message(
                    q_name=f'events_{sn_device}',
                    message=json.dumps({
                        'sn': f'events_{sn_device}',
                        'time': passDateTime,
                        'status': str(atType),
                        "pin": str(id_user),
                    })
                )

            logger.info(f'Booking {sn_device} {passDateTime} {atType} {id_user}')
            return {}

        except Exception as e:
            logger.error(
                f'{log_uuid} Booking append error {sn_device} {passDateTime} {atType} {id_user}'
                f'ATTEMPT#{attempt} of {max_attempt}. Error: {e}'
            )

        attempt += 1
        await asyncio.sleep(sleep_between_attempt)

    logger.error(f'{log_uuid} Booking was not added {sn_device} {passDateTime} {atType} {id_user}')

    put_fail_booking_to_file(payload)

    raise BookingAddException
