import math
from collections import Counter, defaultdict
from pprint import pprint

from core.helpers.utils import counter_top
from server.helpers.tied_value import TiedValue
from server.routes.vk.plugins.tokenizer import ContextTiedValue


class IDFCalculator:
    @classmethod
    def _compute_idf(cls, word, corpus):
        return sum([1 for text in corpus if word in text])

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
    def calculate(cls, texts: list[str]):
        """TF-IDF
        http://nlpx.net/archives/57
        """

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
        top_items = counter_top(idf.most_common(8))
        same_context = defaultdict(list)
        best_token = {}
        for item, count in top_items:
            item.weight = count
            for word, text in item.context:
                same_context[text].append((word, item))

        # return None
        for text, words in same_context.items():
            tokens = list(map(lambda x: x[1], words))
            weight = sum(map(lambda x: x[1].weight, words))
            substr = cls._substr(text, list(map(lambda x: x[0], words)))
            # print(substr, weight, tokens)
            for token in tokens:
                old = best_token.get(token)
                if not old:
                    best_token[token] = (substr, weight)
                else:
                    old_substr, old_weight = old
                    if weight > old_weight:
                        best_token[token] = (substr, weight)
                    elif weight == old_weight and len(substr) < len(old_substr):
                        best_token[token] = (substr, weight)
        results = list(map(lambda x: x[0], set(best_token.values())))
        pprint(results)
        return [
            (cls._repr_tied(item), count) for item, count in top_items if count != 1
        ]
