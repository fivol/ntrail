from ntmodule.one_object import OneObject
from ntmodule.selective_query_exeptions import QueryDataException, QueryProgrammingException


class OneObjectRepresent(OneObject):
    def represent(self, force=False):
        print('OneObjectRepresent')
        many_objects_class = self.__class__.many_objects_class
        if many_objects_class:
            return many_objects_class([self.id]).represent()
        else:
            raise QueryProgrammingException(
                'Невозможно отобразить данный тип объекта (не определен атрибут many_objects_class)')
