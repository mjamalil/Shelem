from collections import deque
from typing import Tuple, List

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Logging import Logging
from players.Enum import NUM_PLAYERS, SUITS, colors
from players.IntelligentPlayer import PPOPlayer
from players.Player import Player
from players.RuleBasedPlayer import RuleBasedPlayer

training = True
benchmark_rounds = 100000

class Game:

    def __init__(self, players: List[Player], verbose: bool = False):
        self.game_end = 1165
        self.limit_game_number = 0
        self.french_deck = Deck()
        self.players = players
        self.player_id_receiving_first_hand = 0
        self.team_1_score = 0
        self.team_2_score = 0
        self.verbose = verbose
        self.logging = Logging()

    @staticmethod
    def check_card_validity(player: Player, card: Card, suit: SUITS):
        if suit == SUITS.NOSUIT or card.suit == suit:
            return True
        for c in player.deck.cards:
            if c.suit == suit:
                return False
        return True

    def play_a_round(self) -> Tuple[int, int]:
        # the last three number shows game mode, trump_suit, current_suit
        d1, d2, d3, middle_deck, d4 = self.french_deck.deal()
        self.logging.log_middle_deck(middle_deck)
        decks = deque([d1, d2, d3, d4])
        # give the first deck to the next player
        for _ in range(self.player_id_receiving_first_hand):
            decks.append(decks.popleft())

        for i in range(NUM_PLAYERS):
            self.players[i].begin_round(decks[i])

        # betting phase
        betting_players = deque(self.players)
        # the betting player should rotate
        for i in range(self.player_id_receiving_first_hand):
            betting_players.append(betting_players.popleft())
        initially_passed_count = 0
        betting_rounds = 0
        last_bets = []
        while len(betting_players) > 1:
            if initially_passed_count == 3:
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
        self.hakem_id = hakem.player_id
        self.logging.log_bet(last_bets[-1])

        # Leader selecting the trump suit
        game_mode = hakem.decide_game_mode(middle_deck)
        hokm_suit = hakem.decide_trump()
        for i in range(NUM_PLAYERS):
            self.players[i].hokm_has_been_determined(game_mode, hokm_suit, last_bets[-1])
        self.logging.log_hakem_saved_hand(Deck(hakem.saved_deck))
        self.logging.log_hokm(game_mode, hokm_suit)
        # print(game_mode, hokm_suit)
        for i in range(NUM_PLAYERS):
            self.players[i].set_hokm_and_game_mode(game_mode, hokm_suit)

        # card play phase
        hands_played = []
        last_winner_id = self.hakem_id
        current_suit = hokm_suit
        for i in range(12):
            first_player = last_winner_id
            current_player_id = last_winner_id
            current_hand = []
            winner_card = None
            print("="*40)

            for _ in range(NUM_PLAYERS):
                played_card = self.players[current_player_id].play_a_card(current_hand, current_suit)
                valid_card = self.check_card_validity(self.players[current_player_id], played_card, current_suit)
                if not valid_card:
                    raise RuntimeError("Player {} played invalid card {}".format(current_player_id, played_card))
                if played_card.suit == hokm_suit:
                    color = colors.FAIL
                else:
                    color = colors.GREEN
                print(f"{color}Player{current_player_id}-> {played_card}{colors.ENDC}")
                for j in range(NUM_PLAYERS):
                    self.players[j].card_has_been_played(current_hand, current_suit)

                current_hand.append(played_card)
                if winner_card:
                    if Card.compare(winner_card, played_card, game_mode, hokm_suit, current_suit) < 0:
                        last_winner_id = current_player_id
                        winner_card = played_card
                else:
                    last_winner_id = current_player_id
                    winner_card = played_card
                    current_suit = played_card.suit
                current_player_id = (current_player_id + 1) % 4
            hands_played.append(current_hand)
            current_suit = SUITS.NOSUIT
            self.logging.add_hand(first_player, current_hand)

            for i in range(NUM_PLAYERS):
                self.players[i].win_trick(current_hand, last_winner_id)

        self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % 4

        self.french_deck = self.players[0].saved_deck + self.players[2].saved_deck + \
            self.players[1].saved_deck + self.players[3].saved_deck
        return self.calculate_round_score(last_bets)

    def calculate_round_score(self, last_bets):
        team1_score = (self.players[0].saved_deck + self.players[2].saved_deck).get_deck_score()
        team2_score = (self.players[1].saved_deck + self.players[3].saved_deck).get_deck_score()
        final_bet = last_bets[-1]
        team1_has_bet = final_bet.id == 0 or final_bet.id == 2
        if self.verbose:
            self.logging.log()

        if (team1_has_bet and team1_score >= final_bet.bet) or (not team1_has_bet and team2_score >= final_bet.bet):
            if team1_has_bet:
                result = final_bet.bet, team2_score
            else:
                result = team1_score, final_bet.bet
        elif (team1_has_bet and team2_score < 85) or (not team1_has_bet and team1_score < 85):
            if team1_has_bet:
                result = -final_bet.bet, team2_score
            else:
                result = team1_score, -final_bet.bet
        elif team1_has_bet:
            result = -2 * final_bet.bet, team2_score
        else:
            result = team1_score, -2 * final_bet.bet
        for i in range(4):
            self.players[i].end_round(self.hakem_id, team1_score, team2_score)
        return result

    def begin_game(self):
        self.round_counter = 1
        while not self.check_game_finished():
            s1, s2 = self.play_a_round()
            if not training or self.round_counter > benchmark_rounds:
                self.team_1_score += s1
                self.team_2_score += s2
            print("{}Round {:04d}: H:{} Team 1 score = {:04d} ({:04d}) and Team 2 score = {:04d} ({:04d}){}".format(
                colors.WARNING, self.round_counter, self.hakem_id, s1, self.team_1_score, s2, self.team_2_score, colors.ENDC))
            self.round_counter += 1
        self.finish_game()

    def finish_game(self):
        print("*" * 100)
        print("{}Final Scores = Team 1 score = {} and Team 2 score = {}{}".format(
            colors.CYAN, self.team_1_score, self.team_2_score, colors.ENDC))
        self.players[0].print_game_stat()

    def check_game_finished(self):
        if self.limit_game_number > 0:
            if self.round_counter > self.limit_game_number:
                return True
            return False
        if self.team_1_score >= self.game_end or self.team_1_score - self.team_2_score >= self.game_end:
            return True
        elif self.team_2_score >= self.game_end or self.team_2_score - self.team_1_score >= self.game_end:
            return True
        return False


if __name__ == '__main__':
    Game([PPOPlayer(0, 2), RuleBasedPlayer(1, 3), RuleBasedPlayer(2, 0), RuleBasedPlayer(3, 1)]).begin_game()
