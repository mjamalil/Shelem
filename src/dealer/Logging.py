from typing import List

from dealer.Card import Card
from dealer.Deck import Hand, Deck
from dealer.Utils import GAMEMODE, SUITS
from players.Player import Bet


class Logging:
    def __init__(self):
        self.hands = []
        self.bet = Bet(0, 0)
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NEITHER
        self.middle_deck = Deck()
        self.saved_hand = Deck()

    def add_hand(self, player_id: int, hand: List[Card]):
        self.hands.append((player_id, Hand(hand)))

    def log(self):
        print("Middle Deck:\n{}".format("\t".join(["   [{:14s}]    ".format(str(x)) for x in self.middle_deck.cards])))
        print("Betting Info:\tPlayer Id: {}\tScore: {}".format(self.bet.player_id, self.bet.bet))
        print("Hokm: {}\t\tGame Mode: {}".format(self.hokm_suit.name.title(), self.game_mode.name.title()))
        print("Hakem Saved Deck:\n{}\n\n".format("\t".join(["   [{:14s}]    ".format(str(x)) for x in self.saved_hand.cards])))
        for hand in self.hands:
            print(hand)

    def log_bet(self, bet: Bet):
        self.bet = bet

    def log_hokm(self, game_mode: GAMEMODE, hokm_suit: SUITS):
        self.game_mode = game_mode
        self.hokm_suit = hokm_suit

    def log_middle_deck(self, middle_deck: Deck):
        self.middle_deck = middle_deck

    def log_hakem_saved_hand(self, hand: Deck):
        self.saved_hand = hand
