from typing import Deque, Tuple, Any

from dealer import Utils
from dealer.Utils import GAMEMODE, SUITS, VALUES
from dealer.Card import Card
from collections import deque
import random


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


class Deck(object):
    def __init__(self, cards: Deque[Card]=None, deck_id: int=0):
        if cards is None:
            cards = []
        self._cards = deque(sorted(cards))
        self.deck_id = deck_id

    def deal(self) -> Tuple[Any, Any, Any, Any, Any]:
        if len(self.cards) == 0:
            self._cards = self.build_cards()
        if len(self._cards) < 52:
            raise ValueError("Not enough cards in deck to shuffle and deal!")
        self._shuffle()
        cards = list(self.cards)
        return Deck(cards[0:12], 1), Deck(cards[12:24], 2), Deck(cards[24:36], 3), \
            Deck(cards[36:40]), Deck(cards[40:52], 4)

    def _shuffle(self):
        if len(self.cards) == 0:
            self._cards = self.build_cards()
        cards = list(self._cards)
        for i in range(random.randint(1, 3)):
            splitted = [x for x in split(cards, random.randint(2, 5))]
            random.shuffle(splitted)
            cards = [y for x in splitted for y in x]
        self._cards = deque(cards)

    @property
    def cards(self) -> Deque:
        return self._cards

    @property
    def size(self) -> int:
        return len(self.cards)

    def get_deck_score(self) -> int:
        number_of_hands = len(self._cards) / 4
        score = number_of_hands * 5
        for card in self._cards:
            if card.value == Utils.VALUES.ACE or card.value == Utils.VALUES.TEN:
                score += 10
            elif card.value == Utils.VALUES.FIVE:
                score += 5
        return score

    @staticmethod
    def build_cards() -> Deque:
        """
        Current build does not build Jokers!
        """
        built_cards = []
        for suit in SUITS:
            if suit == SUITS.NEITHER:
                continue
            for val in VALUES:
                if val == VALUES.JOKER:
                    continue
                built_cards.append(Card(val, suit))
        return deque(sorted(built_cards))

    def __add__(self, other):
        if isinstance(other, Deck):
            return Deck(cards=list(self._cards) + list(other._cards))
        elif isinstance(other, deque):
            return Deck(cards=list(self._cards) + other)
        elif isinstance(other, Card):
            return Deck(cards=list(self._cards) + [other])
        else:
            raise NotImplementedError

    def __iadd__(self, other):
        if isinstance(other, Deck):
            self._cards = deque(sorted(list(self._cards) + list(other._cards)))
        elif isinstance(other, deque) or isinstance(other, list):
            self._cards = deque(sorted(list(self._cards) + other))
        elif isinstance(other, Card):
            self._cards = deque(sorted(list(self._cards) + [other]))
        else:
            raise NotImplementedError
        return self

    def __str__(self):
        return "".join([x.name + "\n" for x in self._cards]).rstrip("\n")

    def __repr__(self):
        return "Stack(cards=%r)" % self._cards

    def __setitem__(self, indice, value):
        self._cards[indice] = value

    def __len__(self):
        return len(self._cards)

    def __delitem__(self, index):
        del self._cards[index]

    def __getitem__(self, key):
        self_len = len(self)
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(self_len))]
        elif isinstance(key, int):
            if key < 0:
                key += self_len
            if key >= self_len:
                raise IndexError("The index ({}) is out of range.".format(key))
            return self._cards[key]
        else:
            raise TypeError("Invalid argument type.")

    def __contains__(self, card):
        return id(card) in [id(x) for x in self._cards]

    def __ne__(self, other):
        if isinstance(other, Deck):
            ocards = other._cards
        elif isinstance(other, deque):
            ocards = other
        else:
            return True
        if len(self._cards) == len(ocards):
            for i, card in enumerate(self._cards):
                if card != ocards[i]:
                    return True
            return False
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, Deck):
            ocards = other._cards
        elif isinstance(other, deque):
            ocards = other
        else:
            return False
        if len(self._cards) == len(ocards):
            for i, card in enumerate(self._cards):
                if card != ocards[i]:
                    return False
            return True
        else:
            return False
