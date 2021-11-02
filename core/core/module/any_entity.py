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
    def name(self):
        """
        Human readable name of object
        """
        pass

    @property
    @abstractmethod
    def hash(self):
        """
        Each media must have own unique string hash
        """
        str_id = str(self.__hash__()).encode('UTF-8')
        obj_id = hashlib.sha1(str_id).hexdigest()[-16:]
        set_obj(obj_id, self)
        return obj_id

    @abstractmethod
    def summary(self) -> dict:
        """
        Little summery about object, most important info
        """
        pass

    @abstractmethod
    def data(self, force=False, full=True) -> typing.Union[list, dict, None, ParserRealError]:
        """
        Data structure about object, list or dict
        """
        pass

    def export(self, filename: str = '', format_: str = 'json',):
        data = self.data(full=True)

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

    def preload(self, force=False):
        self.data(force=force)

    def __hash__(self):
        """
        All objects must implement hash method
        """
        return hash(self.hash)

