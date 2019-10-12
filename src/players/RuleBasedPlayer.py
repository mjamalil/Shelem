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

    # def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
    def discard_cards_decide_hokm(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        """
        # gets the best suit
        discards = []
        hokm_suit = self.my_cards.most_common[BEST_SUIT][0]
        for _ in range(4):
            worst_suit = self.my_cards.most_common[WORST_SUIT][0]
            discards.append(self.my_cards.pop_card(worst_suit))
        return GAMEMODE.NORMAL, hokm_suit, discards

    def play_a_card_from_suit(self, hands_played: List[List[Card]], current_hand: List[Card], suit: SUITS) -> Card:
        if current_hand:
            return super().play_a_card(hands_played, current_hand)
        # I'm the first player
        if self.is_hakem:
            return super().play_a_card(hands_played, current_hand)
            if suit == SUITS.NEITHER:
                # decide the best suit to play
                if self.my_cards.count(self.hokm_suit) < 3:
                    # play anything but hokm
                    suit = self.hokm_suit
                else:
                    suit = self.hokm_suit
        else:
            return super().play_a_card(hands_played, current_hand)
