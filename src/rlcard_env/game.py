from gym import spaces
from collections import deque
from typing import List

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Logging import Logging
from dealer.Utils import ThreeConsecutivePassesException, InvalidActionError
from players.Enum import NUMBER_OF_PARAMS, ACTION_SIZE, NUM_PLAYERS, GAMESTATE, SUITS, GAMEMODE, colors
from players.IntelligentPlayer import IntelligentPlayer, AgentPlayer
from players.Player import Player
from players.RuleBasedPlayer import RuleBasedPlayer


class ShelemGame:
    initialized = False

    metadata = {'render.modes': ['human']}

    def __init__(self, game_end: int = 1165, verbose: int = 0):
        # The game is always going to be the observation
        self.french_deck = Deck()
        self.players = None
        self.player_id_receiving_first_hand = 0
        self.logging = Logging()
        self.team_1_score = 0.0
        self.team_2_score = 0.0
        self.team_1_round_score = 0.0
        self.team_2_round_score = 0.0
        self.game_end_score = game_end
        self.verbose = verbose
        self.round_bets = []
        self.betting_players = None
        self.initially_passed_count = 0
        self.betting_rounds = 0
        self.round_counter = 1

        self.hakem = None
        self.round_middle_deck = None
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NOSUIT

        self.round_hands_played = []
        self.round_current_hand = []
        self.hand_winner = 0

        self.hand_first_player = 0
        self.current_player = 0
        self.hand_winner_card = None

        # self.observation_space = spaces.Discrete(52)
        self.observation_space = spaces.Box(low=0.0, high=1.0,  shape=(NUMBER_OF_PARAMS,))
        self.action_space = spaces.Discrete(ACTION_SIZE)
        self.reward_range = (-1, 1)

        self.game_state = GAMESTATE.READY_TO_START
        self.rewards = [0] * NUM_PLAYERS
        self.action_performed = False
        self.num_envs = 1
        self.set_players([
            AgentPlayer(0, 2),
            RuleBasedPlayer(1, 3),
            RuleBasedPlayer(2, 0),
            RuleBasedPlayer(3, 1)
        ])

    def reset(self):
        print()
        self.round_finished = False
        # self.round_counter = 1
        # self.team_1_score = 0.0
        # self.team_2_score = 0.0
        self.team_1_round_score = 0.0
        self.team_2_round_score = 0.0
        self.french_deck = Deck()
        # self.player_id_receiving_first_hand = 1
        self.game_state = GAMESTATE.READY_TO_START
        del self.round_bets[:]
        self.betting_players = None
        self.initially_passed_count = 0
        self.betting_rounds = 0
        self.hakem = None
        self.round_middle_deck = None
        del self.round_hands_played[:]
        del self.round_current_hand[:]
        self.hand_winner = 0
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NOSUIT
        self.hand_first_player = 0
        self.current_player = 0
        self.hand_winner_card = None
        self.initialized = True

        return self.step()

    def init_game(self):
        return self.reset()

    def set_players(self, players: List[Player]):
        self.players = players

    def get_current_player(self):
        if self.game_state == GAMESTATE.BIDDING:
            bp = self.betting_players.popleft()
            self.betting_players.appendleft(bp)
            return bp
        elif self.game_state == GAMESTATE.DECIDE_GAME_MODE or self.game_state == GAMESTATE.DECIDE_TRUMP \
                or self.game_state == GAMESTATE.WIDOWING:
            return self.hakem
        elif self.game_state == GAMESTATE.PLAYING_CARDS:
            return self.players[self.current_player]
        else:
            raise ValueError("No current player is defined for game state: {}".format(self.game_state))

    def step(self, action=None):
        if self.game_state == GAMESTATE.READY_TO_START:
            self.start_round()
            self.betting_players = deque(self.players)
            # the betting player should rotate
            for i in range(self.player_id_receiving_first_hand):
                self.betting_players.append(self.betting_players.popleft())
            self.initially_passed_count = 0
            self.betting_rounds = 0
            self.game_state = GAMESTATE.BIDDING
            return self.step(action)
        elif self.game_state == GAMESTATE.BIDDING:
            try:
                player_bet = self.get_next_bid(action)
            except ThreeConsecutivePassesException:
                self.game_state = GAMESTATE.READY_TO_START
                return self.step(action)
            if len(self.betting_players) == 1:
                self.game_state = GAMESTATE.DECIDE_GAME_MODE
            return self.step(action)
        elif self.game_state == GAMESTATE.DECIDE_GAME_MODE:
            self.decide_game_mode(action)
            self.game_state = GAMESTATE.DECIDE_TRUMP
            return self.step(action)
        elif self.game_state == GAMESTATE.DECIDE_TRUMP:
            self.decide_trump(action)
            self.game_state = GAMESTATE.PLAYING_CARDS
            if len(self.hakem.saved_deck) == NUM_PLAYERS:
                self.logging.log_hakem_saved_hand(Deck(self.hakem.saved_deck))
                self.hand_winner = self.hakem.player_id
                self.hand_first_player = self.hakem.player_id
                self.current_player = self.hakem.player_id
                self.round_current_hand = []
                self.hand_winner_card = None
                self.game_state = GAMESTATE.PLAYING_CARDS
            return self.step(action)
        elif self.game_state == GAMESTATE.WIDOWING:
            self.player_widow_card(action)
            return self.step(action)
        elif self.game_state == GAMESTATE.PLAYING_CARDS:
            if action is None:
                return self.players[self.current_player].game_state, self.current_player
            if len(self.round_hands_played) < 12:
                state, current_player = self.play_card(action)
            else:
                print(self.round_hands_played)
                raise RuntimeError("There should not be more than 12 hands!")
            if len(self.round_hands_played) == 12:
                self.end_round()
                self.game_state = GAMESTATE.READY_TO_START
                return self.step()
            return state, current_player
        else:
            raise ValueError("INVALID state {} in game state machine".format(self.game_state))

    def start_round(self):
        del self.round_bets[:]
        d1, d2, d3, self.round_middle_deck, d4 = self.french_deck.deal()
        self.logging.log_middle_deck(self.round_middle_deck)
        decks = deque([d1, d2, d3, d4])
        for _ in range(self.player_id_receiving_first_hand):
            decks.append(decks.popleft())
        for i in range(NUM_PLAYERS):
            self.players[i].begin_round(decks[i])

    def get_next_bid(self, action):
        if self.initially_passed_count == NUM_PLAYERS-1:
            self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % NUM_PLAYERS
            raise ThreeConsecutivePassesException("Three first players have passed, the game must re-init")
        bp = self.betting_players.popleft()
        # TODO implement make bet
        player_bet = bp.make_bet(self.round_bets)
        if len(self.round_bets) == 0 or (len(self.round_bets) > 0 and player_bet.bet > self.round_bets[-1].bet):
            self.round_bets.append(player_bet)
            self.betting_players.append(bp)
        elif player_bet.bet == 0 and 3 > self.betting_rounds == self.initially_passed_count:  # he has passed
            self.initially_passed_count += 1
            self.betting_rounds += 1
        return player_bet

    def decide_game_mode(self, action):
        self.hakem = self.betting_players.popleft()
        self.logging.log_bet(self.round_bets[-1])
        if not self.hakem.game_has_begun:
            raise ValueError("Game has not started yet")
        self.game_mode = self.hakem.decide_game_mode(self.round_middle_deck)

    def decide_trump(self, action):
        self.current_suit = self.hokm_suit = self.hakem.decide_trump()
        self.logging.log_hokm(self.game_mode, self.hokm_suit)
        for i in range(NUM_PLAYERS):
            self.players[i].set_hokm_and_game_mode(self.game_mode, self.hokm_suit)

    def player_widow_card(self, action):
        saving_index = self.hakem.decide_widow_card()
        new_deck = Deck([])
        for ind in range(len(self.hakem.deck)):
            if ind == saving_index:
                self.hakem.saved_deck += self.hakem.deck[ind]
            else:
                new_deck += self.hakem.deck[ind]
        self.hakem.deck = new_deck

    def play_card(self, action):
        if self.players[self.current_player].agent:
            self.observation = self.players[self.current_player].game_state
            if self.verbose >= 2:
                self.players[self.current_player].log_game_state()
            try:
                played_card = self.players[self.current_player].pop_card_from_deck(action, self.current_suit)
            except InvalidActionError:
                print("Invalid action: {}".format(action))
                raise RuntimeError("invalid action")
        else:
            played_card = self.players[self.current_player].play_a_card(self.round_current_hand, self.current_suit)

        if played_card.suit == self.hokm_suit:
            color = colors.FAIL
        else:
            color = colors.GREEN
        if self.verbose >= 2:
            print("{}{}-{}{}".format(color, self.current_player, played_card, colors.ENDC))
        self.round_current_hand.append(played_card)
        if self.current_suit == SUITS.NOSUIT:
            self.current_suit = played_card.suit
        for p in self.players:
            p.card_has_been_played(self.round_current_hand, self.current_suit)

        if self.hand_winner_card is None or Card.compare(self.hand_winner_card, played_card, self.game_mode, self.hokm_suit, self.current_suit) < 0:
            self.hand_winner_card = played_card
            self.hand_winner = self.current_player

        if len(self.round_current_hand) == NUM_PLAYERS:
            self.end_trick()
            self.current_player = self.hand_winner
        else:
            self.current_player = (self.current_player + 1) % NUM_PLAYERS
        return self.players[self.current_player].game_state, self.current_player

    def end_trick(self):
        if self.verbose >= 2:
            separator = "*" * 40
            print("{}{}{}".format(colors.BLUE, separator, colors.ENDC))
        self.round_hands_played.append(self.round_current_hand)
        self.logging.add_hand(self.hand_first_player, self.round_current_hand)
        for p in self.players:
            p.win_trick(self.round_current_hand, self.hand_winner)
        if self.hand_winner in [0, 2]:
            self.rewards[0] = Deck(self.round_current_hand).get_deck_score() / 165
        else:
            self.rewards[0] = 0
        self.hand_first_player = self.hand_winner
        self.round_current_hand = []
        self.current_suit = SUITS.NOSUIT
        self.hand_winner_card = None

    def end_round(self):
        self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % NUM_PLAYERS
        self.team_1_round_score = (self.players[0].saved_deck + self.players[2].saved_deck).get_deck_score()
        self.team_2_round_score = (self.players[1].saved_deck + self.players[3].saved_deck).get_deck_score()
        self.rewards[0] = self.get_round_reward(self.hakem.player_id, self.team_1_round_score, self.team_2_round_score, 0)
        self.french_deck = self.players[0].saved_deck + self.players[2].saved_deck + \
                           self.players[1].saved_deck + self.players[3].saved_deck
        final_bet = self.round_bets[-1]
        team1_has_bet = final_bet.id == 0 or final_bet.id == 2
        if (team1_has_bet and self.team_1_round_score >= final_bet.bet) or \
                (not team1_has_bet and self.team_2_round_score >= final_bet.bet):
            if team1_has_bet:
                s1, s2 = final_bet.bet, self.team_2_round_score
            else:
                s1, s2 = self.team_1_round_score, final_bet.bet
        elif (team1_has_bet and self.team_2_round_score < 85) or (not team1_has_bet and self.team_1_round_score < 85):
            if team1_has_bet:
                s1, s2 = -final_bet.bet, self.team_2_round_score
            else:
                s1, s2 = self.team_1_round_score, -final_bet.bet
        elif team1_has_bet:
            s1, s2 = -2 * final_bet.bet, self.team_2_round_score
        else:
            s1, s2 = self.team_1_round_score, -2 * final_bet.bet
        self.team_1_score += s1
        self.team_2_score += s2
        print("{}Round {}: Team 1 score = {} ({}) and Team 2 score = {} ({}){}".format(
            colors.WARNING, self.round_counter, s1, self.team_1_score, s2, self.team_2_score, colors.ENDC))
        self.round_counter += 1
        if self.check_game_finished():
            print("{}Final Scores = Team 1 score = {} and Team 2 score = {}{}".format(
                colors.CYAN, self.team_1_score, self.team_2_score, colors.ENDC))
        self.round_hands_played.clear()
        self.round_finished = True

    def check_game_finished(self):
        if self.game_end_score == 0:
            return False
        if self.team_1_score >= self.game_end_score or self.team_1_score - self.team_2_score >= self.game_end_score:
            return True
        elif self.team_2_score >= self.game_end_score or self.team_2_score - self.team_1_score >= self.game_end_score:
            return True
        return False

    def get_round_reward(self, hakem_id: int, team1_score: int, team2_score: int, last_reward):
        if hakem_id in [0, 2]:
            if team1_score == 165:
                round_reward = 1.0
            elif team1_score >= self.round_bets[-1].bet:
                round_reward = 0.5
            elif team1_score > 80:
                round_reward = -0.7
            else:
                round_reward = -1.0
        else:
            if team2_score == 165:
                round_reward = 0.0
            elif team2_score >= self.round_bets[-1].bet:
                round_reward = 0.0
            elif team2_score > 80:
                round_reward = 0.5
            else:
                round_reward = 1.0

        round_reward += last_reward
        if round_reward > 1.0:
            round_reward = 1.0
        elif round_reward < -1.0:
            round_reward = -1.0
        return round_reward

    def get_state(self, player_id):
        """ Return player's state
        Args:
            player_id (int): player id
        Returns:
            (dict): The state of the player
        """
        return self.players[self.current_player].game_state

    def get_payoffs(self):
        """ Return the payoffs of the game
        Returns:
            (list): Each entry corresponds to the payoff of one player
        """
        return self.rewards

    def get_legal_actions(self):
        """ Return the legal actions for current player
        Returns:
            (list): A list of legal actions
        """

        return self.players[self.current_player].get_legal_actions(self.current_suit)

    def get_num_players(self):
        return NUM_PLAYERS

    @staticmethod
    def get_num_actions():
        """ Return the number of applicable actions
        Returns:
            (int): The number of actions. There are 61 actions
        """
        return 52

    def get_player_id(self):
        """ Return the current player's id
        Returns:
            (int): current player's id
        """
        return self.current_player

    def is_over(self):
        """ Check if the game is over
        Returns:
            (boolean): True if the game is over
        """
        return self.round_finished
        return self.check_game_finished()
