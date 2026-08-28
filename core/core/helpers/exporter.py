import csv
import io
import json
from abc import abstractmethod


class FormatWriter:
    def __init__(self, filename):
        self._filename = filename

    @abstractmethod
    def save(self, data):
        pass

    def _write(self, text: str):
        with open(self._filename, 'w') as f:
            f.write(text)


class CsvWriter(FormatWriter):
    def save(self, data):
        if not isinstance(data, list):
            raise TypeError(f'CSV can represent only list data, have {type(data)}')
        output = io.StringIO()
        writer = csv.DictWriter(output, dicts_keys(data))
        writer.writeheader()
        writer.writerows(data)
        text = output.getvalue()
        self._write(text)


class JsonWriter(FormatWriter):
    def save(self, data):
        self._write(json.dumps(data))


class DataExporter:
    def __init__(self, data):
        self._data = data

    @classmethod
    def _make_dict_plain(cls, item):
        """
        {1: {2: 3}} -> {"1.2": 3}
        """
        if not isinstance(item, dict):
            return item
        result = {}
        for key, value in item.items():
            if not value:
                continue
            if isinstance(value, dict):
                sub_dict = cls._make_dict_plain(value)
                result.update({key + k: v for k, v in sub_dict.items()})
            elif isinstance(value, list):
                if not isinstance(value[0], dict):
                    result[key] = value
                    continue
                list_begin = value[:3]
                list_remain = value[3:]
                if list_remain:
                    result[f'{key}-remain'] = list_remain
                if list_begin:
                    for i, dct in enumerate(list_begin):
                        sub_dict = cls._make_dict_plain(dct)
                        result.update({f'{key}-{i}-{k}': v for k, v in sub_dict.items()})
            else:
                result[key] = value
        return result

    @abstractmethod
    def write(self, writer: FormatWriter):
        pass


class DictExporter(DataExporter):
    def write(self, writer: FormatWriter):
        writer.save(self._data)


class ListExporter(DataExporter):
    def write(self, writer: FormatWriter):
        dicts = [self._make_dict_plain(d) for d in self._data]
        writer.save(dicts)
