import random
from typing import Tuple, List

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Utils import GAMEMODE, SUITS


class Bet:
    def __init__(self, player_id, bet_score):
        self.player_id = player_id
        self.bet_score = bet_score

    @property
    def id(self):
        return self.player_id

    @property
    def bet(self):
        return self.bet_score

    def __repr__(self):
        return "Bet(player_id=%r, score=%r)" % (self.id, self.bet)


class Player:
    def __init__(self, player_id, team_mate_player_id):
        self.deck = Deck()
        self.saved_deck = Deck()
        self.is_hakem = False
        self.game_has_begun = False
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NOSUIT
        self.player_id = player_id
        self.team_mate_player_id = team_mate_player_id
        self.trick_number = 0

    def begin_round(self, deck: Deck):
        self.deck = deck
        self.game_has_begun = True
        self.saved_deck = Deck()
        self.trick_number = 0

    def end_round(self, team1_score: int, team2_score: int):
        pass

    def set_hokm_and_game_mode(self, game_mode: GAMEMODE, hokm_suit: SUITS):
        self.game_mode = game_mode
        self.hokm_suit = hokm_suit

    def win_trick(self, hand: List[Card], winner_id: int, first_player: int):
        # calculate reward
        self.trick_number += 1
        if self.player_id == winner_id:
            self.saved_deck += hand

    def make_hakem(self, middle_hand: Deck) -> Tuple[GAMEMODE, SUITS]:
        """ 
        :return: Game mode and hokm suit 
        """
        if not self.game_has_begun:
            raise ValueError("Game has not started yet")
        self.is_hakem = True
        self.deck += middle_hand
        new_deck = Deck([])
        saving_indices, game_mode, hokm_suit = self.discard_cards_from_leader()
        for ind in range(16):
            if ind in saving_indices:
                self.saved_deck += self.deck[ind]
            else:
                new_deck += self.deck[ind]
        self.deck = new_deck
        return game_mode, hokm_suit

    def play_a_card(self, current_hand: List, current_suit: SUITS) -> Card:
        """
        :return: pops and plays the best available card in the current hand
        request action
        """
        # TODO: NotImplemented

        return self.deck.pop_random_from_suit(current_suit)

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Score should be strictly > previous_last_bet
        """
        # TODO: NotImplemented
        return Bet(self.player_id, 120)
        choice = random.random()
        if choice < 0.4:
            return Bet(self.player_id, 0)
        elif choice < 0.7:
            return Bet(self.player_id, random.randint(20, 22) * 5)
        elif choice < 0.9:
            return Bet(self.player_id, random.randint(23, 25) * 5)
        elif choice < 0.97:
            return Bet(self.player_id, random.randint(26, 30) * 5)
        else:
            return Bet(self.player_id, random.randint(31, 33) * 5)

    def discard_cards_from_leader(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        return random.sample(range(16), 4), self.game_mode, self.deck.cards[0].suit