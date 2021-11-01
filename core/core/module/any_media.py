import hashlib
import io
import json
import csv
import typing
from pprint import pprint
from abc import abstractmethod
from core.utils import *


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

    def export(self, format: str = 'json', filename: str = None):
        data = self.data(full=True)

        if filename:
            guess_format = filename.split('.')[-1]
            if len(guess_format) < 5 and guess_format != filename:
                format = guess_format

        if format == 'json':
            file_content = json.dumps(data)
        elif format == 'csv':
            if not isinstance(data, list):
                raise TypeError(f'CSV can represent only list data, have {type(data)}')
            output = io.StringIO()
            writer = csv.DictWriter(output, dicts_keys(data))
            writer.writeheader()
            writer.writerows(data)
            file_content = output.getvalue()
        else:
            raise NotImplemented

        if filename:
            with open(filename, 'w') as f:
                f.write(file_content)

        return file_content

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
