# coding=utf-8
import argparse
import os
import pickle
import sys
import random
from collections import defaultdict, Counter

import renderer
from tokenizers import SentenceTokenizer, WordTokenizer
from markov_chain import MarkovChain
from consts import *


class MasterpieceWriter(object):
    def __init__(self, sentence_tokenizer, word_tokenizer):
        self.sentence_tokenizer = sentence_tokenizer
        self.word_tokenizer = word_tokenizer

        self.markov_chain = MarkovChain()
        self.word_contexts = defaultdict(list)

        self.word_counts = Counter()
        self.word_pair_counts = Counter()

    def _paragraphs_from_file(self, file_name):
        sys.stderr.write("Reading from file {0}\n".format(file_name))
        with open(file_name) as f:
            for line in f:
                line = line.strip()
                if line != "":
                    yield line

    def _get_words_and_contexts(self, input_files):
        for file_name in input_files:
            for paragr in self._paragraphs_from_file(file_name):
                sentences = self.sentence_tokenizer.tokenize(paragr)
                if len(sentences) == 0:
                    continue

                yield PARA_BEGIN, None
                for sentence in sentences:
                    words, contexts = self.word_tokenizer.tokenize(sentence)
                    if len(words) == 0:
                        continue

                    yield SENT_BEGIN, None
                    for word in words:
                        yield (word, None)
                    yield SENT_END, None

                    if contexts is not None:
                        yield None, contexts

                yield PARA_END, None

    def train(self, training_files):
        prev_prev_word, prev_word = None, None
        for word, contexts in self._get_words_and_contexts(training_files):
            if contexts is not None:
                for ctx_key in contexts:
                    self.word_contexts[ctx_key].extend(contexts[ctx_key])

            if word is not None:
                # Train markov chain (need at least 3 tokens)
                if prev_prev_word is not None:
                    self.markov_chain.add((prev_prev_word, prev_word),
                                          (prev_word, word))
                # Collect stats
                if word not in ALL_SPECIAL:
                    self.word_counts[word] += 1
                    if prev_word not in ALL_SPECIAL:
                        self.word_pair_counts[(prev_word, word)] += 1

                # Update prev_prev_word and prev_word
                prev_prev_word, prev_word = prev_word, word

    def stats(self, top=10):
        return self.word_counts.most_common(top), \
               self.word_pair_counts.most_common(top)

    def generate_masterpiece(self, prng=None):
        yield PARA_BEGIN
        yield SENT_BEGIN
        for next in self.markov_chain.generate((PARA_BEGIN, SENT_BEGIN), prng):
            w1, w2 = next
            yield w2

def get_all_files(path):
    if type(path) == list:
        for x in path:
            for y in get_all_files(x):
                yield y
        return

    if os.path.isfile(path) and path.endswith(".txt"):
        yield path
    if os.path.isdir(path):
        for sub_path in os.listdir(path):
            for x in get_all_files(os.path.join(path, sub_path)):
                yield x

def run(training_fileset, masterpiece_length, show_top_stats):
    sentence_tokenizer = SentenceTokenizer()
    word_tokenizer = WordTokenizer()
    mw = MasterpieceWriter(sentence_tokenizer, word_tokenizer)

    # Train
    all_files = [x for x in get_all_files(training_fileset)]
    mw.train(get_all_files(all_files))

    # Save stats to file
    word_stats, pair_word_stats = mw.stats(show_top_stats)
    with open("stats.pickle", "wb") as f:
        pickle.dump((word_stats, pair_word_stats), f)

    # Generate masterpiece
    prng = random.Random(0)
    output_text = []
    for word in mw.generate_masterpiece(prng):
        output_text.append(word)
        if word == PARA_END and len(output_text) >= masterpiece_length:
            break

    # Write masterpiece as an html file
    for piece in renderer.html(output_text, mw.word_contexts, prng):
        sys.stdout.write(piece)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate some masterpiece.')
    parser.add_argument("--length", type=int, default=10000, nargs="?",
                        help="Length of the masterpiece (in words).")
    parser.add_argument("--show_top_words", type=int, default=100, nargs="?",
                        help="Display this much most commonly used words.")
    parser.add_argument("--training_set", nargs="*", default="texts/asimov",
                        help="List of files to train on.")

    args = parser.parse_args()
    run(args.training_set, args.length, args.show_top_words)
