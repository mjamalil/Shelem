import copy
from typing import List, Tuple, Any, Dict

from dealer import Utils
from dealer.Utils import SUITS, VALUES
from dealer.Card import Card
import random


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


class Hand(object):
    def __init__(self, player_id: int, cards: List[Card]):
        self.cards_map = {}
        self.init_player_id = player_id
        for ind, card in enumerate(cards):
            self.cards_map[(player_id + ind) % 4] = card

    def __str__(self):
        result = ""
        for i in range(4):
            if i == self.init_player_id:
                result += "**[{:14s}]**\t\t".format(str(self.cards_map[i]))
            else:
                result += "  [{:14s}]  \t\t".format(str(self.cards_map[i]))
        return result


class Deck(object):
    def __init__(self, cards: List[Card] = None, deck_id: int=0):
        if cards is None:
            cards = []
        self._cards = list(sorted(cards))
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
        self._cards = list(cards)

    @property
    def cards(self) -> List:
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

    def pop_random_from_suit(self, suit: SUITS):
        # TODO optimize it with memoization
        if suit is SUITS.NEITHER:
            return self._cards.pop(0)
        pop_index = 0
        for ind, card in enumerate(self._cards):
            if card.suit == suit:
                pop_index = ind
                break
        return self._cards.pop(pop_index)

    @staticmethod
    def build_cards() -> List:
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
        return list(sorted(built_cards))

    def __add__(self, other):
        if isinstance(other, Deck):
            return Deck(cards=list(self._cards) + list(other._cards))
        elif isinstance(other, list):
            return Deck(cards=list(self._cards) + other)
        elif isinstance(other, Card):
            return Deck(cards=list(self._cards) + [other])
        else:
            raise NotImplementedError

    def __iadd__(self, other):
        if isinstance(other, Deck):
            self._cards = sorted(list(self._cards) + list(other._cards))
        elif isinstance(other, list):
            self._cards = sorted(list(self._cards) + other)
        elif isinstance(other, Card):
            self._cards = sorted(list(self._cards) + [other])
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
        elif isinstance(other, list):
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
        elif isinstance(other, list):
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

    def __iter__(self):
        for x in self._cards:
            yield x


class SortedCards(object):
    def __init__(self, cards=None):
        if cards is None:
            cards = []

        self._cards = {}
        for card in cards:
            if card.suit in self._cards:
                self._cards[card.suit].append(card.value)
            else:
                self._cards[card.suit] = [card.value, ]
        self.self_sort()

    @property
    def num_of_cards(self):
        count = 0
        for suit in SUITS:
            count += len(self.my_cards[suit])
        return count

    def self_sort(self):
        for suit in SUITS:
            if suit in self._cards:
                self._cards[suit] = sorted(self._cards[suit])
            else:
                self._cards[suit] = []

    def __getitem__(self, item: SUITS):
        return self._cards[item]

    def add_card(self, other):
        if isinstance(other, Deck) or isinstance(other, list):
            for card in Deck:
                self._cards[card.suit].append(card.value)
        elif isinstance(other, Card):
            self._cards[other.suit].append(other.value)
        else:
            raise NotImplementedError
        self.self_sort(self)

    def pop_random_from_suit(self, suit: SUITS = SUITS.NEITHER):
        if suit is SUITS.NEITHER:
            random_card = random.randint(0, self.num_of_cards)
            for suit in SUITS:
                try:
                    return self._cards.pop(random_card)
                except IndexError:
                    random_card -= len(self.my_cards[suit])
        else:
            num_of_cards_in_suit = len(self._cards[suit])
            if num_of_cards_in_suit:
                return self._cards.pop(random.randint(0, num_of_cards_in_suit))
            else:
                return self.pop_random_from_suit()
        raise RuntimeError("can't find a random card")
