import random
from typing import Tuple, List
from collections import Counter

from dealer import Deck
from dealer.Card import Card
from dealer.Utils import GAMEMODE, SUITS
from players.Player import Player


class RuleBasedPlayer(Player):
    def __init__(self, player_id, team_mate_player_id):
        super(RuleBasedPlayer, self).__init__(player_id, team_mate_player_id)

    def begin_game(self, deck: Deck):
        super().begin_game(deck)
        self.deck._cards = sorted(self.deck._cards)
        self.cnts = Counter()
        self.mappings = {}
        for ind, card in enumerate(self.deck._cards):
            self.cnts[card.suit] += 1
            if card.suit not in self.mappings:
                self.mappings[card.suit] = []
            self.mappings[card.suit].append(ind)

    # def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
    def discard_cards_decide_hokm(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        hokm_suit = self.cnts.most_common()[0][0]
        discard_hand = []
        last_index = -1
        while len(discard_hand) < 4:
            lst = self.mappings[self.cnts.most_common()[last_index][0]]
            discard_hand.append(lst.pop())
            if not lst:
                last_index -= 1
        return tuple(discard_hand), self.game_mode, hokm_suit

    def play_a_card(self, hands_played: List[List[Card]], current_hand: List[Card]) -> Card:
        # TODO: not implemented
        # if I'm not the first player
        # if current_hand:
        #     suit = current_hand[0].suit
        # # if I'm the first player and hakem
        # elif not hands_played and not current_hand:
        #     suit = self.hokm_suit
        # else:
        #     suit = SUITS.NEITHER
        return super().play_a_card(hands_played, current_hand)
