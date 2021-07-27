import gym
import numpy as np
from gym import spaces
from collections import deque
from typing import List

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Logging import Logging
from dealer.Utils import ThreeConsecutivePassesException, InvalidActionError
from players.Enum import NUMBER_OF_PARAMS, ACTION_SIZE, NUM_PLAYERS, GAMESTATE, SUITS, GAMEMODE
from players.IntelligentPlayer import IntelligentPlayer, AgentPlayer
from players.Player import Player


class ShelemEnv(gym.Env):
    initialized = False

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

        from players.PPO import ShelemPolicyDQN
        self.optimization_policy = ShelemPolicyDQN()
        self.game_state = GAMESTATE.READY_TO_START
        self.reward = 0
        self.action_performed = False
        self.num_envs = 1

    def action_mask(self):
        raise NotImplementedError
        return self.players[0].action_mask

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
            return self.players[self.current_player]
        else:
            raise ValueError("No current player is defined for game state: {}".format(self.game_state))

    def step(self, action):
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
            return self.step(action)
        elif self.game_state == GAMESTATE.DECIDE_GAME_MODE:
            self.decide_game_mode(action)
            self.game_state = GAMESTATE.DECIDE_TRUMP
            reward = 0
            return self.step(action)
        elif self.game_state == GAMESTATE.DECIDE_TRUMP:
            self.decide_trump(action)
            self.game_state = GAMESTATE.PLAYING_CARDS
            if len(self.hakem.saved_deck) == NUM_PLAYERS:
                self.logging.log_hakem_saved_hand(Deck(self.hakem.saved_deck))
                self.hand_winner = self.hakem.player_id
                self.hand_first_player = self.hand_winner
                self.current_player = self.hand_winner
                self.round_current_hand = []
                self.hand_winner_card = None
                self.game_state = GAMESTATE.PLAYING_CARDS
            reward = 0
            return self.step(action)
        elif self.game_state == GAMESTATE.WIDOWING:
            self.player_widow_card(action)
            # TODO what should be the reward in here?
            reward = 0
            return self.step(action)
        elif self.game_state == GAMESTATE.PLAYING_CARDS:
            if len(self.round_hands_played) < 12:
                done = self.play_card(action)
                if done:
                    print("reward:{}".format(self.reward))
                    return self.observation, self.reward, False, {}
            else:
                print(self.round_hands_played)
                raise RuntimeError("There should not be more than 12 hands!")
            if len(self.round_hands_played) == 12:
                self.end_round()
                self.game_state = GAMESTATE.READY_TO_START
                return self.observation, 0, True, {}
            return self.step(action)
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
            # raise RuntimeError("Three first players have passed, the game must re-init")
            self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % NUM_PLAYERS
            raise ThreeConsecutivePassesException("Three first players have passed, the game must re-init")
        bp = self.betting_players.popleft()
        # TODO implement make bet
        player_bet = bp.make_bet(self.round_bets)
        # p_action, p_bet = self.select_action()
        # p_bet.player_id = bp.player_id
        # print(p_bet)
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
            self.players[i].set_hokm_and_game_mode(self.game_mode, self.hokm_suit, self.hakem)

    def player_widow_card(self, action):
        saving_index = self.hakem.decide_widow_card()
        new_deck = Deck([])
        for ind in range(len(self.hakem.deck)):
            if ind == saving_index:
                self.hakem.saved_deck += self.hakem.deck[ind]
            else:
                new_deck += self.hakem.deck[ind]
        self.hakem.deck = new_deck
        # p_action, p_card = self.select_action()
        # print(p_card)

    def play_card(self, action):

        if self.players[self.current_player].agent:
            if self.action_performed:
                self.action_performed = False
                self.observation = self.players[self.current_player].game_state
                self.players[self.current_player].log_game_state()
                # self.reward = 1
                return True
            try:
                played_card = self.players[self.current_player].pop_card_from_deck(action, self.current_suit)
            except InvalidActionError:
                print("Invalid action: {}".format(action))
                self.reward = -1
                return True
            self.action_performed = True
            print("{}-{}:Agent".format(self.current_player, played_card))
        else:
            played_card = self.players[self.current_player].play_a_card(self.round_current_hand, self.current_suit)
            print("{}-{}".format(self.current_player, played_card))
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
        return False

    def end_trick(self):
        print("*" * 40)
        self.round_hands_played.append(self.round_current_hand)
        self.logging.add_hand(self.hand_first_player, self.round_current_hand)
        for p in self.players:
            p.win_trick(self.round_current_hand, self.hand_winner)
        if self.hand_winner in [0, 2]:
            self.reward = Deck(self.round_current_hand).get_deck_score() / 165
        else:
            self.reward = 0
        self.hand_first_player = self.hand_winner
        self.round_current_hand = []
        self.current_suit = SUITS.NOSUIT
        self.hand_winner_card = None

    def end_round(self):
        self.player_id_receiving_first_hand = (self.player_id_receiving_first_hand + 1) % NUM_PLAYERS
        self.team_1_round_score = (self.players[0].saved_deck + self.players[2].saved_deck).get_deck_score()
        self.team_2_round_score = (self.players[1].saved_deck + self.players[3].saved_deck).get_deck_score()
        self.reward = self.get_round_reward(self.hakem.player_id, self.team_1_round_score, self.team_2_round_score, self.reward)
        self.french_deck = self.players[0].saved_deck + self.players[2].saved_deck + \
                           self.players[1].saved_deck + self.players[3].saved_deck
        final_bet = self.round_bets[-1]
        team1_has_bet = final_bet.id == 0 or final_bet.id == 2
        if self.verbose:
            self.logging.log()
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
        print("Round {}: Team 1 score = {} and Team 2 score = {}".format(self.round_counter, s1, s2))
        self.round_counter += 1
        if self.check_game_finished():
            print("Final Scores = Team 1 score = {} and Team 2 score = {}".format(self.team_1_score, self.team_2_score))
        self.round_hands_played.clear()

    def check_game_finished(self):
        if self.team_1_score >= 1165 or self.team_1_score - self.team_2_score >= 1165:
            return True
        elif self.team_2_score >= 1165 or self.team_2_score - self.team_1_score >= 1165:
            return True
        return False

    def reset(self):
        if self.initialized:
            return self.observation
        self.set_players([
            AgentPlayer(0, 2),
            IntelligentPlayer(1, 3),
            IntelligentPlayer(2, 0),
            IntelligentPlayer(3, 1)
        ])
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
        self.hand_winner = 0
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NOSUIT
        self.hand_first_player = 0
        self.current_player = 0
        self.hand_winner_card = None
        # return np.ndarray([1,2,3])
        self.observation = self.players[0].game_state
        self.initialized = True
        return self.observation
        # return np.array(self.players[0].game_state)

    def render(self, mode='human'):
        pass

    def close(self):
        del self.players[:]

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
        print(round_reward)
        if round_reward > 1.0:
            round_reward = 1.0
        elif round_reward < -1.0:
            round_reward = -1.0
        return round_reward
