import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical

from envs import ShelemEnv
from players.Enum import DECK_SIZE

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class Memory:
    def __init__(self):
        self.actions = []
        self.states = []
        self.logprobs = []
        self.rewards = []
        self.is_terminals = []

    def clear_memory(self):
        del self.actions[:]
        del self.states[:]
        del self.logprobs[:]
        del self.rewards[:]
        del self.is_terminals[:]

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim, n_latent_var):
        super().__init__()

        # actor
        self.action_layer = nn.Sequential(
            nn.Linear(state_dim, n_latent_var),
            nn.Tanh(),
            nn.Linear(n_latent_var, n_latent_var),
            nn.Tanh(),
            nn.Linear(n_latent_var, action_dim),
            nn.Softmax(dim=-1)
        )

        # critic
        self.value_layer = nn.Sequential(
            nn.Linear(state_dim, n_latent_var),
            nn.Tanh(),
            nn.Linear(n_latent_var, n_latent_var),
            nn.Tanh(),
            nn.Linear(n_latent_var, 1)
        )

    def forward(self):
        raise NotImplementedError

    def act(self, state, memory):
        state = torch.from_numpy(state).float().to(device)
        action_probs = self.action_layer(state)
        dist = Categorical(action_probs)
        action = dist.sample()

        memory.states.append(state)
        memory.actions.append(action)
        memory.logprobs.append(dist.log_prob(action))

        return action.item()

    def evaluate(self, state, action):
        action_probs = self.action_layer(state)
        dist = Categorical(action_probs)

        action_logprobs = dist.log_prob(action)
        dist_entropy = dist.entropy()

        state_value = self.value_layer(state)

        return action_logprobs, torch.squeeze(state_value), dist_entropy


class MaskableActorCritic(ActorCritic):

    def act(self, state, memory, valid_actions):
        state = torch.from_numpy(state).float().to(device)
        self.action_probs = self.action_layer(state)
        # mask actions
        print(self.action_probs)
        self.new_probs = torch.tensor(DECK_SIZE * [0.0])
        self.new_probs.masked_scatter_(torch.from_numpy(valid_actions), self.action_probs)
        # print(self.new_probs)
        dist = Categorical(self.new_probs)
        action = dist.sample()

        memory.states.append(state)
        memory.actions.append(action)
        memory.logprobs.append(dist.log_prob(action))

        return action.item()


class PPO:
    def __init__(self, state_dim, action_dim, n_latent_var, lr, betas, gamma, K_epochs, eps_clip):
        self.lr = lr
        self.betas = betas
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.K_epochs = K_epochs
        print("using device: {}".format(device))

        self.policy = MaskableActorCritic(state_dim, action_dim, n_latent_var).to(device)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=lr, betas=betas)
        self.policy_old = MaskableActorCritic(state_dim, action_dim, n_latent_var).to(device)
        self.policy_old.load_state_dict(self.policy.state_dict())

        self.MseLoss = nn.MSELoss()

    def update(self, memory):
        # Monte Carlo estimate of state rewards:
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(memory.rewards), reversed(memory.is_terminals)):
            if is_terminal:
                discounted_reward = 0
            discounted_reward = reward + (self.gamma * discounted_reward)
            rewards.insert(0, discounted_reward)

        # Normalizing the rewards:
        rewards = torch.tensor(rewards, dtype=torch.float32).to(device)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)

        # convert list to tensor
        old_states = torch.stack(memory.states).to(device).detach()
        old_actions = torch.stack(memory.actions).to(device).detach()
        old_logprobs = torch.stack(memory.logprobs).to(device).detach()

        # Optimize policy for K epochs:
        for _ in range(self.K_epochs):
            # Evaluating old actions and values :
            logprobs, state_values, dist_entropy = self.policy.evaluate(old_states, old_actions)

            # Finding the ratio (pi_theta / pi_theta__old):
            ratios = torch.exp(logprobs - old_logprobs.detach())

            # Finding Surrogate Loss:
            advantages = rewards - state_values.detach()
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1-self.eps_clip, 1+self.eps_clip) * advantages
            loss = -torch.min(surr1, surr2) + 0.5*self.MseLoss(state_values, rewards) - 0.01*dist_entropy

            # take gradient step
            self.optimizer.zero_grad()
            loss.mean().backward()
            self.optimizer.step()

        # Copy new weights into old policy:
        self.policy_old.load_state_dict(self.policy.state_dict())

def main():
    state_dim = 71
    action_dim = 52
    env = ShelemEnv(action_dim, state_dim)
    env_name = env.environment_name
    state_dim = env.observation_space.shape[0]
    num_box = tuple((env.observation_space.high + np.ones(env.observation_space.shape)).astype(int))
    print(env.observation_space.shape)
    q_table = np.zeros(num_box+(env.action_space.n,))
    print(num_box+(env.action_space.n,))
    print(np.zeros((2,2)))


    render = False
    solved_reward = 230         # stop training if avg_reward > solved_reward
    log_interval = 20           # print avg reward in the interval
    max_episodes = 50000        # max training episodes
    max_timesteps = 300         # max timesteps in one episode
    n_latent_var = 64           # number of variables in hidden layer
    update_timestep = 2000      # update policy every n timesteps
    lr = 0.002
    betas = (0.9, 0.999)
    gamma = 0.99                # discount factor
    K_epochs = 4                # update policy for K epochs
    eps_clip = 0.2              # clip parameter for PPO

    #############################################

    # random_seed = None
    # if random_seed:
    #     torch.manual_seed(random_seed)
    #     env.seed(random_seed)

    memory = Memory()
    ppo = PPO(state_dim, action_dim, n_latent_var, lr, betas, gamma, K_epochs, eps_clip)

    # logging variables
    running_reward = 0
    avg_length = 0
    timestep = 0

    # training loop
    for i_episode in range(1, max_episodes+1):
        state = env.reset()
        for t in range(max_timesteps):
            timestep += 1

            # Running policy_old:
            action = ppo.policy_old.act(state, memory)
            print(action)
            # state, reward, done, _ = env.step(action)
            state, reward, done = state, -1, False
            if action == 20:
                reward = 1

            # Saving reward and is_terminal:
            memory.rewards.append(reward)
            memory.is_terminals.append(done)

            # update if its time
            if timestep % update_timestep == 0:
                ppo.update(memory)
                memory.clear_memory()
                timestep = 0

            running_reward += reward
            if render:
                env.render()
            if done:
                break

        avg_length += t

        # stop training if avg_reward > solved_reward
        if running_reward > (log_interval*solved_reward):
            print("########## Solved! ##########")
            torch.save(ppo.policy.state_dict(), './PPO_{}.pth'.format(env_name))
            break

        # logging
        if i_episode % log_interval == 0:
            avg_length = int(avg_length/log_interval)
            running_reward = int((running_reward/log_interval))

            print('Episode {} \t avg length: {} \t reward: {}'.format(i_episode, avg_length, running_reward))
            running_reward = 0
            avg_length = 0


import random
import math
from collections import namedtuple

from typing import List

from dealer.Card import Card
from dealer.Deck import Deck
from players.Enum import GAMESTATE, VALUES, GAMEMODE, SUITS
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


