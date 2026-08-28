from server.plugin.plugin import BasePlugin


class VKGroupsPlugin(BasePlugin):
    name = 'groups'
    namespace = 'vk'

    def result(self):
        user = self.get_plugin_result('user')
        return user.groups()

    def response(self) -> dict:
        return self.result().summary()

    def params(self):
        logger.debug('@ get groups params')
        params = {}
        groups_list = self.full_data
        params['size'] = self.size
        params['age_limits'] = get_field_values(groups_list, 'age_limits', counter=True)
        params['name'] = get_field_values(groups_list, 'name')
        params['city'] = get_field_values(groups_list, 'city', key='title', counter=True)
        params['country'] = get_field_values(groups_list, 'country', key='title', counter=True)
        params['has_photo'] = get_field_values(groups_list, 'has_photo')
        params['main_section'] = get_field_values(groups_list, 'main_section', counter=True, clean=True)
        params['place'] = get_field_values(groups_list, 'title', counter=True)
        params['verified'] = get_field_values(groups_list, 'verified', clean=True, counter=True)
        params['members_count'] = get_field_values(groups_list, 'members_count')
        params['trending'] = get_field_values(groups_list, 'trending')
        params['wall'] = get_field_values(groups_list, 'wall')
        links = get_field_values(groups_list, 'links')
        params['links_names'] = get_field_values(links, 'name', clean=True)
        params['links_urls'] = get_field_values(links, 'url', clean=True)
        # params['contacts'] = Counter(list_from_dicts(
        #     sum(get_field_values(groups_list, 'contacts'), []), 'user_id')).most_common()
        params['description'] = get_field_values(groups_list, 'description', clean=True)
        params['site'] = get_field_values(groups_list, 'site', clean=True)
        params['start_date'] = get_field_values(groups_list, 'start_date', clean=True)
        params['deactivated'] = get_field_values(groups_list, 'deactivated', counter=True)
        # counters = get_field_values(groups_list, 'counters')
        # for counter_item in ['albums', 'articles', 'docs', 'photos', 'topics', 'videos']:
        #     params['counters_' + counter_item] = get_field_values(counters, counter_item, clean=True)

        type_groups = self.select_type('group')
        type_pages = self.select_type('page')
        type_event = self.select_type('event')

        params['type_groups_count'] = type_groups.size
        params['type_pages_count'] = type_pages.size
        params['type_events_count'] = type_event.size
        params['type'] = get_field_values(groups_list, 'type', counter=True)

        params['pages_activity'] = get_field_values(type_pages.full_data, 'activity', counter=True)
        params['groups_activity'] = get_field_values(type_groups.full_data, 'activity', counter=True)

        return params

    def process_data(self):
        params = self.params
        data = {
            'size': self.size
        }
        list_size_limit = 20
        ## Need work with links
        ## Добавить обработку сайтов - количество валидных, конкретные адреса, закономерности по именам доменов
        ## Подумать на полем counters. Сейчас оно вообще не считается (не приходит тк не использую execute)
        data['age_limits'] = {
            # 'count': params['age_limits'].size,
            'source_list': params['age_limits'].most_common()
        }
        data['city'] = {
            # 'count': params['city'].size,
            'source_list': params['city'].most_common()
        }
        data['country'] = {
            # 'count': params['country'].size,
            'source_list': params['country'].most_common()
        }
        # data['has_photo'] = {
        #     'count': params['has_photo']
        # }
        data['main_section'] = {
            'source_list': params['main_section'].most_common()
        }
        data['verified'] = {
            'count': params['verified'].size
        }
        members_count = sorted(params['members_count'])
        data['members_count'] = {
            **prepare_list(members_count),
            'source_list': members_count
        }
        # data['trending'] = {
        #     'count': params['trending'].size
        # }
        # data['wall'] = {
        #     'all_count': len(params['wall']),
        #     'common_categories': counter_top(params['wall'])
        # }
        # data['contacts'] = {
        #     'all_count': len(params['contacts']),
        #     'common_list': counter_top(params['contacts'])
        # }
        # data['description'] = {
        #     'len_median': np.median([len(item) for item in params['description']]),
        #     'len_mean': np.mean([len(item) for item in params['description']]),
        #     'source_list': get_common_texts_terms(params['description']).most_common(list_size_limit)
        # }
        data['name'] = {
            'source_list': get_common_texts_terms(params['name']).most_common(list_size_limit)
        }
        data['site'] = {
            'count': len(params['site'])
        }
        data['start_date'] = prepare_list(params['start_date'])
        data['deactivated'] = {
            'count': params['deactivated'].size,
            'source_list': params['deactivated'].most_common()
        }
        data['type'] = {
            'groups_count': params['type_groups_count'],
            'pages_count': params['type_pages_count'],
            'events_count': params['type_events_count']
        }
        data['activity_pages'] = {
            # 'count': params['pages_activity'].size,
            'source_list': params['pages_activity'].most_common(ignore_single=True)
        }
        data['activity_groups'] = {
            'source_list': params['groups_activity'].most_common()
        }
        data['type'] = {
            'source_list': params['type'].most_common()
        }

        return data

    def get_features(self):
        if hasattr(self, 'features_dict'):
            return self.features_dict
        data = self.process_data()
        assert isinstance(data, dict)
        features = self.get_common_features(
            data,
            category_frequency_features={
                'activity.pages.common_categories',
                'activity.groups.common_categories',
                'deactivated.common_categories',
                'wall.common_categories',
                'main_section.common_categories',
                'age_limits.common_categories',
            }, plain_features={
                'description.len_median',
                'description.len_mean'
            }, frequency_features={
                'activity.pages.all_count',
                'type.groups_count',
                'type.pages_count',
                'type.events_count'
            }
        )
        self.features_dict = features
        return features

    def get_all_properties(self):
        return bool_filter([
            self.gen_property_category('age_limits', 'Возрастные ограничения', [], PlotType.CIRCULAR,
                                       common_count=3, name_func=lambda x: age_limits_dict[x]),
            self.gen_property_category('city', 'Город', [], PlotType.CIRCULAR, common_count=3),
            self.gen_property_category('name', 'Имя содержит', [], PlotType.CIRCULAR, common_count=10),
            self.gen_property_category('country', 'Страна', [], PlotType.CIRCULAR, common_count=3),
            self.gen_property_category('members_count', 'Количество подписчиков', [], PlotType.LINE),
            self.gen_property_category('activity_pages', 'Тема публичной страницы', [], PlotType.CIRCULAR, common_count=6),
            self.gen_property_category('activity_groups', 'Тип группы', [], PlotType.CIRCULAR, common_count=3),
            self.gen_property_category('type', 'Тип', [], PlotType.CIRCULAR, common_count=5, names_dict=groups_types_dict),
            # self.gen_property_category('description', 'Описание', [], PlotType.CIRCULAR, common_count=10),
            self.gen_property_category('verified', 'Верификация', [('count', 'Верифициовано')]),
        ])

    def get_name(self):
        source_list = self.process_data()['name']['source_list'] or []

        def name_from_words_list(items):
            return ', '.join(map(lambda x: x[0].get_value().capitalize(), items))

        if len(source_list) and len(source_list[0]) and source_list[0][1] <= 1:
            activity_pages = self.process_data()['activity_pages']['source_list']
            if activity_pages:
                return self.process_data()['activity_pages']['source_list'][0][0].get_value().capitalize()

        if len(source_list) >= 3:
            if source_list[2][1] > 2:
                return name_from_words_list(source_list[:3])
            elif source_list[1][1] > 2:
                return name_from_words_list(source_list[:2])
            else:
                return name_from_words_list(source_list[:1])

        return name_from_words_list(source_list[:1])
