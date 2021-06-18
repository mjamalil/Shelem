from typing import Tuple, List
import numpy as np
import torch

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Utils import GAMEMODE, SUITS, VALUES
from players.Player import Player, Bet
from players.Enum import *


class BaseIntelligentPlayer(Player):
    hokm_suit = SUITS.NOSUIT

    def __init__(self, player_id, team_mate_player_id):
        super().__init__(player_id, team_mate_player_id)
        self.build_model()
        self.game_state = [NOT_SET] * NUMBER_OF_PARAMS
        self.PLAYED_CARD_OFFSET = 16
        self.agent = False

    def init_policies_from_another_policy(self, other_policy):
        pass

    def begin_round(self, deck: Deck):
        super().begin_round(deck)
        # a series of values storing all data of a round
        # game_state = my cards + ground cards + played tricks + game status
        self.game_state = [NOT_SET] * NUMBER_OF_PARAMS
        for i in range(len(deck.cards)):
            self.game_state[deck.cards[i].id] = 1

    def end_round(self, team1_score: int, team2_score: int):
        pass

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Score should be strictly > previous_last_bet
        """
        # TODO: NotImplemented
        return Bet(self.player_id, 120)

    def decide_trump(self) -> SUITS:
        trump = super().decide_trump()
        # set new deck
        for i in range(DECK_SIZE):
            self.game_state[i] = 0
        for i in range(len(self.deck.cards)):
            self.game_state[self.deck.cards[i].id] = 1
        # set widow cards
        widow_size = 4
        for i in range(widow_size):
            self.game_state[STATE_PLAYED_CARDS_IDX+self.saved_deck[i].id] = 1
        return trump

    def set_hokm_and_game_mode(self, game_mode: GAMEMODE, hokm_suit: SUITS):
        super().set_hokm_and_game_mode(game_mode, hokm_suit)
        self.game_mode = game_mode
        self.hokm_suit = hokm_suit
        self.game_state[STATE_TRUMP_IDX] = hokm_suit/SUITS.NOSUIT

    def play_a_card(self, current_hand: List, current_suit: SUITS) -> Card:
        return self.deck.pop_random_from_suit(current_suit)

    def card_has_been_played(self, current_hand: List, current_suit: SUITS):
        max_crr_trick_num = 3
        self.game_state[STATE_SUIT_IDX] = current_suit/SUITS.NOSUIT
        for i in range(max_crr_trick_num):
            if i < len(current_hand):
                self.game_state[STATE_CRR_TRICK_IDX+i] = current_hand[i].id/DECK_SIZE
            else:
                self.game_state[STATE_CRR_TRICK_IDX+i] = 1

    def discard_cards_from_leader(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        # TODO: NotImplemented
        return super().discard_cards_from_leader()

    def encode_last_bets(self, all_bets: List[Bet]):
        score_mappings = {v: k for k, v in enumerate([x*5 for x in ([0] + list(range(20, 36)))])}
        opponent_1_id = (self.player_id + 1) % 4
        encoding_vector = [0] * (len(score_mappings)*4 + 52)
        for bet in all_bets:
            score_id = score_mappings[int(bet.bet)]
            if bet.id == self.player_id:
                encoding_vector[score_id] = 1
            elif bet.id == self.team_mate_player_id:
                encoding_vector[score_id + len(score_mappings)] = 1
            elif bet.id == opponent_1_id:
                encoding_vector[score_id + 2 * len(score_mappings)] = 1
            else:
                encoding_vector[score_id + 3 * len(score_mappings)] = 1
        for card in self.deck:
            val = card.value.value.normal_value
            st = card.suit.value - 1
            encoding_vector[st * 13 + val + len(score_mappings)*4] = 1
        return encoding_vector

    def win_trick(self, hand: List[Card], winner_id: int):
        super().win_trick(hand, winner_id)
        for c in hand:
            # remove card from my cards if I have it
            self.game_state[c.id] = 0
            # add card to played cards
            self.game_state[STATE_PLAYED_CARDS_IDX+c.id] = 1
        max_crr_trick_num = 3
        for i in range(max_crr_trick_num):
            self.game_state[STATE_CRR_TRICK_IDX+i] = 1
        self.game_state[STATE_SUIT_IDX] = 1.0

    def get_valid_actions(self, current_suit):
        valid_actions = DECK_SIZE * [False]
        valid_action_found = False
        for c in self.deck.cards:
            if self.deck.has_suit(current_suit):
                if c.suit == current_suit:
                    valid_actions[c.id] = True
                    valid_action_found = True
            else:
                valid_actions[c.id] = True
                valid_action_found = True

        if not valid_action_found:
            raise RuntimeError("No Valid action found")
        return np.array(valid_actions)

    def build_model(self):
        pass

    def log_game_state(self):
        my_cards = []
        for idx in range(STATE_TRUMP_IDX):
            for c in self.deck:
                if idx == c.id and self.game_state[idx] == 1:
                    my_cards.append(c)
        print("MyCards", my_cards)
        print("Trump", self.game_state[STATE_TRUMP_IDX])
        print("Current Suit", self.game_state[STATE_SUIT_IDX])
        print("Current Trick", self.game_state[STATE_CRR_TRICK_IDX:STATE_PLAYED_CARDS_IDX])
        print("Played Cards", self.game_state[STATE_PLAYED_CARDS_IDX:])

class IntelligentPlayer(BaseIntelligentPlayer):
    pass

class AgentPlayer(BaseIntelligentPlayer):

    def __init__(self, player_id, team_mate_player_id):
        super().__init__(player_id, team_mate_player_id)
        self.agent = True


class PPOPlayer(BaseIntelligentPlayer):

    def build_model(self):
        state_dim = NUMBER_OF_PARAMS
        action_dim = ACTION_DIM
        #############################################
        n_latent_var = 64           # number of variables in hidden layer
        lr = 0.002
        betas = (0.9, 0.999)
        gamma = 0.99                # discount factor
        K_epochs = 4                # update policy for K epochs
        eps_clip = 0.2              # clip parameter for PPO
        #############################################
        from players.PPO import Memory, PPO
        self.memory = Memory()
        self.ppo = PPO(state_dim, action_dim, n_latent_var, lr, betas, gamma, K_epochs, eps_clip)

    def play_a_card(self, current_hand: List, current_suit: SUITS) -> Card:
        """
        :return: pops and plays the best available card in the current hand
        """
        invalid_card = True
        invalid_card_reward = -1
        invalid_count = 1
        # action = self.request_action(self.game_state)
        # print(action)
        # if action == 25:
        #     self.set_reward(1, True)
        # else:
        #     self.set_reward(-1, True)
        # return self.deck.pop_random_from_suit(current_suit)
        while invalid_card:
            try:
                valid_actions = self.get_valid_actions(current_suit)
                action = self.request_action(self.game_state, valid_actions)
                selected_card = self.deck.get_by_value(action)
            except ValueError as err:
                print(err)
            else:
                if self.deck.has_suit(current_suit):
                    if selected_card.suit == current_suit:
                        invalid_card = False
                else:
                    invalid_card = False
            if invalid_card:
                raise RuntimeError("invalid action")
                invalid_count += 1
                self.set_reward(invalid_card_reward, False)
        # if action >= 50:
        #     self.reward = 1
        # else:
        #     self.reward = -1
        # return self.deck.pop_random_from_suit(current_suit)
        return self.deck.pop_card_from_deck(selected_card)

    def set_reward(self, reward: float, done: bool):
        print("reward: {}".format(reward))
        self.memory.rewards.append(reward)
        self.memory.is_terminals.append(done)

    def request_action(self, game_state: List, valid_actions: List):
        action = self.ppo.policy_old.act(np.array(game_state), self.memory, valid_actions)
        for idx, a in enumerate(self.ppo.policy_old.new_probs):
            if a.item() != 0.0:
                selected_card = self.deck.get_by_value(idx)
                print("{} ->{: .2f}".format(selected_card, a.item() * 100))
        return action

    def begin_round(self, deck: Deck):
        super().begin_round(deck)
        print(deck)
        self.reward = 0

    def end_round(self, team1_score: int, team2_score: int):
        # if self.player_id in [0, 2]:
        #     reward = (team1_score - team2_score) / 330
        # else:
        #     reward = (team2_score - team1_score) / 330
        # if reward > 1:
        #     reward = 1
        # elif reward < -1:
        #     reward = -1
        if self.player_id in [0, 2]:
            if team1_score > team2_score:
                reward = 1
            else:
                reward = -1
        else:
            if team1_score > team2_score:
                reward = -1
            else:
                reward = 1
        self.set_reward(reward, True)
        self.ppo.update(self.memory)
        self.memory.clear_memory()
        pass

    def win_trick(self, hand: List[Card], winner_id: int):
        super().win_trick(hand, winner_id)
        if winner_id == self.player_id or winner_id == self.team_mate_player_id:
            reward = Deck(hand).get_deck_score() / self.hakem_bid.bet_score
        else:
            reward = -Deck(hand).get_deck_score() / self.hakem_bid.bet_score
        done = True if self.trick_number == PLAYER_INITIAL_CARDS else False
        if not done:
            self.set_reward(reward, False)
