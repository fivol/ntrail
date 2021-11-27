from collections import Counter, defaultdict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from transliterate import translit, slugify
from textblob import TextBlob
import langid


class NameComparator:
    # https://habr.com/ru/post/491448/

    @classmethod
    def _compare_strings(cls, s1, s2):
        return

    @classmethod
    def compare_names(cls, name1, name2):
        if not name1 or not name2:
            return 0
        return fuzz.token_sort_ratio(name1, name2)

    @classmethod
    def _match_one_many(cls, name, names):
        multiplied_name = [name] * len(names)
        return Counter({
            n2: cls.compare_names(n1, n2)
            for n1, n2 in zip(multiplied_name, names)
        }).most_common()

    @classmethod
    def _enrich_name(cls, name: str):
        # TODO
        names = [name]
        if langid.classify(name)[0] == 'ru':
            names.append(translit(name, reversed=True))
            names.append(slugify(name))
        items = name.split(' ')
        if len(items) > 1:
            names += items
        return names

    @classmethod
    def best_match(cls, existing_names: list[str], target_names: list):
        existing_names = filter(bool, existing_names)
        existing_names = sum(map(cls._enrich_name, existing_names), [])
        target_names = list(filter(bool, target_names))
        name_score = defaultdict(int)
        for origin in existing_names:
            for target in target_names:
                # TODO
                if isinstance(target, tuple):
                    score = max(*[cls.compare_names(origin, item) for item in target if isinstance(item, str)])
                else:
                    score = cls.compare_names(origin, target)
                name_score[target] = max(name_score[target], score)
        return Counter(name_score)
