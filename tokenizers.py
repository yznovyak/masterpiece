import re
import sys
import string
from collections import defaultdict
from consts import *


class SentenceTokenizer(object):
    """A tokenizer that splits text into list of sentences.

    Currently this tokenizer uses a regexp I found at StackOverflow.
    Here's the regexp:

    If we need much better accuracy we can use NLTK which has built in
    sentence tokenizer for English.
    """

    # https://regex101.com/r/nG1gU7/27
    regexp = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s'

    def tokenize(self, text):
        """Returns list of sentences from a single line text."""
        return re.split(self.regexp, text)


class WordTokenizer(object):
    """A tokenizer that splits sentence into a list of canonical words.

    "Hello, world!" -> ["hello", "world"]

    A canonical word is simply lowercased version of the word with all
    non-essential things removed.  "Didn't" -> "didn't", "i.e." -> "ie",
    etc.

    This is a very simple tokenizer that:
    1. first converts the sentence to the lowercase,
    2. splits it using ' ' as a separator,
    3. removes all non-lowercase and some non special chars
       (apostrophe is kept to handle words like "didn't", hyphen
       is kept to keep words like "pleasant-tasting".)

    This tokenizer is a little fancier than SentenceTokenizer because
    it also returns a "context" for each pair of words.  This context will
    be used to deduce punctuation and proper capitalization when building
    the final text.
    """

    def __init__(self):
        # TODO: Check if deletechars can be a set().
        chars_to_keep = string.lowercase + "-'"
        self.deletechars = "".join(
            [chr(x) for x in range(256) if chr(x) not in chars_to_keep])

    def _get_suffix_punctuation(self, s):
        s_sans_suffix_punctuation = s.rstrip(string.punctuation)
        return s[len(s_sans_suffix_punctuation):]

    def _calc_context(self, words, clean_words, pos):
        cur_word = clean_words[pos]

        # find previous clean word
        prev_pos = pos-1
        while prev_pos >= 0 and len(clean_words[prev_pos]) == 0:
            prev_pos -= 1

        if prev_pos == -1:
            # This is the first actual word in sentence
            prev_word = SENT_BEGIN
            this_context = " ".join(words[:pos+1])
        else:
            # This is not the first actual word
            prev_word = clean_words[prev_pos]
            this_context = self._get_suffix_punctuation(words[prev_pos])
            this_context += " "
            this_context += " ".join(words[prev_pos+1:pos+1])

        # Remove trailing punctuation from this context because trailing
        # punctuation goes into the context of the next word.
        this_context = this_context.rstrip(string.punctuation)

        return (prev_word, cur_word), this_context

    def tokenize(self, sentence):
        sentence_words = sentence.split()

        canonical_words = [word.lower().translate(None, self.deletechars)
                           for word in sentence_words]
        non_empty_canonical_words = []

        contexts = defaultdict(list)
        last_valid_ind = -1
        for ind in range(len(canonical_words)):
            word = canonical_words[ind]
            if word == "":
                continue

            last_valid_ind = ind
            non_empty_canonical_words.append(word)

            ctx_key, ctx_val = (
                self._calc_context(sentence_words, canonical_words, ind))
            contexts[ctx_key].append(ctx_val)

        if len(non_empty_canonical_words) == 0:
            # This sentence contains only punctuation.  Skip it
            return [], None

        # This sentence contains at least one valid word.  Add end of the
        # sentence punctuation.
        tail_context = self._get_suffix_punctuation(
                sentence_words[last_valid_ind])
        more_tail_context = " ".join(sentence_words[last_valid_ind+1:])

        if len(tail_context) > 0 and len(more_tail_context) > 0:
            tail_context = tail_context + ' ' + more_tail_context
        else:
            tail_context += more_tail_context

        tail_context_key = (non_empty_canonical_words[-1], SENT_END)
        contexts[tail_context_key].append(tail_context)

        return non_empty_canonical_words, contexts
