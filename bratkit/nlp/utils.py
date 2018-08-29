import numpy as np

from bratkit.models import Span


def construct_char_token_map(tokenised):
    char_length = tokenised[-1][1].end
    tm = np.asarray([None] * char_length)
    for i, (_, span) in enumerate(tokenised):
        tm[span.start:span.end] = i
    return tm


def tokenize(tokenizer, text, with_spans=False):
    if with_spans:
        return [(text[start:end], Span(start, end)) for start, end in
                tokenizer.span_tokenize(text)]
    return tokenizer.tokenize(text)


def set_slice_val(a, start, end, val):
    for i in range(start, end):
        a[i] = val
    return a
