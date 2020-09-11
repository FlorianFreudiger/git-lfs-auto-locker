from __future__ import annotations

from datetime import date
from typing import List


class LfsLock:
    def __init__(self, lock_id: int, path: str, owner: str, locked_at: date):
        self.lock_id = lock_id
        self.path = path
        self.owner = owner
        self.locked_at = locked_at

    @staticmethod
    def from_dict(lock_dict: dict) -> LfsLock:
        return LfsLock(int(lock_dict['id']),
                       lock_dict['path'],
                       lock_dict['owner']['name'],
                       lock_dict['locked_at'])

    @staticmethod
    def lock_list_to_path_list(lock_list: List[LfsLock]):
        path_list = []
        for lock in lock_list:
            path_list.append(lock.path)
        return path_list
