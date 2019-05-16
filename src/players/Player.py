import random
from typing import Tuple, List

from dealer.Card import Card
from dealer.Deck import Deck, SortedCards
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
        # self.my_cards = SortedCards()
        self.my_cards = None
        self.saved_deck = Deck()
        self.is_hakem = False
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NEITHER
        self.player_id = player_id
        self.team_mate_player_id = team_mate_player_id

    @property
    def game_has_begun(self):
        return self.my_cards is not None

    def begin_game(self, deck: Deck):
        self.my_cards = SortedCards(deck.cards)
        self.saved_deck = Deck()

    def set_hokm_and_game_mode(self, game_mode: GAMEMODE, hokm_suit: SUITS):
        self.game_mode = game_mode
        self.hokm_suit = hokm_suit

    def store_hand(self, hand: List[Card]):
        self.saved_deck += hand

    def check_played_card(self, played_card, current_hand, first=False):
        if first and self.game_mode == GAMEMODE.NORMAL and played_card.suit is not self.hokm_suit:
            raise RuntimeError("Hakem didn't start with hokm")

        if current_hand:
            leading_suit = current_hand[0].suit
            if played_card.suit != leading_suit:
                if self.my_cards[leading_suit]:
                    raise RuntimeError(f"Player played {played_card} whereas the leading suit is {leading_suit}."
                                       f" He could have played {self.my_cards[leading_suit][0]}")

    def make_hakem(self, middle_hand: Deck) -> Tuple[GAMEMODE, SUITS]:
        """ 
        :return: Game mode and hokm suit 
        """
        if not self.game_has_begun:
            raise ValueError("Game has not started yet")
        self.is_hakem = True
        self.my_cards.add_card(middle_hand)
        game_mode, hokm_suit = self.discard_cards_decide_hokm()
        return game_mode, hokm_suit

    def play_a_card(self, hands_played: List[List[Card]], current_hand: List[Card]) -> Card:
        """
        :return: pops and plays the best available card in the current hand  
        """
        # TODO: Can be improved
        # if I'm not the first player
        if current_hand:
            suit = current_hand[0].suit
        # if I'm the first player and hakem
        elif not hands_played and not current_hand:
            suit = self.hokm_suit
        else:
            suit = SUITS.NEITHER
        return self.my_cards.pop_random_from_suit(suit)

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Sacore should be strictly > previous_last_bet
        """
        # TODO: Can be improved
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

    def discard_cards_decide_hokm(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        self.saved_deck += self.my_cards.pop_random_from_suit()
        # decide the suit with maximum number to be the hokm
        best_suit = None
        maximum_num = 0
        for suit in SUITS:
            if len(self.my_cards[suit]) > maximum_num:
                maximum_num = len(self.my_cards[suit])
                best_suit = suit

        return self.game_mode, best_suit
