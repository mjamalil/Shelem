import unittest

from players.Player import Bet

from dealer.Deck import Deck
from players.IntelligentPlayer import IntelligentPlayer


class IntelligentPlayerTest(unittest.TestCase):
    def setUp(self):
        self.french_deck = Deck()
        self.player = IntelligentPlayer(0, 2)
        d1, d2, d3, middle_deck, d4 = self.french_deck.deal()
        self.player.begin_game(d1)

    def testEncode(self):
        all_bets = [Bet(0, 100), Bet(1, 110), Bet(2, 0), Bet(3, 130)]
        self.player.encode_last_bets(all_bets)
