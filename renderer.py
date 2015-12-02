import string

from consts import *
from random import Random


def html(words, contexts, prng):
    """Generates HTML text out given array of words."""

    if prng is None:
        prng = Random()

    yield "<html>\n"
    yield "  <head></head>\n"
    yield "  <body>\n"
    prev_word = None
    for word in words:
        if word == PARA_BEGIN:
            yield "    <p>"
        elif word == PARA_END:
            yield "</p>\n"
        elif word == SENT_BEGIN:
            if prev_word != PARA_BEGIN:
                yield " "
        else:
            possible = contexts.get((prev_word, word), [word])
            n = len(possible)
            yield possible[prng.randint(0, n-1)]

        prev_word = word

    yield "  </body>\n"
    yield "</html>\n"
