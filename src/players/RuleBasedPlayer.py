from typing import Tuple, List

from dealer import Deck
from dealer.Card import Card
from dealer.Utils import GAMEMODE, SUITS
from players.Player import Player, WORST_SUIT, BEST_SUIT


class RuleBasedPlayer(Player):
    def __init__(self, player_id, team_mate_player_id):
        super(RuleBasedPlayer, self).__init__(player_id, team_mate_player_id)

    def begin_game(self, deck: Deck):
        super().begin_game(deck)
        # self.deck._cards = sorted(self.deck._cards)
        # self.card_by_suit = {}
        # if card.suit not in self.card_by_suit:
        #     self.card_by_suit[card.suit] = []
        # self.card_by_suit[card.suit].append(ind)

    # def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
    def discard_cards_decide_hokm(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        # gets the best suit
        hokm_suit = self.my_cards.most_common[BEST_SUIT][0]
        for _ in range(4):
            worst_suit = self.my_cards.most_common[WORST_SUIT][0]
            discarded = self.my_cards.pop_card(worst_suit)
            self.saved_deck += discarded
        return GAMEMODE.NORMAL, hokm_suit

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
