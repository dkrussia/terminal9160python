"""Синхронизуемся по всем устройствам"""
import asyncio
import datetime
from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

from base.bookings.sync import sync_booking_all_devices
from base.mqtt_client import mqtt_consumer
from services.devices_storage import device_service

set_event_loop_policy(WindowsSelectorEventLoopPolicy())

devices = device_service.all_sn_list
date = datetime.datetime.now() - datetime.timedelta(days=1)

print(date)
print(devices)


async def main():
    asyncio.create_task(mqtt_consumer())
    await sync_booking_all_devices(devices, date, from_matrix=True)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
