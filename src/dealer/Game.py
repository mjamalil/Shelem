from typing import Tuple, List

from collections import deque

from dealer.Deck import Deck
from dealer.Logging import Logging
from players.Player import Player

number_of_params = 71
NOT_SET = 255
class Game:
    NUM_PLAYERS = 4

    def __init__(self, players: List[Player], verbose: bool = False):
        self.game_end = 10
        self.french_deck = Deck()
        self.players = players
        self.player_id_receiving_first_hand = 0
        self.team_1_score = 0
        self.team_2_score = 0
        self.verbose = verbose
        self.logging = Logging()
        # a series of values storing all data of a round
        self.game_state = [NOT_SET] * number_of_params

    def play_a_round(self) -> Tuple[int, int]:
        self.game_state = [NOT_SET] * number_of_params
        d1, d2, d3, middle_deck, d4 = self.french_deck.deal()
        self.logging.log_middle_deck(middle_deck)
        decks = deque([d1, d2, d3, d4])
        for _ in range(self.player_id_receiving_first_hand):
            decks.append(decks.popleft())
        for i in range(4):
            self.players[i].begin_game(decks[i])

        # betting phase
        betting_players = deque(self.players)
        initially_passed_count = 0
        betting_rounds = 0
        last_bets = []
        while len(betting_players) > 1:
            if initially_passed_count == 3:
                # raise RuntimeError("Three first players have passed, the game must re-init")
                self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % 4
                self.play_a_round()
            bp = betting_players.popleft()
            player_bet = bp.make_bet(last_bets)
            if len(last_bets) == 0 or (len(last_bets) > 0 and player_bet.bet > last_bets[-1].bet):
                last_bets.append(player_bet)
                betting_players.append(bp)
            elif player_bet.bet == 0 and 3 > betting_rounds == initially_passed_count:  # he has passed
                initially_passed_count += 1
                betting_rounds += 1
        hakem = betting_players.popleft()
        hakem_id = hakem.player_id
        self.logging.log_bet(last_bets[-1])

        # Leader selecting the trump suit
        game_mode, hokm_suit = hakem.make_hakem(middle_deck)
        self.logging.log_hakem_saved_hand(Deck(hakem.saved_deck))
        self.logging.log_hokm(game_mode, hokm_suit)
        for i in range(4):
            self.players[i].set_hokm_and_game_mode(game_mode, hokm_suit)

        # card play phase
        hands_played = []
        last_winner_id = hakem_id

        for i in range(12):
            first_player = last_winner_id
            current_player_id = last_winner_id
            current_hand = []
            winner_card = None
            for _ in range(4):
                played_card = self.players[current_player_id].play_a_card(hands_played, current_hand)
                self.game_state[i * self.NUM_PLAYERS + current_player_id] = played_card.id
                current_hand.append(played_card)
                if winner_card:
                    if winner_card.compare(played_card, game_mode, hokm_suit) == -1:
                        last_winner_id = current_player_id
                        winner_card = played_card
                else:
                    last_winner_id = current_player_id
                    winner_card = played_card
                current_player_id = (current_player_id + 1) % 4
            hands_played.append(current_hand)
            self.logging.add_hand(first_player, current_hand)
            self.players[last_winner_id].win_trick(current_hand)
            # for _ in range(4):
            #     self.players

        self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % 4
        team1_score = (self.players[0].saved_deck + self.players[2].saved_deck).get_deck_score()
        team2_score = (self.players[1].saved_deck + self.players[3].saved_deck).get_deck_score()
        self.french_deck = self.players[0].saved_deck + self.players[2].saved_deck + \
            self.players[1].saved_deck + self.players[3].saved_deck

        # calculate round score
        final_bet = last_bets[-1]
        team1_has_bet = final_bet.id == 0 or final_bet.id == 2
        if self.verbose:
            self.logging.log()
        if (team1_has_bet and team1_score >= final_bet.bet) or (not team1_has_bet and team2_score >= final_bet.bet):
            if team1_has_bet:
                return final_bet.bet, team2_score
            else:
                return team1_score, final_bet.bet
        elif (team1_has_bet and team2_score < 85) or (not team1_has_bet and team1_score < 85):
            if team1_has_bet:
                return -final_bet.bet, team2_score
            else:
                return team1_score, -final_bet.bet
        elif team1_has_bet:
            return -2 * final_bet.bet, team2_score
        else:
            return team1_score, -2 * final_bet.bet

    def begin_game(self):
        round_counter = 1
        while not self.check_game_finished():
            s1, s2 = self.play_a_round()
            self.team_1_score += s1
            self.team_2_score += s2
            print("Round {}: Team 1 score = {} and Team 2 score = {}".format(round_counter, s1, s2))
            round_counter += 1
        print("Final Scores = Team 1 score = {} and Team 2 score = {}".format(self.team_1_score, self.team_2_score))

    def check_game_finished(self):
        if self.team_1_score >= self.game_end or self.team_1_score - self.team_2_score >= self.game_end:
            return True
        elif self.team_2_score >= self.game_end or self.team_2_score - self.team_1_score >= self.game_end:
            return True
        return False


if __name__ == '__main__':
    Game([Player(0, 2), Player(1, 3), Player(2, 0), Player(3, 1)]).begin_game()






