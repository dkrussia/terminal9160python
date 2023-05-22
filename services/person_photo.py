import base64
import os

from config import PHOTO_DIR, PHOTO_URL


class PersonPhoto:

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
        return f"{PHOTO_URL}/{person_id}.jpg"
