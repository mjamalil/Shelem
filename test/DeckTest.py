import unittest

from dealer.Deck import Deck


class DeckTester(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()

    def testBuild(self):
        cards = self.deck.build_cards()
        self.assertEqual(len(cards), 52)
        self.deck.deal()
        self.assertEqual(self.deck.get_deck_score(), 165)

    def testDeal(self):
        playing_stacks = self.deck.deal()
        self.assertEqual(len(playing_stacks[0]), 12)
        self.assertEqual(len(playing_stacks[1]), 12)
        self.assertEqual(len(playing_stacks[2]), 12)
        self.assertEqual(len(playing_stacks[3]), 4)
        self.assertEqual(len(playing_stacks[4]), 12)
        ruler_hand = playing_stacks[2] + playing_stacks[3]
        self.assertEqual(len(ruler_hand), 16)
        ruler_hand2 = playing_stacks[2]
        ruler_hand2 += playing_stacks[3]
        self.assertEqual(len(ruler_hand2), 16)
        self.assertEqual(ruler_hand, ruler_hand2)
        self.assertNotEqual(ruler_hand2, playing_stacks[4])
