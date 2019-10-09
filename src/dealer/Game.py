from typing import Tuple, List
from collections import deque

from dealer.Deck import Deck
from dealer.Logging import Logging
from dealer.Utils import GameConfig
from players.Player import Player
from players.RuleBasedPlayer import RuleBasedPlayer

FULL_SCORE = 165


class Game:
    def __init__(self, players: List[Player], verbose: bool = False):
        self.french_deck = Deck()
        self.players = players
        self.player_id_receiving_first_hand = 0
        self.team_1_score = 0
        self.team_2_score = 0
        self.verbose = verbose
        self.logging = Logging()

    def play_a_round(self) -> Tuple[int, int]:
        d1, d2, d3, middle_deck, d4 = self.french_deck.deal()
        self.logging.log_middle_deck(middle_deck)
        decks = deque([d1, d2, d3, d4])
        for _ in range(self.player_id_receiving_first_hand):
            decks.append(decks.popleft())
        for i in range(4):
            self.players[i].begin_game(decks[i])
        betting_players = deque(self.players)
        initially_passed_count = 0
        last_bets = []
        potential_rematch = True
        while len(betting_players) > 1:
            if initially_passed_count == 3:
                # Three consecutive pass the game must re-init
                self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % 4
                self.play_a_round()
            bp = betting_players.popleft()
            player_bet = bp.ask2bet(last_bets)

            if player_bet.bet and (len(last_bets) == 0 or player_bet.bet > last_bets[-1].bet):
                last_bets.append(player_bet)
                betting_players.append(bp)
                potential_rematch = False
            if potential_rematch:
                initially_passed_count += 1
        hakem = betting_players.popleft()
        last_winner_id = hakem.player_id
        self.logging.log_bet(last_bets[-1])
        GameConfig.game_mode, GameConfig.hokm_suit = hakem.make_hakem(middle_deck)
        self.logging.log_hakem_saved_hand(Deck(hakem.saved_deck))
        self.logging.log_hokm(GameConfig.game_mode, GameConfig.hokm_suit)
        for i in range(4):
            self.players[i].set_hokm_and_game_mode(GameConfig.game_mode, GameConfig.hokm_suit)
            self.players[i].sort_cards()
        hands_played = []
        for i in range(12):
            first_player = last_winner_id
            next_player_id = last_winner_id
            current_hand = []
            winner_card = self.players[next_player_id].play_a_card(hands_played, current_hand)
            self.players[next_player_id].check_played_card(winner_card, current_hand, i == 0)
            current_hand.append(winner_card)
            # players playing a card
            for _ in range(3):
                next_player_id = (next_player_id + 1) % 4
                played_card = self.players[next_player_id].play_a_card(hands_played, current_hand)
                self.players[next_player_id].check_played_card(played_card, current_hand)
                current_hand.append(played_card)
                # if played_card.is_greater(winner_card, game_mode, hokm_suit):
                if played_card > winner_card:
                    last_winner_id = next_player_id
                    winner_card = played_card
            hands_played.append(current_hand)
            self.logging.add_hand(first_player, current_hand)
            self.players[last_winner_id].store_hand(current_hand)
        self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % 4
        team1_score = (self.players[0].saved_deck + self.players[2].saved_deck).get_deck_score()
        team2_score = (self.players[1].saved_deck + self.players[3].saved_deck).get_deck_score()
        self.french_deck = self.players[0].saved_deck + self.players[2].saved_deck + \
                           self.players[1].saved_deck + self.players[3].saved_deck
        if len(self.french_deck) < 52:
            for i in range(4):
                print("cards in player{}'s hand:{}".format(
                    i, len(self.players[i].saved_deck)))
            raise ValueError("Not enough cards in deck to shuffle and deal!")
        final_bet = last_bets[-1]
        team1_has_bet = final_bet.id == 0 or final_bet.id == 2
        if self.verbose:
            self.logging.log()
        if team1_score == FULL_SCORE:
            return '1', final_bet.bet, 2 * final_bet.bet, team2_score
        elif team2_score == FULL_SCORE:
            return '2', final_bet.bet, team2_score, 2 * final_bet.bet
        elif (team1_has_bet and team1_score >= final_bet.bet) or (not team1_has_bet and team2_score >= final_bet.bet):
            if team1_has_bet:
                return '1', final_bet.bet, final_bet.bet, team2_score
            else:
                return '2', final_bet.bet, team1_score, final_bet.bet
        elif (team1_has_bet and team2_score < 85) or (not team1_has_bet and team1_score < 85):
            if team1_has_bet:
                return '1', final_bet.bet, -final_bet.bet, team2_score
            else:
                return '2', final_bet.bet, team1_score, -final_bet.bet
        elif team1_has_bet:
            return '1', final_bet.bet, -2 * final_bet.bet, team2_score
        else:
            return '2', final_bet.bet, team1_score, -2 * final_bet.bet

    def begin_game(self):
        round_counter = 1
        while not self.check_game_finished():
            team, bet, score1, score2 = self.play_a_round()
            self.team_1_score += score1
            self.team_2_score += score2
            print("Round {}: Team {} has bet {:d} and Team 1:{} and Team 2:{}".format(
                str(round_counter).rjust(3, ' '), team, bet, str(score1).rjust(4, ' '), str(score2).rjust(4, ' ')))
            round_counter += 1
        print("Final Scores = Team 1 score = {} and Team 2 score = {}".format(self.team_1_score, self.team_2_score))

    def check_game_finished(self):
        if self.team_1_score >= 1165 or self.team_1_score - self.team_2_score >= 1165:
            return True
        elif self.team_2_score >= 1165 or self.team_2_score - self.team_1_score >= 1165:
            return True
        return False


if __name__ == '__main__':
    new_game = Game([RuleBasedPlayer(0, 2), Player(1, 3), RuleBasedPlayer(2, 0), Player(3, 1)])
    new_game.begin_game()
# Game([RuleBasedPlayer(0, 2), RuleBasedPlayer(1, 3), RuleBasedPlayer(2, 0), RuleBasedPlayer(3, 1)]).begin_game()
