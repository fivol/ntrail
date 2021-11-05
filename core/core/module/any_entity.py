import datetime
import hashlib
import os
import typing
from pathlib import Path
from abc import abstractmethod, ABCMeta

from core.helpers.exporter import JsonWriter, CsvWriter, DictExporter, ListExporter
from core.helpers.utils import *
from worker.parsers.exceptions import ParserRealError


class AnyEntity(metaclass=ABCMeta):

    @property
    @abstractmethod
    def hash(self):
        """
        Each media must have own unique string hash
        """
        str_id = str(self.__hash__()).encode('UTF-8')
        obj_id = hashlib.sha1(str_id).hexdigest()[-16:]
        return obj_id

    @abstractmethod
    def data(self) -> typing.Union[list, dict, None]:
        """
        Data structure about object, list or dict
        """
        pass

    def export(self, filename: str = '', format_: str = 'json',):
        data = self.data()

        writers = {
            'json': JsonWriter,
            'csv': CsvWriter
        }

        if filename:
            format_ = file_extension(filename) or format_

        if not filename or Path(filename).is_dir():
            file = f'{self.__class__.__name__.lower()}-{datetime.datetime.now().isoformat()}.{format_}'
            filename = os.path.join(filename, file)

        from core.module.many_entities import ManyEntities
        from core.module.single_entity import SingleEntity

        if isinstance(self, ManyEntities):
            exporter = ListExporter
        elif isinstance(self, SingleEntity):
            exporter = DictExporter
        else:
            raise NotImplementedError

        exporter(data=data).write(writers[format_](filename=filename))

    def preload(self):
        self.data()

    def __hash__(self):
        """
        All objects must implement hash method
        """
        return hash(self.hash)

