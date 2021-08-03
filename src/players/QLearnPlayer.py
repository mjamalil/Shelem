import random
from typing import List

import numpy as np

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Utils import SUITS
from players.Enum import *
from players.IntelligentPlayer import IntelligentPlayer


class QLearnPlayer(IntelligentPlayer):

    def __init__(self, player_id, team_mate_player_id):
        super().__init__(player_id, team_mate_player_id)
        self.q_table_actions = []
        self.current_action = None
        self.current_state = None

    def build_model(self):
        self.epsilon = 1
        self.epsilon_decay = 0.001
        self.learning_rate = 0.1
        self.gamma = 0.6
        self.q_table = np.zeros(NUMBER_OF_PARAMS*(ACTION_DIM,))

    def add_reward(self, action: int, reward: int, state: List, next_state: List):
        q_value = self.q_table[state][action]
        best_q = np.max(self.q_table[next_state])
        new_q = (1-self.learning_rate) * q_value + self.learning_rate * (reward + self.gamma * best_q)
        self.q_table[state][action] = new_q

    def request_action(self, game_state: List):
        self.epsilon -= self.epsilon_decay
        if random.uniform(0, 1) < self.epsilon:
            action = random.randint(0, ACTION_DIM-1)
        else:
            action = np.argmax(self.q_table[game_state])
        return action

    def end_trick(self, hand: List[Card], winner_id: int, first_player: int):
        super().end_trick(hand, winner_id, first_player)

        if winner_id == self.player_id or winner_id == self.team_mate_player_id:
            reward = Deck(hand).get_deck_score()
        else:
            reward = -Deck(hand).get_deck_score()

        done = True if self.trick_number == PLAYER_INITIAL_CARDS else False
        self.add_reward(self.current_action, reward, self.current_state, self.game_state)

    def play_a_card(self, current_hand: List, current_suit: SUITS) -> Card:
        """
        :return: pops and plays the best available card in the current hand
        """
        # action = self.ppo.policy_old.act(np.array(game_state), self.memory)
        # if action == 20:
        #     self.memory.rewards.append(20)
        # else:
        #     self.memory.rewards.append(-20)
        # return super().play_a_card(game_state, current_suit)
        # self.game_state[-3] = current_suit
        # copy_current_hand = current_hand[:]
        # for i in range(len(current_hand)):
        #     state_idx = self.PLAYED_CARD_OFFSET + self.trick_number * 4 + (self.player_id - i + 3) % 4
        #     self.game_state[state_idx] = copy_current_hand.pop().id

        invalid_card = True
        invalid_card_reward = -1000
        invalid_count = 1
        while invalid_card:
            try:
                action = self.request_action(self.game_state)
                selected_card = self.deck.get_by_value(action)
            except ValueError:
                pass
            else:
                if self.deck.has_suit(current_suit):
                    if selected_card.suit == current_suit:
                        invalid_card = False
                else:
                    invalid_card = False
            if invalid_card:
                invalid_count += 1
                self.add_reward(action, invalid_card_reward, self.game_state, self.game_state)
        self.current_action = action
        self.current_state = self.game_state[:]
        # remove card from game state
        for i in range(PLAYER_INITIAL_CARDS):
            if self.game_state[i] == selected_card.id:
                self.game_state[i] = NOT_SET
                break
        else:
            raise RuntimeError("can't find selected card: {}".format(selected_card.id))

        return self.deck.pop_card_from_deck(selected_card)


