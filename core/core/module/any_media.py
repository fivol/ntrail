import datetime
import hashlib
import io
import json
import csv
import typing
from pprint import pprint
from abc import abstractmethod

from core.helpers.exporter import JsonWriter, CsvWriter, DictExporter, ListExporter
from core.helpers.utils import *


class AnyMedia:
    @abstractmethod
    def params(self):
        """
        Dict of object parameters
        All interesting properties in folding-dict form
        """
        pass

    @property
    def name(self):
        """
        Human readable name of object
        """
        raise NotImplementedError

    def summery(self):
        """
        Little summery about object, most important info
        """
        pass

    def export(self, format_: str = 'json', filename: str = None):
        data = self.data(full=True)

        writers = {
            'json': JsonWriter,
            'csv': CsvWriter
        }

        if filename:
            format_ = format_ or file_extension(filename)
        else:
            filename = f'{self.__class__.__name__.lower()}-{datetime.datetime.now().isoformat()}.{format_}'

        from core.module.many_media import ManyMedia
        from core.module.single_media import SingleMedia

        if isinstance(self, ManyMedia):
            exporter = ListExporter
        elif isinstance(self, SingleMedia):
            exporter = DictExporter
        else:
            raise NotImplementedError

        exporter(data=data).write(writers[format_](filename=filename))

    def print_params(self):
        pprint(self.params, compact=True)

    def print(self):
        pprint(self.data(), compact=True)

    @once_property
    def hash(self):
        str_id = str(self.__hash__()).encode('UTF-8')
        obj_id = hashlib.sha1(str_id).hexdigest()[-16:]
        set_obj(obj_id, self)
        return obj_id

    @abstractmethod
    def data(self, force=False, full=True) -> typing.Union[list, dict, None]:
        """
        Data structure about object, list or dict
        """
        pass

    def preload(self, force=False):
        self.data(force=force)

    @abstractmethod
    def __hash__(self):
        """
        All objects must implement hash method
        """
        pass
