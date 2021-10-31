from core.module.single_media import SingleMedia
from core.module.selective_query_exeptions import QueryProgrammingException


class OneObjectRepresent(SingleMedia):
    def represent(self, force=False):
        many_objects_class = self.__class__.many_objects_class
        if many_objects_class:
            return many_objects_class([self.id]).represent()
        else:
            raise QueryProgrammingException(
                'Невозможно отобразить данный тип объекта (не определен атрибут many_objects_class)')
