import gym
from gym import spaces
# from gym import error, utils
# from gym.utils import seeding
from collections import deque
from typing import List

from dealer.Deck import Deck
from dealer.Logging import Logging
from dealer.Utils import GAMESTATE, GAMEMODE, SUITS
from players.IntelligentPlayer import IntelligentPlayer
from players.Player import Player

from policies.policy_dqn import ShelemPolicyDQN


class ThreeConsecutivePassesException(Exception):
    def __init__(self, message):
        super().__init__(message)


class ShelemEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, verbose: bool = False):
        # The game is always going to be the observation
        self.french_deck = Deck()
        self.players = None
        self.player_id_receiving_first_hand = 0
        self.logging = Logging()
        self.team_1_score = 0.0
        self.team_2_score = 0.0
        self.team_1_round_score = 0.0
        self.team_2_round_score = 0.0
        self.verbose = verbose
        self.round_bets = []
        self.betting_players = None
        self.initially_passed_count = 0
        self.betting_rounds = 0
        self.round_counter = 1

        self.hakem = None
        self.round_middle_deck = None
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NEITHER

        self.round_hands_played = []
        self.round_current_hand = []
        self.last_hand_winner_id = 0

        self.hand_first_player = 0
        self.hand_next_player_id = 0
        self.hand_winner_card = None

        self.observation_space = spaces.Discrete(52)
        self.action_space = spaces.Tuple((spaces.Discrete(17), spaces.Discrete(52), spaces.Discrete(52),  spaces.Discrete(4), spaces.Discrete(3)))

        self.optimization_policy = ShelemPolicyDQN()
        self.game_state = GAMESTATE.READY_TO_START

    def set_players(self, players: List[Player]):
        self.players = players

    def select_action(self):
        return self.optimization_policy.select_action(self.game_state, self.get_current_player().deck)

    def get_current_player(self):
        if self.game_state == GAMESTATE.BIDDING:
            bp = self.betting_players.popleft()
            self.betting_players.appendleft(bp)
            return bp
        elif self.game_state == GAMESTATE.DECIDE_GAME_MODE or self.game_state == GAMESTATE.DECIDE_TRUMP or self.game_state == GAMESTATE.WIDOWING:
            return self.hakem
        elif self.game_state == GAMESTATE.PLAYING_CARDS:
            return self.players[self.hand_next_player_id]
        else:
            raise ValueError("No current player is defined for game state: {}".format(self.game_state))

    def step(self, action):
        """assert self.action_space.contains(action)
        self.path.append(action)
        done = False
        if len(self.path) > 10:
            done = True
        if sum(self.path) % 2 == 0:  # hit: add a card to players hand and return
            reward = 0.0
        else:
            reward = 1.0
        return sum(self.path) % 2, reward, done, {}"""
        if self.game_state == GAMESTATE.READY_TO_START:
            self.start_round()
            self.betting_players = deque(self.players)
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
            # TODO what should be the reward in here?
            reward = 0
            return (GAMESTATE.BIDDING, player_bet.bet), reward, False, {}
        elif self.game_state == GAMESTATE.DECIDE_GAME_MODE:
            self.decide_game_mode(action)
            self.game_state = GAMESTATE.DECIDE_TRUMP
            reward = 0
            return (GAMESTATE.DECIDE_GAME_MODE, self.game_mode.value), reward, False, {}
        elif self.game_state == GAMESTATE.DECIDE_TRUMP:
            self.decide_trump(action)
            self.game_state = GAMESTATE.WIDOWING
            reward = 0
            return (GAMESTATE.DECIDE_TRUMP, self.hokm_suit.value), reward, False, {}
        elif self.game_state == GAMESTATE.WIDOWING:
            self.player_widow_card(action)
            if len(self.hakem.saved_deck) == 4:
                self.logging.log_hakem_saved_hand(Deck(self.hakem.saved_deck))
                self.last_hand_winner_id = self.hakem.player_id
                self.hand_first_player = self.last_hand_winner_id
                self.hand_next_player_id = self.last_hand_winner_id
                self.round_current_hand = []
                self.hand_winner_card = None
                self.game_state = GAMESTATE.PLAYING_CARDS
            # TODO what should be the reward in here?
            reward = 0
            return (GAMESTATE.WIDOWING, self.game_mode.value), reward, False, {}
        elif self.game_state == GAMESTATE.PLAYING_CARDS:
            if len(self.round_hands_played) < 12:
                self.play_card(action)
            else:
                raise ValueError("There should not be more than 12 hands!")
            # TODO what should be the reward in here?
            reward = 0
            if len(self.round_hands_played) == 12:
                self.end_round()
                self.game_state = GAMESTATE.READY_TO_START
                return (GAMESTATE.PLAYING_CARDS, self.game_mode.value), reward, True, {}
            return (GAMESTATE.PLAYING_CARDS, self.game_mode.value), reward, False, {}
        else:
            raise ValueError("INVALID state {} in game state machine".format(self.game_state))

    def start_round(self):
        del self.round_bets[:]
        d1, d2, d3, self.round_middle_deck, d4 = self.french_deck.deal()
        self.logging.log_middle_deck(self.round_middle_deck)
        decks = deque([d1, d2, d3, d4])
        for _ in range(self.player_id_receiving_first_hand):
            decks.append(decks.popleft())
        for i in range(4):
            self.players[i].begin_game(decks[i])

    def get_next_bid(self, action):
        if self.initially_passed_count == 3:
            # raise RuntimeError("Three first players have passed, the game must re-init")
            self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % 4
            raise ThreeConsecutivePassesException("Three first players have passed, the game must re-init")
        bp = self.betting_players.popleft()
        # TODO implement make bet
        player_bet = bp.make_bet(self.round_bets)
        p_action, p_bet = self.select_action()
        p_bet.player_id = bp.player_id
        print(p_bet)
        if len(self.round_bets) == 0 or (len(self.round_bets) > 0 and player_bet.bet > self.round_bets[-1].bet):
            self.round_bets.append(player_bet)
            self.betting_players.append(bp)
        elif player_bet.bet == 0 and 3 > self.betting_rounds == self.initially_passed_count:  # he has passed
            self.initially_passed_count += 1
            self.betting_rounds += 1
        return player_bet

    def decide_trump(self, action):
        self.hokm_suit = self.hakem.decide_trump()
        self.logging.log_hokm(self.game_mode, self.hokm_suit)
        for i in range(4):
            self.players[i].set_hokm_and_game_mode(self.game_mode, self.hokm_suit)
        p_action, p_trump = self.select_action()
        print(p_trump)

    def decide_game_mode(self, action):
        self.hakem = self.betting_players.popleft()
        self.logging.log_bet(self.round_bets[-1])
        if not self.hakem.game_has_begun:
            raise ValueError("Game has not started yet")
        self.hakem.is_hakem = True
        self.hakem.deck += self.round_middle_deck
        self.game_mode = self.hakem.decide_game_mode()
        p_action, p_game_mode = self.select_action()
        print(p_game_mode)

    def player_widow_card(self, action):
        saving_index = self.hakem.decide_widow_card()
        new_deck = Deck([])
        for ind in range(len(self.hakem.deck)):
            if ind == saving_index:
                self.hakem.saved_deck += self.hakem.deck[ind]
            else:
                new_deck += self.hakem.deck[ind]
        self.hakem.deck = new_deck
        p_action, p_card = self.select_action()
        print(p_card)

    def play_card(self, action):
        played_card = self.players[self.hand_next_player_id].play_a_card(self.round_hands_played, self.round_current_hand)
        self.round_current_hand.append(played_card)
        p_action, p_card = self.select_action()
        print(p_card)
        if self.hand_winner_card is None or self.hand_winner_card.compare(played_card, self.game_mode, self.hokm_suit) == -1:
            self.hand_winner_card = played_card
            self.last_hand_winner_id = self.hand_next_player_id
        self.hand_next_player_id = (self.hand_next_player_id + 1) % 4
        if len(self.round_current_hand) == 4:
            self.round_hands_played.append(self.round_current_hand)
            self.logging.add_hand(self.hand_first_player, self.round_current_hand)
            self.players[self.last_hand_winner_id].store_hand(self.round_current_hand)
            self.hand_first_player = self.last_hand_winner_id
            self.hand_next_player_id = self.last_hand_winner_id
            self.round_current_hand = []
            self.hand_winner_card = None

    def end_round(self):
        self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % 4
        self.team_1_round_score = (self.players[0].saved_deck + self.players[2].saved_deck).get_deck_score()
        self.team_2_round_score = (self.players[1].saved_deck + self.players[3].saved_deck).get_deck_score()
        self.french_deck = self.players[0].saved_deck + self.players[2].saved_deck + self.players[1].saved_deck + self.players[3].saved_deck
        final_bet = self.round_bets[-1]
        team1_has_bet = final_bet.id == 0 or final_bet.id == 2
        if self.verbose:
            self.logging.log()
        if (team1_has_bet and self.team_1_round_score >= final_bet.bet) or (not team1_has_bet and self.team_2_round_score >= final_bet.bet):
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
        print("Round {}: Team 1 score = {} and Team 2 score = {}".format(self.round_counter, s1, s2))
        self.round_counter += 1
        if self.check_game_finished():
            print("Final Scores = Team 1 score = {} and Team 2 score = {}".format(self.team_1_score, self.team_2_score))

    def check_game_finished(self):
        if self.team_1_score >= 1165 or self.team_1_score - self.team_2_score >= 1165:
            return True
        elif self.team_2_score >= 1165 or self.team_2_score - self.team_1_score >= 1165:
            return True
        return False

    def reset(self):
        self.set_players([IntelligentPlayer(0, 2), IntelligentPlayer(1, 3), IntelligentPlayer(2, 0), IntelligentPlayer(3, 1)])
        for i in range(4):
            self.players[i].init_policies_from_another_policy(self.optimization_policy)
        self.round_counter = 1
        self.team_1_score = 0.0
        self.team_2_score = 0.0
        self.team_1_round_score = 0.0
        self.team_2_round_score = 0.0
        self.french_deck = Deck()
        self.player_id_receiving_first_hand = 0
        self.game_state = GAMESTATE.READY_TO_START
        del self.round_bets[:]
        self.betting_players = None
        self.initially_passed_count = 0
        self.betting_rounds = 0
        self.hakem = None
        self.round_middle_deck = None
        del self.round_hands_played[:]
        del self.round_current_hand[:]
        self.last_hand_winner_id = 0
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NEITHER
        self.hand_first_player = 0
        self.hand_next_player_id = 0
        self.hand_winner_card = None

    def render(self, mode='human'):
        pass

    def close(self):
        del self.players[:]
