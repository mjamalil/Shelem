import torch
import torch.nn as nn
import random
import math
from collections import namedtuple

from typing import List

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Utils import GAMESTATE, VALUES, GAMEMODE, SUITS
from players.Player import Bet

Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class DQN(nn.Module):
    def __init__(self, input_size, output_size):
        super(DQN, self).__init__()
        self.input_size = input_size
        self.output_size = output_size
        # TODO try more complicated models here
        self.transformer = nn.Linear(input_size, output_size)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, input_observation, **kwargs):
        return self.softmax(self.transformer(input_observation))


class ShelemPolicyDQN(nn.Module):
    def __init__(self, maximum_valid_bet=165, minimum_valid_bet=100):
        super(ShelemPolicyDQN, self).__init__()
        self.number_of_cards = len(VALUES) * 4
        self.number_of_suits = 4
        BATCH_SIZE = 128
        GAMMA = 0.999
        self.EPS_START = 0.9
        self.EPS_END = 0.05
        self.EPS_DECAY = 200
        self.steps_done = 0
        self.number_of_game_modes = len(GAMEMODE)
        # [PASS, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, SHELEM, SAR-SHELEM, SUPER-SHELEM]
        self.size_of_bet_space = int((maximum_valid_bet - minimum_valid_bet) / 5) + 4
        # each policy receives a one-hot vector of cards (+ the available history of the game)
        self.bidding_policy = DQN(input_size=self.number_of_cards + self.size_of_bet_space, output_size=self.size_of_bet_space).to(device)
        self.play_card_policy = DQN(input_size=self.number_of_cards, output_size=self.number_of_cards).to(device)
        self.widowing_policy = DQN(input_size=self.number_of_cards, output_size=self.number_of_cards).to(device)
        self.trump_decision_policy = DQN(input_size=self.number_of_cards, output_size=self.number_of_suits).to(device)
        self.game_mode_decision_policy = DQN(input_size=self.number_of_cards, output_size=self.number_of_game_modes).to(device)

    def load_from_policy(self, p):
        self.bidding_policy.load_state_dict(p.bidding_policy.state_dict())
        self.play_card_policy.load_state_dict(p.play_card_policy.state_dict())
        self.widowing_policy.load_state_dict(p.widowing_policy.state_dict())
        self.trump_decision_policy.load_state_dict(p.trump_decision_policy.state_dict())
        self.game_mode_decision_policy.load_state_dict(p.game_mode_decision_policy.state_dict())

    def select_action(self, game_state: GAMESTATE, player_deck: Deck, bidding_sequence: List[Bet] = None):
        sample = random.random()
        eps_threshold = self.EPS_END + (self.EPS_START - self.EPS_END) * math.exp(-1. * self.steps_done / self.EPS_DECAY)
        self.steps_done += 1
        if sample > eps_threshold:
            with torch.no_grad():
                # t.max(1) will return largest column value of each row.
                # second column on max result is index of where max element was
                # found, so we pick action with the larger expected reward.
                state_policy = self.get_state_policy(game_state)
                if game_state == GAMESTATE.BIDDING and bidding_sequence is None:
                    bidding_sequence = []
                state = self.create_state_policy_input(player_deck, bidding_sequence)
                res = state_policy(torch.tensor([state], device=device, dtype=torch.float)).max(1)[1].view(1, 1)

        else:
            res = torch.tensor([[random.randrange(self.get_action_space_size(game_state))]], device=device, dtype=torch.long)
        return res, self.interpret_action(game_state, res.item())

    def interpret_action(self, game_state: GAMESTATE, action: int):
        if game_state == GAMESTATE.BIDDING:
            if action == 0:
                return Bet(-1, 0)
            else:
                return Bet(-1, (action+19) * 5)
        elif game_state == GAMESTATE.DECIDE_GAME_MODE:
            if action == 0:
                return GAMEMODE.NORMAL
            elif action == 1:
                return GAMEMODE.SARAS
            elif action == 2:
                return GAMEMODE.NARAS
            else:
                return GAMEMODE.ACE_NARAS
        elif game_state == GAMESTATE.DECIDE_TRUMP:
            if action == 0:
                return SUITS.DIAMONDS
            elif action == 1:
                return SUITS.CLUBS
            elif action == 2:
                return SUITS.HEARTS
            else:
                return SUITS.SPADES
        elif game_state == GAMESTATE.WIDOWING:
            return Card.from_numeric_value(action)
        elif game_state == GAMESTATE.PLAYING_CARDS:
            return Card.from_numeric_value(action)
        else:
            raise ValueError("No policy network is defined for game state: {}".format(game_state))

    def get_state_policy(self, game_state: GAMESTATE):
        if game_state == GAMESTATE.BIDDING:
            return self.bidding_policy
        elif game_state == GAMESTATE.DECIDE_GAME_MODE:
            return self.game_mode_decision_policy
        elif game_state == GAMESTATE.DECIDE_TRUMP:
            return self.trump_decision_policy
        elif game_state == GAMESTATE.WIDOWING:
            return self.widowing_policy
        elif game_state == GAMESTATE.PLAYING_CARDS:
            return self.play_card_policy
        else:
            raise ValueError("No policy network is defined for game state: {}".format(game_state))

    def get_action_space_size(self, game_state: GAMESTATE):
        if game_state == GAMESTATE.BIDDING:
            return self.size_of_bet_space
        elif game_state == GAMESTATE.DECIDE_GAME_MODE:
            return self.number_of_game_modes
        elif game_state == GAMESTATE.DECIDE_TRUMP:
            return self.number_of_suits
        elif game_state == GAMESTATE.WIDOWING:
            return self.number_of_cards
        elif game_state == GAMESTATE.PLAYING_CARDS:
            return self.number_of_cards
        else:
            raise ValueError("No policy network is defined for game state: {}".format(game_state))

    def create_state_policy_input(self, player_deck: Deck, bidding_sequence: List[Bet] = None):
        embedded_player_deck = [0] * len(VALUES) * 4
        for card in player_deck:
            embedded_player_deck[card.numeric_value] = 1
        if bidding_sequence is not None:
            temp_embedding = [0] * self.size_of_bet_space
            for bet in bidding_sequence:
                bet_score = bet.bet_score
                if bet_score == 0:
                    temp_embedding[0] = 1
                else:
                    bet_index = int(bet_score * 0.2 - 19)
                    temp_embedding[bet_index] = 1
            return embedded_player_deck + temp_embedding
        else:
            return embedded_player_deck


class ReplayMemory(object):

    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, *args):
        """Saves a transition."""
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)
