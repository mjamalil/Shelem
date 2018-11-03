import unittest

from dealer.Game import Game
from players.Player import Player
from players.RuleBasedPlayer import RuleBasedPlayer


class GameTester(unittest.TestCase):
    def setUp(self):
        self.game = Game([Player(0, 2), Player(1, 3), Player(2, 0), Player(3, 1)], True)

    # def testARound(self):
        # s1, s2 = self.game.play_a_round()
        # print("Round {}: Team 1 score = {} and Team 2 score = {}".format(0, s1, s2))

    @staticmethod
    def testRuleBasedPlayer():
        gme = Game([Player(0, 2), Player(1, 3), Player(2, 0), Player(3, 1)], False)
        s1, s2 = gme.play_a_round()
        # print("Round {}: Team 1 score = {} and Team 2 score = {}".format(0, s1, s2))

    @staticmethod
    def testRuleBasedPlayer2():
        return 
        gme = Game([RuleBasedPlayer(0, 2), Player(1, 3), RuleBasedPlayer(2, 0), Player(3, 1)], False)
        gme.begin_game()