# С 1 Августа ПН-ПТ с 7.00-9.00/16.00-18.00
"""
events_$device.
`{sn: str, time: 2000-01-01: 21:00:00, status: str, pin: int, str}`
status:
IN: 2
OUT: 3
sn: номер устройства.
pin = id_person(Идентификатор человека)
"""
import asyncio
import json
import random

from datetime import datetime, timedelta, time

from base.rmq_client import rabbit_mq


async def seed_booking():
    await rabbit_mq.start()
    # ALL_SN_DEVICE = ['SNKDLSJD92']
    # ALL_PERSON_NUMBER = ['1', '2', '3']
    ALL_SN_DEVICE = []
    ALL_PERSON_NUMBER = []
    IN = 2
    OUT = 3

    start_date = datetime(2023, 8, 1)
    end_date = datetime(2023, 8, 3)
    current_date = start_date

    while current_date < end_date:
        # Проверяем, является ли текущий день субботой или воскресеньем
        if current_date.weekday() != 5 and current_date.weekday() != 6:
            # Генерируем случайное время для входа утром (7:00-9:00)
            morning_entry = datetime.combine(
                current_date.date(),
                time(random.randint(7, 8),
                     random.randint(0, 59)))

            # Генерируем случайное время для ухода вечером (16:00-18:00)
            evening_exit = datetime.combine(current_date.date(),
                                            time(random.randint(16, 17),
                                                 random.randint(0, 59)))

            for person_id in ALL_PERSON_NUMBER:
                sn_device = random.choice(ALL_SN_DEVICE)
                q_name = f'events_{sn_device}'
                morning_entry_str = morning_entry.strftime('%Y-%m-%dT%H:%M:%S')
                evening_exit_str = morning_entry.strftime('%Y-%m-%dT%H:%M:%S')
                print(f"Morning Entry: {sn_device}", morning_entry)
                print(f"Evening Exit: {sn_device}", evening_exit)

                await rabbit_mq.publish_message(
                    q_name=q_name,
                    message=json.dumps({
                        'sn': f'events_{sn_device}',
                        'time': morning_entry_str,
                        'status': str(IN),
                        "pin": str(person_id),
                    })
                )
                await rabbit_mq.publish_message(
                    q_name=q_name,
                    message=json.dumps({
                        'sn': f'events_{sn_device}',
                        'time': evening_exit_str,
                        'status': str(OUT),
                        "pin": str(person_id),
                    })
                )

        current_date += timedelta(days=1)  # Переходим к следующему дню


asyncio.run(seed_booking())
