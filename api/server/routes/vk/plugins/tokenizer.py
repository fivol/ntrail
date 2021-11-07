import re
import nltk
import pymorphy2

from server.helpers.tied_value import TiedValue


class ContextTiedValue(TiedValue):
    def __init__(self, value, contexts):
        super().__init__(value, None)
        self.context = contexts
        self.weight = None


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

    # Experimental
    @classmethod
    def tied_tokenize(cls, text: str) -> list[ContextTiedValue]:
        tokens = []
        # m.lemmatize(text)
        for token in nltk.word_tokenize(text, language='russian'):
            if len(token) < 3:
                continue
            # tokens.append(stem)
            lexem = cls._morph.parse(token)[0]
            if cls._denied_tags_reg.search(str(lexem.tag)):
                continue
            tokens.append(ContextTiedValue(cls._stemmer.stem(lexem.normal_form), [(token, text)]))

        return tokens
