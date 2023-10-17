person_storage = {}


# 1. Сервер включился -> хранилище пустое
# 2. Если в хранилище нет записей -> запросить с терминала
# 3. Если записи есть -> добавить\удалить
# 4. Если пришла команда deleteAll -> очистить

class PersonStorage:

    @staticmethod
    def clear(sn_device):
        try:
            del person_storage[sn_device]
        except KeyError:
            pass

    @staticmethod
    def add(sn_device, ids: list):
        if not person_storage.get(sn_device):
            person_storage[sn_device] = set()
        person_storage[sn_device].update(ids)

    @staticmethod
    def remove(sn_device, id):
        if not person_storage.get(sn_device):
            try:
                person_storage[sn_device].remove(id)
            except KeyError:
                pass

    @classmethod
    def get_person_ids(cls, sn_device) -> list:
        if not person_storage.get(sn_device):
            return []
        return list(person_storage.get(sn_device))

    @classmethod
    def get_all(cls):
        return person_storage
