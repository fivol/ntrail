import pathlib
import typing
from contextlib import suppress
from datetime import datetime
import numpy as np
import csv
import os

from server.helpers.utils import absolute_path

_map_file_name = '../data/id-date.csv'


class UserRegistrationDate:
    """
    See user.registration
    """
    _ids: np.ndarray
    _dates: list

    @classmethod
    def date(cls, user_id) -> typing.Optional[datetime]:
        i = np.searchsorted(cls._ids, user_id)
        if i >= len(cls._dates):
            # TODO
            return datetime.now()
        if i < 0:
            return None
        return cls._dates[i]

    @classmethod
    def _read_map_file(cls):
        filename = absolute_path(__file__, _map_file_name)
        ids = []
        dates = []
        with open(filename, newline='') as f:
            reader = csv.reader(f)
            for id_, date in reader:
                if id_ == 'id':
                    continue
                ids.append(int(id_))
                dates.append(datetime.fromisoformat(date))

        cls._ids = np.array(ids)
        cls._dates = dates
        print()


with suppress(Exception):
    UserRegistrationDate._read_map_file()
