import asyncio
import base64
import json
import os

from base.mqtt_api import check_face, update_config
from base.mqtt_client import mqtt_consumer
from config import s as settings, BASE_DIR
from base.log import logger


async def make_report(SN_DEVICE: str, featureThresholds: list, ORIGIN_FT=85):
    FINISH_RESULT = []
    REPORT_FILE = os.path.join(BASE_DIR, 'assets', 'report.json')
    try:
        os.remove(REPORT_FILE)
    except FileNotFoundError:
        pass
    asyncio.create_task(mqtt_consumer(state=False))

    logger.info(f'Start recognize report on featureThresholds = {featureThresholds}')
    for ft in featureThresholds:
        logger.info(f'Set featureThresholds to {ft}')
        await update_config(SN_DEVICE, {"featureThreshold": ft})

        result = {
            'NOT_RECOGNIZED': [],
            'WRONG_RECOGNIZED': []
        }

        for img in os.listdir(settings.PHOTO_DIR):
            person_id = img.split('.')[0]

            try:
                person_id = int(person_id)
            except ValueError:
                logger.error(f'Can not to int person id {person_id}')
                continue

            with open(os.path.join(settings.PHOTO_DIR, img), "rb") as image_file:
                img_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            resp = await check_face(img_base64, SN_DEVICE, )
            answer = resp['answer']

            if not answer:
                logger.warning(f'Can not get person for {img}')
                continue
            if answer["operations"]["executeStatus"] == 2:
                result["NOT_RECOGNIZED"].append(person_id)
            if (answer["operations"]["executeStatus"] == 1
                    and not answer["operations"]["result"]["id"] == person_id):
                result["WRONG_RECOGNIZED"].append(person_id)

        FINISH_RESULT.append({"featureThreshold": ft, "result": result})

    with open(REPORT_FILE, 'w') as f:
        json.dump(FINISH_RESULT, f)

    await update_config(SN_DEVICE, {"featureThreshold": ORIGIN_FT})
