import asyncio
import base64
import json
import os
from config import PHOTO_DIR, FACE_TEMPLATES_FILE
from config import s as settings


def json_keys_to_int(x):
    if isinstance(x, dict):
        return {int(k): v for k, v in x.items()}
    return x


class PersonPhoto:
    face_templates = {}

    @staticmethod
    def base64_to_file(person_id: int, photo_base64: str):
        decoded_data = base64.b64decode(photo_base64)
        with open(f"{PHOTO_DIR}/{person_id}.jpg", "wb") as fh:
            fh.write(decoded_data)
        return PersonPhoto.get_photo_url(person_id)

    @staticmethod
    def remove_photo(person_id: int, ):
        try:
            os.remove(f"{PHOTO_DIR}/{person_id}.jpg")
        except FileNotFoundError:
            pass

    @staticmethod
    def get_photo_url(person_id):
        return f"{settings.PHOTO_URL}/{person_id}.jpg"

    @classmethod
    def get_face_template(cls, person_id):
        return cls.face_templates.get(person_id, None)

    @classmethod
    def save_person_template(cls, person_id, face_template):
        print(
            f'SV: id={person_id} Start={face_template[:3]}...{face_template[-3:-1]}. Total: {len(cls.face_templates)}')
        cls.face_templates[person_id] = face_template

    @classmethod
    def save_person_template_if_not_exist(cls, person_id, face_template):
        if not cls.get_face_template(person_id):
            cls.save_person_template(person_id, face_template)

    @classmethod
    def delete_template(cls, person_id):
        try:
            del cls.face_templates[person_id]
        except KeyError:
            pass

    @classmethod
    async def save_templates_to_file(cls):
        while True:
            with open(FACE_TEMPLATES_FILE, 'w') as f:
                json.dump(cls.face_templates, f)
            await asyncio.sleep(2 * 60)

    @classmethod
    def load_faces(cls):
        try:
            with open(FACE_TEMPLATES_FILE, 'r') as f:
                cls.face_templates = json.load(f, object_hook=json_keys_to_int)
                print(f'Load pi cache {len(cls.face_templates)}')
        except FileNotFoundError as e:
            print(f'File pi cache not found {str(e)}')
