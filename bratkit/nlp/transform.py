import numpy as np
from nltk.tokenize import WordPunctTokenizer, PunktSentenceTokenizer
from tqdm import tqdm

from bratkit.models import Span
from bratkit.nlp.utils import tokenize, construct_char_token_map, set_slice_val


class LabelSequenceGenerator(object):
    DEFAULT_OUTSIDE_LABEL = 'O'

    def __init__(self, outside_label=DEFAULT_OUTSIDE_LABEL,
                 tokenizer=None, splitter=None):
        self.outside_label = outside_label
        if splitter is None:
            self.splitter = PunktSentenceTokenizer()
        else:
            self.splitter = splitter
        if tokenizer is None:
            self.tokenizer = WordPunctTokenizer()
        else:
            self.tokenizer = tokenizer

    def _tokenize(self, text):
        return tokenize(self.tokenizer, text, with_spans=True)

    def split_blocks(self, text):
        return tokenize(self.splitter, text, with_spans=True)

    def transform_document(self, doc):
        tokens = []
        labels = []

        splitted = self.split_blocks(doc.text)
        for bltxt, blsp in splitted:
            tokenised = self._tokenize(bltxt)
            char2token = construct_char_token_map(tokenised)

            markers = np.asarray([self.outside_label] * len(tokenised),
                                 dtype='U12')
            for ent in doc.entities.values():
                if not ent.span.within(blsp):
                    continue
                ets = Span(char2token[ent.span.start - blsp.start],
                           char2token[ent.span.end - blsp.start - 1] + 1)
                markers = set_slice_val(markers, ets.start, ets.end, ent.type)

            tokenised = [(t, sp.shift(blsp.start))
                         for t, sp in tokenised]
            tokens.append(tokenised)
            labels.append(markers)
        return tokens, labels

    def transform_documents(self, documents, verbose=1):
        prg = documents
        if verbose:
            prg = tqdm(documents, desc='transforming')
        transformed = [self.transform_document(d) for d in prg]
        if len(transformed) == 0:
            return []
        return list(zip(*transformed))
