import logging

from server.helpers.tied_value import TiedValue
import numpy as np

from core.helpers.utils import bool_filter, get_random_color
from core.constants import PlotType

logger = logging.getLogger('represent')


class RepresentTools:

    default_props = [
        ('mean', 'Средний'),
        ('max', 'Максимальный'),
        ('min', 'Минимальный'),
        ('median', 'Медианный'),
        ('count', 'Указали')
    ]

    def gen_prop(self, id_, name_, value_, ids=None):
        value_dict = {}
        if isinstance(value_, TiedValue):
            value_, ids = value_.get_value(), value_.get_ids(self.get_id_prefix())

        try:
            value_ = float(value_)
        except:
            pass

        if isinstance(value_, float):
            value_dict['value'] = round(value_, 2)
            value_dict['type'] = 'num'
        elif isinstance(value_, str):
            value_dict['value'] = value_
            value_dict['type'] = 'str'
        else:
            logger.warning('Unknown property value type %s %s', type(value_), value_)
            return None

        if ids and len(ids) > 1:
            value_dict['percent'] = round(len(ids) / self.size * 100, 2)

        if not value_ or (isinstance(value_, float) and np.isnan(value_)):
            return None
        return {
            'id': id_,
            'name': name_.capitalize(),
            'value': value_dict,
            'ids': ids
        }

    def gen_circular_plot(self, items, name=None, color=None):
        if color is None:
            color = lambda x: get_random_color()
        if name is None:
            name = lambda value: value.get_value()
        return [
            {
                'value': count,
                'ids': value.get_ids(self.get_id_prefix()),
                'name': name(value),
                'color': color(value)
            }
            for value, count in items if count > 0
        ]

    def gen_line_plot(self, items, name=None):
        data_dict = self.data_dict()
        return [
            {
                'ids': item.get_ids(self.get_id_prefix()),
                'value': round(item.get_value(), 2),
                'name': self.__class__.base_class(data_dict[item.get_ids()[0]]).name
            }
            for item in items]

    def gen_plot(self, type_, data_list, key, name=None):
        data = self.process_data()
        if not type_:
            return None

        if not data_list:
            if type_ == PlotType.CIRCULAR:
                data_list = self.gen_circular_plot(data[key]['source_list'], name=name)
            elif type_ == PlotType.LINE:
                data_list = self.gen_line_plot(data[key]['source_list'])
            else:
                return None

        if len(data_list) < 2:
            return None
        return {
            'type': type_,
            'data': data_list
        }

    def gen_property_category(self, key, name, props,
                              plot_type=None, plot_data=None, common_count=0, name_func=None, names_dict=None):
        if names_dict:
            name_func = lambda x: names_dict.get(x, 'Идентификатор не найден')

        data = self.process_data()
        if data[key].get('count', 1) == 0:
            return None
        base_id = f'{self.hash}.{key}'
        sup_properties = []

        if common_count:
            source_list = data[key]['source_list']
            for idx in range(common_count):
                if len(source_list) > idx:
                    sub_prop_name = source_list[idx][0].value
                    if name_func:
                        sub_prop_name = name_func(sub_prop_name)
                    sup_properties.append(self.gen_prop(f'top_{idx}', sub_prop_name, source_list[idx][1],
                                                   source_list[idx][0].get_ids(self.get_id_prefix())))
        added_sub_keys = set()
        props += self.__class__.default_props
        for sub_property in props:
            sub_key = sub_property[0]
            if sub_key in data[key] and sub_key not in added_sub_keys:
                added_sub_keys.add(sub_key)
                sub_name = sub_property[1]
                sub_value = data[key][sub_key]
                sup_properties.append(self.gen_prop(sub_key, sub_name, sub_value))


        values = bool_filter(sup_properties)
        if not values:
            return None
        return {
            'id': base_id,
            'name': name,
            'plot': self.gen_plot(plot_type, plot_data, key, name=name_func),
            'values': values
        }
