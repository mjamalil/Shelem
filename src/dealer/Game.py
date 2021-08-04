from collections import deque
from typing import Tuple, List

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Logging import Logging
from dealer.Utils import get_round_payoff
from players.Enum import NUM_PLAYERS, SUITS, colors
from players.IntelligentPlayer import PPOPlayer, IntelligentPlayer
from players.Player import Player
from players.RuleBasedPlayer import RuleBasedPlayer

training = True


class Game:

    def __init__(self, players: List[Player]):
        self.game_end = 1165
        self.random_play = 2000
        self.limit_game_number = 2000
        self.benchmark_rounds = 0
        self.french_deck = Deck()
        self.players = players
        self.player_id_receiving_first_hand = 0
        self.team_1_score = 0
        self.team_2_score = 0

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

        # Leader selecting the trump suit
        game_mode = hakem.decide_game_mode(middle_deck)
        hokm_suit = hakem.decide_trump()
        for i in range(NUM_PLAYERS):
            self.players[i].hokm_has_been_determined(game_mode, hokm_suit, last_bets[-1])
        for i in range(NUM_PLAYERS):
            self.players[i].set_hokm_and_game_mode(game_mode, hokm_suit, hakem.player_id)

        # card play phase
        hands_played = []
        last_winner_id = self.hakem_id
        current_suit = hokm_suit
        for i in range(12):
            current_player_id = last_winner_id
            current_hand = []
            winner_card = None
            Logging.debug("="*40)

            for _ in range(NUM_PLAYERS):
                if self.round_counter < self.random_play and current_player_id != 0:
                    played_card = self.players[current_player_id].play_random_card(current_hand, current_suit)
                else:
                    played_card = self.players[current_player_id].play_a_card(current_hand, current_suit)
                valid_card = self.check_card_validity(self.players[current_player_id], played_card, current_suit)
                if not valid_card:
                    raise RuntimeError("Player {} played invalid card {}".format(current_player_id, played_card))

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

                if played_card.suit == hokm_suit:
                    color = colors.RED
                elif played_card.suit == current_suit:
                    color = colors.GREEN
                else:
                    color = colors.BROWN
                Logging.debug(f"{color}Player{current_player_id}-> {played_card}{colors.ENDC}")

                current_player_id = (current_player_id + 1) % 4

            hands_played.append(current_hand)
            current_suit = SUITS.NOSUIT

            for k in range(NUM_PLAYERS):
                self.players[k].end_trick(current_hand, last_winner_id)

        self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % 4

        self.french_deck = self.players[0].saved_deck + self.players[2].saved_deck + \
            self.players[1].saved_deck + self.players[3].saved_deck
        return self.calculate_round_score(last_bets)

    def calculate_round_score(self, last_bets):
        team1_score = (self.players[0].saved_deck + self.players[2].saved_deck).get_deck_score()
        team2_score = (self.players[1].saved_deck + self.players[3].saved_deck).get_deck_score()
        final_bet = last_bets[-1]
        for i in range(4):
            self.players[i].end_round(self.hakem_id, team1_score, team2_score)

        final_score1, final_score2, reward = get_round_payoff(self.hakem_id, final_bet.bet, team1_score, team2_score)
        return final_score1, final_score2

    def begin_game(self):
        self.round_counter = 1
        while not self.check_game_finished():
            s1, s2 = self.play_a_round()
            if not training or self.round_counter > self.benchmark_rounds:
                self.team_1_score += s1
                self.team_2_score += s2
            Logging.info("{}Round {:04d}: H:{} Team 1 score = {:04d} ({:04d}) and Team 2 score = {:04d} ({:04d}){}".format(
                colors.BLUE, self.round_counter, self.hakem_id, s1, self.team_1_score, s2, self.team_2_score, colors.ENDC))
            self.round_counter += 1
        self.finish_game()

    def finish_game(self):
        Logging.debug("*" * 100)
        Logging.important("{}Final Scores = Team 1 score = {} and Team 2 score = {}{}".format(
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
    players = [PPOPlayer(0, 2), IntelligentPlayer(1, 3), IntelligentPlayer(2, 0), IntelligentPlayer(3, 1)]
    Game(players).begin_game()
