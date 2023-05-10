import base64
import os

from main import PHOTO_DIR


class PersonPhoto:

    @staticmethod
    def base64_to_file(person_id: int, photo_base64: str):
        decoded_data = base64.b64decode(photo_base64)
        with open(f"{PHOTO_DIR}/{person_id}.jpg", "wb") as fh:
            fh.write(decoded_data)

    @staticmethod
    def remove_photo(person_id: int, ):
        try:
            os.remove(f"{PHOTO_DIR}/{person_id}.jpg")
        except FileNotFoundError:
            pass
