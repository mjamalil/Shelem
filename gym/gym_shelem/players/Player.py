import random
from typing import Tuple, List

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Utils import GAMEMODE, SUITS


class Bet(object):
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


class Player(object):
    def __init__(self, player_id, team_mate_player_id):
        self.deck = Deck()
        self.saved_deck = Deck()
        self.is_hakem = False
        self.game_has_begun = False
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NEITHER
        self.player_id = player_id
        self.team_mate_player_id = team_mate_player_id

    def init_policies_from_another_policy(self, other_policy):
        pass

    def begin_game(self, deck: Deck):
        self.deck = deck
        self.game_has_begun = True
        self.saved_deck = Deck()

    def set_hokm_and_game_mode(self, game_mode: GAMEMODE, hokm_suit: SUITS):
        self.game_mode = game_mode
        self.hokm_suit = hokm_suit

    def store_hand(self, hand: List[Card]):
        self.saved_deck += hand

    def make_hakem(self, middle_hand: Deck)-> Tuple[GAMEMODE, SUITS]:
        """
        :return: Game mode and hokm suit
        """
        if not self.game_has_begun:
            raise ValueError("Game has not started yet")
        self.is_hakem = True
        self.deck += middle_hand
        new_deck = Deck([])
        game_mode = self.decide_game_mode()
        hokm_suit = self.decide_trump()
        for _ in range(4):
            saving_index = self.decide_widow_card()
            for ind in range(len(self.deck)):
                if ind == saving_index:
                    self.saved_deck += self.deck[ind]
                else:
                    new_deck += self.deck[ind]
            self.deck = new_deck
        return game_mode, hokm_suit

    def play_a_card(self, hands_played: List[List[Card]], current_hand: List[Card]) -> Card:
        """
        :return: pops and plays the best available card in the current hand  
        """
        # TODO: NotImplemented

        if current_hand:
            suit = current_hand[0].suit
        elif not hands_played and not current_hand:
            suit = self.hokm_suit
        else:
            suit = SUITS.NEITHER
        return self.deck.pop_random_from_suit(suit)

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Sacore should be strictly > previous_last_bet
        """
        # TODO: NotImplemented
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

    def decide_game_mode(self) -> GAMEMODE:
        return self.game_mode

    def decide_trump(self) -> SUITS:
        return self.deck.cards[0].suit

    def decide_widow_card(self) -> int:
        """
        if its a hakem hand, selects the most probable card index out of the hand and returns it to be saved in the saved_deck
        :return: 
        """
        return random.sample(range(len(self.deck.cards)), 1)[0]
