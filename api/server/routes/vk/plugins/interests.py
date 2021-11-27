from collections import Counter
import nltk

from core import VKUser
from server.helpers.utils import absolute_path
from server.plugin.plugin import BasePlugin
from server.routes.vk.features.tf_idf import IDFCalculator
from server.routes.vk.plugins.tokenizer import Morphology
from worker.ctx import get_context


interests_filename = '../data/interests.txt'


class UserInterestsPlugin(BasePlugin):
    name = 'user-interests'

    # Соотетствие названия интереса списку тегов, его характеризующих
    _interests_map: list[tuple[str, set[str]]] = None

    def __init__(self, user: VKUser, **kwargs):
        super().__init__(**kwargs)
        self._user = user

    @classmethod
    def _text_from_group_dict(cls, group: dict):
        name = group['name']
        desc = group.get('description', '')
        return f'{name} {desc}'

    @classmethod
    def _group_desc_tokens(cls, group: dict) -> set:
        text = cls._text_from_group_dict(group)
        return set(Morphology.tokenize(text.lower()))

    @classmethod
    def _prepare_dict_line(cls, line) -> tuple[str, set]:
        items = line.split(',')
        name = items[0]
        tokens = set(Morphology.tokenize(line))
        return name, tokens

    @classmethod
    def _read_data(cls):
        with open(absolute_path(__file__, interests_filename)) as f:
            text = f.read().lower()
        cls._interests_map = [
            cls._prepare_dict_line(line.strip())
            for line in text.split('\n') if line.strip()
        ]

    @classmethod
    def _compare_token_sets(cls, items: Counter, template: set):
        return sum(items.get(item, 0) for item in template)

    @classmethod
    def _groups_tokens(cls, groups_data: list) -> Counter:
        return sum([
            Counter(cls._group_desc_tokens(group))
            for group in groups_data
        ], start=Counter())

    @classmethod
    def _extract_topics(cls, tokens: Counter) -> Counter:
        priority = Counter()
        for topic, topic_template in cls._interests_map:
            priority[topic] = cls._compare_token_sets(tokens, topic_template)

        return priority

    async def relevant(self):
        top = await self.response()
        if not top:
            return top
        best = top[0][1]
        return [
            (name, count)
            for name, count in top
            if count > best / 3 and count > 1
        ]

    async def groups(self):
        """TF-IDF
        http://nlpx.net/archives/57
        """
        groups = await self._user.groups()
        data = await groups.data()
        names = [group.get('name') for group in data]
        return IDFCalculator.calculate(names)

    async def response(self) -> list:
        groups = await self._user.groups()
        data = await groups.data()
        tokens = self._groups_tokens(data)
        topics = self._extract_topics(tokens)
        best_topics = topics.most_common(10)
        return [
            (name.capitalize(), value)
            for name, value in best_topics
        ]


ctx = get_context()
nltk.download('punkt')
UserInterestsPlugin._read_data()  # noqa
