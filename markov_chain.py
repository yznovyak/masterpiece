from collections import Counter, defaultdict
from random import Random


class MarkovChain(object):
    def __init__(self):
        self.edges = defaultdict(list)

    def add(self, src, dst):
        self.edges[src].append(dst)

    def generate(self, node, prng=None):
        if prng is None:
            prng = Random()

        while True:
            possible_next = self.edges[node]
            n = len(possible_next)
            if n == 0:
                return
            else:
                node = possible_next[prng.randint(0, n-1)]
                yield node
