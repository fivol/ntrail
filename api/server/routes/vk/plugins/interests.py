import re
from collections import Counter
from contextlib import suppress

import nltk
import pymorphy2

from core import VKUser
from server.helpers.utils import absolute_path
from server.plugin.plugin import BasePlugin


class Morphology:
    _denied_tags = ['PREP', 'PNCT', 'CONJ', 'NUMB', 'UNKN', 'PRCL', 'NPRO', 'ADVB']
    _denied_tags_reg = re.compile('|'.join(_denied_tags))
    _morph = pymorphy2.MorphAnalyzer(lang='ru')
    _stemmer = nltk.stem.snowball.RussianStemmer()

    """
    Stemmers:
    m = Mystem()
    # https://stackoverflow.com/questions/45696028/snowballstemmer-for-russian-words-list
    
    
    https://pymorphy2.readthedocs.io/en/stable/user/guide.html
    morph.parse(token)[0]
    """

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        """
        Split text to form independent tokens
        """
        tokens = []
        # m.lemmatize(text)
        for token in nltk.word_tokenize(text, language='russian'):
            if len(token) < 3:
                continue
            # tokens.append(stem)
            lexem = cls._morph.parse(token)[0]
            if cls._denied_tags_reg.search(str(lexem.tag)):
                continue
            tokens.append(cls._stemmer.stem(lexem.normal_form))

        return tokens


interests_filename = 'data/interests.txt'


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


with suppress(Exception):
    UserInterestsPlugin.broken = True
    UserInterestsPlugin._read_data()  # noqa
    UserInterestsPlugin.broken = False
