import random
from typing import List, Tuple, Any, Dict

from dealer import Utils
from dealer.Utils import SUITS, VALUES
from dealer.Card import Card


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


class Deck:
    def __init__(self, cards: List[Card] = None, deck_id: int=0):
        if cards is None:
            cards = []
        self._cards = list(cards)
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
        number_of_hands = len(self._cards) // 4
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
        return list(built_cards)

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
            self._cards = list(self._cards) + list(other._cards)
        elif isinstance(other, list):
            self._cards.extend(other)
        elif isinstance(other, Card):
            self._cards.append(other)
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


class Hand:
    def __init__(self, cards: List[Card] = None):
        if cards is None:
            cards = []
        self._count = {}
        self._cards = {}
        for suit in SUITS:
            self._cards[suit] = []
            self._count[suit] = 0
        for card in cards:
            self._cards[card.suit].append(card)
            self._count[card.suit] += 1
        # self.self_sort()

    @property
    def num_of_cards(self):
        cnt = 0
        for suit in SUITS:
            cnt += len(self._cards[suit])
        return cnt

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
            for card in other:
                self._cards[card.suit].append(card)
                self._count[card.suit] += 1
        elif isinstance(other, Card):
            self._cards[other.suit].append(other)
            self._count[other.suit] += 1
        else:
            raise NotImplementedError
        # self.self_sort(self)

    def pop_random_from_suit(self, suit: SUITS = SUITS.NEITHER):
        if suit is SUITS.NEITHER:
            random_card = random.randint(0, self.num_of_cards-1)
            for suit in SUITS:
                try:
                    discarded = self._cards[suit].pop(random_card)
                except IndexError:
                    random_card -= self.count(suit)
                else:
                    self._count[suit] -= 1
                    self.check_count()
                    return discarded
        else:
            num_of_cards_in_suit = self.count(suit)
            if num_of_cards_in_suit:
                random_idx = random.randint(0, num_of_cards_in_suit-1)
                discarded = self._cards[suit].pop(random_idx)
                self._count[suit] -= 1
                self.check_count()
                return discarded
            else:
                return self.pop_random_from_suit()
        raise RuntimeError("can't find a random card")

    @property
    def cards(self):
        return self._cards

    def count(self, suit=None):
        if suit:
            return self._count[suit]
        cnt = 0
        for s in SUITS:
            cnt += self._count[s]
        return cnt

    def check_count(self):
        for suit in SUITS:
            if self._count[suit] < 0:
                raise RuntimeError("Ran out of cards in " + suit)

    def __iter__(self):
        for suit in SUITS:
            for card in self._cards[suit]:
                yield card

    # def __next__(self):
    #     try:
    #         next_card = self._cards[SUITS(self.suit_idx)][self.card_idx]
    #     except IndexError:
    #         self.suit_idx += 1
    #         self.card_idx = 0
    #         return self.__next__()
    #     except KeyError:
    #         raise StopIteration
    #     return next_card

    def __str__(self):
        return str(self._cards)

    @property
    def most_common(self):
        """ returns a sorted list from the number of each card in the hand """
        sorted_list = []
        for s in SUITS:
            if self._count[s]:
                sorted_list.append((s, self._count[s]))
        sorted_list.sort(key=lambda tup: tup[1])
        return sorted_list

    def pop_card(self, suit, index=-1):
        removed = self._cards[suit].pop(index)
        self._count[suit] -= 1
        self.check_count()
        return removed
