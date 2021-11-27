import math
from collections import Counter, defaultdict
from pprint import pprint

from core.helpers.utils import counter_top
from server.helpers.tied_value import TiedValue
from server.helpers.utils import absolute_path
from server.routes.vk.plugins.tokenizer import ContextTiedValue

words_filename = '../data/russian_words.txt'
stop_words_filename = '../data/stop_words.txt'


class IDFCalculator:
    _frequent_words = {}
    _stop_words = set()

    @classmethod
    def _compute_idf(cls, word, corpus):
        return sum([1 for text in corpus if word in text])

    @classmethod
    def _read_frequent_words(cls):
        with open(absolute_path(__file__, words_filename), 'r') as f:
            lines = f.readlines()

        for i, word in enumerate(lines[:2000]):
            cls._frequent_words[word.strip()] = i

    @classmethod
    def _read_stop_words(cls):
        with open(absolute_path(__file__, stop_words_filename), 'r') as f:
            lines = f.readlines()
        for word in lines:
            cls._stop_words.add(word.strip('\n').lower())

    @classmethod
    def _combine_tied(cls, left, right):
        return ContextTiedValue(left.value, left.context + right.context)

    @classmethod
    def _substr(cls, text: str, words: list[str]):
        indexes = sorted([(text.find(word), word) for word in words])
        left = indexes[0][0]
        right = indexes[-1][0]
        return text[left: right + len(indexes[-1][1])]

    @classmethod
    def _repr_tied(cls, tied_value: ContextTiedValue):
        context = sorted(tied_value.context, key=lambda x: x[1])
        # print(context)
        i = 0
        variants = []
        while i < len(context):
            words = []
            curr = context[i][1]
            while i < len(context) and curr == context[i][1]:
                words.append(context[i][0])
                i += 1
            variants.append(cls._substr(curr, words))
        return variants[0]

    @classmethod
    def _choose_best(cls, tokens: list[str]) -> str:
        tokens = sorted(tokens, key=lambda x: len(x))
        smallest = len(tokens[0])
        tokens = filter(lambda x: len(x) == smallest, tokens)
        return sorted(tokens)[-1]

    @classmethod
    def _repr_label(cls, label: tuple[int, str]):
        weight, name = label
        if name[0].isalpha() and not name[0].isupper():
            name = name[0].upper() + name[1:]
        return name, weight

    @classmethod
    def calculate(cls, texts: list[str]):
        """TF-IDF
        http://nlpx.net/archives/57
        """
        TOP_IDF_ITEMS_COUNT = 8
        COUNTER_MIN_LIMIT = 1
        OUTPUT_WEIGHT_LIMIT = 3

        from server.routes.vk.plugins.interests import Morphology
        words = [Morphology.tied_tokenize(text) for text in texts]
        all_words = {}
        for word in sum(words, []):
            if word not in all_words:
                all_words[word] = word
            else:
                old = all_words.pop(word)
                word = cls._combine_tied(old, word)
                all_words[word] = word
        idf = Counter({word: cls._compute_idf(word, words) for word in all_words})
        top_items = counter_top(idf.most_common(TOP_IDF_ITEMS_COUNT), COUNTER_MIN_LIMIT)
        same_context = defaultdict(list)
        best_token = {}
        for item, count in top_items:
            item.weight = count
            for word, text in item.context:
                same_context[text].append((word, item))

        for text, words in list(same_context.items()):
            tokens = list(map(lambda x: x[1], words))
            weight = sum(map(lambda x: x[1].weight, words)) #+ sum([1 for _, vals in same_context.items() if all([token in map(lambda x: x[1], vals) for token in tokens])])
            substr = cls._substr(text, list(map(lambda x: x[0], words)))
            # print(substr, weight, tokens)
            for token in tokens:
                old = best_token.get(token)
                if not old:
                    best_token[token] = (substr, weight, tokens)
                else:
                    old_substr, old_weight, _ = old
                    if weight > old_weight:
                        best_token[token] = (substr, weight, tokens)
                    elif weight == old_weight and len(substr) < len(old_substr):
                        best_token[token] = (substr, weight, tokens)

        used_tokens = set()
        labels = []
        targets = sorted([(item[1], item[0], item[2]) for token, item in best_token.items()], reverse=True)
        for weight, substr, tokens in targets:
            remain_tokens = []
            for token in tokens:
                if token not in used_tokens:
                    remain_tokens.append(token)
            used_tokens.update(set(tokens))
            if len(remain_tokens) == len(tokens):
                used_tokens.update(set(tokens))
                labels.append((weight, substr))
            else:
                for token in remain_tokens:
                    labels.append(
                        (idf[token], cls._choose_best(list(map(lambda x: x[0], token.context)))),
                    )
                    used_tokens.add(token)

        labels = sorted(labels, reverse=True)
        labels = list(map(cls._repr_label, labels))
        labels = list(filter(lambda x: x[0].lower() not in cls._frequent_words, labels))
        labels = list(filter(lambda x: x[0].lower() not in cls._stop_words, labels))
        labels = list(filter(lambda x: x[1] >= OUTPUT_WEIGHT_LIMIT, labels))
        return labels


IDFCalculator._read_frequent_words()  # noqa
IDFCalculator._read_stop_words()  # noqa
