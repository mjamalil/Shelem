import unittest

from dealer.Game import Game


class GameTester(unittest.TestCase):
    def setUp(self):
        self.game = Game(True)

    def testARound(self):
        s1, s2 = self.game.play_a_round()
        print("Round {}: Team 1 score = {} and Team 2 score = {}".format(0, s1, s2))