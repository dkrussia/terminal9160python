import base64


class PersonPhoto:
    @staticmethod
    def base64_to_file(person_id: int, photo_base64: str):
        decoded_data = base64.b64decode(photo_base64)
        with open(f"../photo/{person_id}.jpg", "wb") as fh:
            fh.write(decoded_data)
