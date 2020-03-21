from ntmodule.many_objects import ManyObjects
from ntmodule.selective_query_exeptions import QueryDataException
from ntmodule.tools import merge_lists

# Этот класс отвечает за отображение модуля на интерфейс NTrail.
# Если модуль нужнается в визуальном отображении, нужну унаследовать этот класс и переопределить некоторые методы
# при необходимости. Но без этого тоже будет работать, просто запрос вернет пустой json нужного формата


def try_base_analog(func):
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        print('func_name', func_name)
        base_class = self.__class__.base_class
        if base_class and func_name in base_class.available_attributes and self.size == 1:
            obj = base_class(self.data_list()[0])
            return getattr(obj, func_name)(*args, **kwargs)

        return func(self, *args, **kwargs)

    return wrapper


class Represent(ManyObjects):

    def get_sub_properties_categories(self):
        categories = {
            'school': {'min_percent': 10, 'importance': 7},
            'sex': {'min_percent': 50, 'importance': 3},
            'city': {'min_percent': 30, 'importance': 4},
            'country': {'min_percent': 70, 'importance': 2},
            'occupation_university': {'min_percent': 20, 'importance': 7},
            'university': {'min_percent': 20, 'importance': 6},
        }
        return categories

    def sub_prop_importance_metrics(self, prop):
        name = prop['name']
        prop_id = prop['id']
        category = prop_id.split('.')[1]
        prop_name = prop_id.split('.')[2]
        value_dict = prop['value']
        value = value_dict['value']
        value_type = value_dict['type']
        percent = value_dict.get('percent', 0)
        metric = 0
        categories = self.get_sub_properties_categories()

        if category in categories:
            prop_data = categories[category]
            if 'min_percent' in prop_data:
                min_percent = prop_data['min_percent']

                if percent >= min_percent:
                    metric = (percent - min_percent) / min_percent
            elif 'min_count' in prop_data:
                min_count = prop_data['min_count']

                if value >= min_count:
                    metric = (value - min_count) / min_count

            if prop_name != 'count':
                metric *= prop_data['importance']
            else:
                metric /= 10

            return metric

        return metric

    def get_template_actions(self, split=False):
        actions = []
        if split and self.size > 1:
            actions.append(
                {
                    'id': 'split',
                    'name': 'Разбить на подкластеры',
                    'target': 'cluster',
                    'value': 'clusters',
                },
            )
        return actions

    def get_interesting_properties(self):
        all_props = self.get_all_properties()

        # processed_data = self.process_data()

        base_id = self.hash
        return sorted(merge_lists([

            [
                {
                    'id': f"{prop['id']}.{sub_prop['id']}",
                    'name': f"{prop['name']} {sub_prop['name']}",
                    'value': sub_prop['value'],
                    'ids': sub_prop['ids']
                }
                for sub_prop in prop['values']
            ]
            for prop in all_props
        ]), key=lambda prop: self.sub_prop_importance_metrics(prop), reverse=True)

    def get_important_properties(self):
        if not self.valid:
            return []
        return []

    def get_all_properties(self):
        return []

    def get_description(self):
        return ''

    def get_properties(self):
        return {
            'all': self.get_all_properties(),
            'interesting': self.get_interesting_properties(),
            'important': self.get_important_properties(),
            'description': self.get_description()
        }

    def get_params(self, parent=None):
        return {}

    def get_id(self):
        raise NotImplementedError()

    def get_connections(self):
        return {}

    def get_output_connections(self):
        base_class = self.__class__.base_class
        return {
            base_class.gen_id(first_id): [base_class.gen_id(id_) for id_ in connected_list]
            for (first_id, connected_list) in
            self.get_connections().items()
        }

    def get_items(self):
        return [user.get_entity() for user in self.objects]

    def get_entities(self):

        return {
            'connections': self.get_output_connections(),
            'items': self.get_items()
        }

    def get_actions(self):
        return []

    def main_cluster_data(self, parent=None):
        return {
            'properties': self.get_properties(),
            'params': self.get_params(parent),
            'entities': self.get_entities(),
            'id': self.hash,
            'actions': self.get_actions()
        }

    def represent(self, force=False):
        if not self.valid:
            raise QueryDataException('такого объекта не существует')

        if not self.size:
            return {
                'warning': {
                    'text': 'Запрашиваемый кластер не содержит 0 объектов'
                }
            }

        self.preload(force=force)
        return {
            'clusters': {
                'items': [
                    self.main_cluster_data()
                ],
                'mainID': self.hash
            }
        }
