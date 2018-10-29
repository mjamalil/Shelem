import unittest

from dealer.Card import Card
from dealer.Utils import VALUES, SUITS, GAMEMODE


class CardTester(unittest.TestCase):
    def setUp(self):
        pass

    def testComparison(self):
        game_mode = GAMEMODE.NARAS
        card1 = Card(VALUES.ACE, SUITS.SPADES)
        card2 = Card(VALUES.TWO, SUITS.SPADES)
        self.assertEqual(card1.compare(card2, hokm_suit=SUITS.NEITHER, game_mode=game_mode), -1)
        self.assertEqual(card2.compare(card1, hokm_suit=SUITS.NEITHER, game_mode=game_mode), 1)
        game_mode = GAMEMODE.SARAS
        card1 = Card(VALUES.ACE, SUITS.SPADES)
        card2 = Card(VALUES.TWO, SUITS.SPADES)
        self.assertEqual(card1.compare(card2, hokm_suit=SUITS.NEITHER, game_mode=game_mode), 1)
        self.assertEqual(card2.compare(card1, hokm_suit=SUITS.NEITHER, game_mode=game_mode), -1)
        game_mode = GAMEMODE.SARAS
        card1 = Card(VALUES.THREE, SUITS.SPADES)
        card2 = Card(VALUES.KING, SUITS.HEARTS)
        self.assertEqual(card1.compare(card2, hokm_suit=SUITS.NEITHER, game_mode=game_mode), 1)
        self.assertEqual(card2.compare(card1, hokm_suit=SUITS.NEITHER, game_mode=game_mode), 1)
        game_mode = GAMEMODE.NORMAL
        card1 = Card(VALUES.THREE, SUITS.SPADES)
        card2 = Card(VALUES.KING, SUITS.HEARTS)
        self.assertEqual(card1.compare(card2, hokm_suit=SUITS.SPADES, game_mode=game_mode), 1)
        self.assertEqual(card2.compare(card1, hokm_suit=SUITS.SPADES, game_mode=game_mode), -1)
