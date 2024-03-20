import json
from datetime import datetime

from base.bookings.booking import add_booking
from base.bookings.viewer import get_booking_history, add_booking_report
from base.log import get_logger

logger = get_logger('sync_booking')


def find_missing_bookings(db_bookings, device_bookings):
    # Определяем отсутствующие bookings
    db_passage_times = [booking.passageTime
                        for booking in db_bookings]
    missing_bookings = [
        booking for booking in device_bookings
        if booking.passageTime not in db_passage_times
    ]
    return missing_bookings


async def get_booking_from_db_on_date(sn_device, date: datetime, ):
    date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = date.replace(hour=23, minute=59, second=59, microsecond=0)
    logger.info(f'Get booking from db {date_start} {date_end}')
    result = await get_booking_history(
        sn_device=sn_device,
        date_start=date_start,
        date_end=date_end,
        stranger=False,
        from_db=True)
    logger.info(f'Got {len(result)}')
    return result


async def get_booking_from_device_on_date(sn_device, date: datetime.date, ):
    date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = date.replace(hour=23, minute=59, second=59, microsecond=0)
    logger.info(f'Get booking from device {date_start} {date_end}')
    result = await get_booking_history(
        sn_device=sn_device,
        date_start=date_start,
        date_end=date_end,
        stranger=False,
        from_db=False)
    result = list(filter(lambda b: b.devUserId != -1, result))
    logger.info(f'Got {len(result)}')
    return result


async def sync_booking_on_device(sn_device: str, date: datetime, ):
    db_booking = await get_booking_from_db_on_date(sn_device, date)
    device_bookings = await get_booking_from_device_on_date(sn_device, date)
    missing_bookings = find_missing_bookings(db_booking, device_bookings)

    count = 0
    logger.info(f'Missing bookings: {len(missing_bookings)}')

    for b in missing_bookings:
        try:
            b_json = b.dict()
            b_json["passageTime"] = b.passageTime.strftime('%Y-%m-%d %H:%M:%S')
            await add_booking(b_json)
            await add_booking_report(b_json)
            count += 1
            logger.info(f'\tSuccess : {b}')
        except Exception as e:
            logger.error(f'\tFail : {b}. {str(e)}')

    return {
        "missing": len(missing_bookings),
        "success": count,
        "fail": len(missing_bookings) - count
    }


async def sync_booking_all_devices(sn_devices: list, date: datetime):
    results = {}
    for sn_device in sn_devices:
        logger.info(f'Sync booking for {sn_device}. {date}')
        r = await sync_booking_on_device(sn_device, date)
        results[sn_device] = r
    return results
