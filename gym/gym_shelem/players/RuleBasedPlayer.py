from typing import Tuple
from collections import Counter

from dealer.Utils import SUITS
from players.Player import Player


class RuleBasedPlayer(Player):
    def __init__(self, player_id, team_mate_player_id):
        super(RuleBasedPlayer, self).__init__(player_id, team_mate_player_id)

    def decide_trump(self) -> SUITS:
        self.deck._cards = sorted(self.deck._cards)
        cnts = Counter()
        for ind, card in enumerate(self.deck._cards):
            cnts[card.suit] += 1
        hokm_suit = cnts.most_common()[0][0]
        return hokm_suit

    def decide_widow_card(self) -> int:
        """
        if its a hakem hand, selects the most probable card index out of the hand and returns it to be saved in the saved_deck
        :return:
        """
        self.deck._cards = sorted(self.deck._cards)
        cnts = Counter()
        mappings = {}
        for ind, card in enumerate(self.deck._cards):
            cnts[card.suit] += 1
            if card.suit not in mappings:
                mappings[card.suit] = []
            mappings[card.suit].append(ind)
        last_index = -1
        lst = mappings[cnts.most_common()[last_index][0]]
        most_probable_widow = lst.pop()
        return most_probable_widow

    def decide_widow_hand(self) -> Tuple[int, int, int, int]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck
        :return:
        """
        self.deck._cards = sorted(self.deck._cards)
        cnts = Counter()
        mappings = {}
        for ind, card in enumerate(self.deck._cards):
            cnts[card.suit] += 1
            if card.suit not in mappings:
                mappings[card.suit] = []
            mappings[card.suit].append(ind)
        saving_hand = []
        last_index = -1
        while len(saving_hand) < 4:
            lst = mappings[cnts.most_common()[last_index][0]]
            saving_hand.append(lst.pop())
            if not lst:
                last_index -= 1
        return tuple(saving_hand)
