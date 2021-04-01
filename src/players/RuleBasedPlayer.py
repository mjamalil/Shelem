import random
from typing import Tuple, List
from collections import Counter

from dealer.Card import Card
from dealer.Utils import GAMEMODE, SUITS
from players.Player import Player, Bet


class RuleBasedPlayer(Player):
    def __init__(self, player_id, team_mate_player_id):
        super(RuleBasedPlayer, self).__init__(player_id, team_mate_player_id)

    # def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
    def discard_cards_from_leader(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
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
        hokm_suit = cnts.most_common()[0][0]
        saving_hand = []
        last_index = -1
        while len(saving_hand) < 4:
            lst = mappings[cnts.most_common()[last_index][0]]
            saving_hand.append(lst.pop())
            if not lst:
                last_index -= 1
        return tuple(saving_hand), self.game_mode, hokm_suit

    # def play_a_card(self, hands_played: List[List[Card]], current_hand: List[Card]) -> Card:
