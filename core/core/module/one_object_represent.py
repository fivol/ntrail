from core.module.single_entity import SingleEntity
from core.module.selective_query_exeptions import QueryProgrammingException


class OneObjectRepresent(SingleEntity):
    def represent(self, force=False):
        many_objects_class = self.__class__._many_media_cls
        if many_objects_class:
            return many_objects_class([self.id]).represent()
        else:
            raise QueryProgrammingException(
                'Невозможно отобразить данный тип объекта (не определен атрибут many_objects_class)')
