import random
from collections import namedtuple
import gym
import numpy as np
from gym import spaces
from gym.utils import seeding

class ShelemEnv(gym.Env):
    environment_name = "Shelem Environment"

    def __init__(self, action_dim, num_states, stochasticity_of_action_right=0.5):
        self.action_space = spaces.Discrete(action_dim)
        # self.observation_space = spaces.Dict(dict(
        #     bid=spaces.Box(0, 10, shape=(num_states,), dtype=np.int64),
        #     played_cards=spaces.Box(0, 10, shape=(num_states,), dtype=np.int64),
        #     gamestate=spaces.Box(0, 10, shape=(num_states,), dtype=np.int64),
        # ))
        self.observation_space = spaces.Box(0, 200, shape=(num_states,), dtype=np.int64)
        self.observation_space = spaces.Box(np.array([0,0,0,0,0]), np.array([10,10,10,10,10]), dtype=np.int64)
        # self.observation_space = spaces.MultiDiscrete([4,12,4, 48,3])
        self.seed()
        self.reward_threshold = 1.0
        self.trials = 100
        self.max_episode_steps = 100
        self.id = "Long Corridor"
        self.action_translation = {0: "left", 1: "right"}
        self.stochasticity_of_action_right = stochasticity_of_action_right
        self.num_states = num_states
        self.visited_final_state = False
        self.reward_if_visited_final_state = 1.0
        self.reward_if_havent_visited_final_state = 0.01

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        self.episode_steps += 1
        # print(action)
        if action == 20:
            self.reward = 10
        else:
            self.reward = -10
        self.done = False
        self.next_state = self.observation_space.sample()
        self.state = self.next_state
        self.s = np.array(self.next_state)
        return self.s, self.reward, self.done, {}

    def reset(self):
        self.state = self.observation_space.sample()  # environment always starts in state 1
        print(self.state)
        self.next_state = None
        self.reward = None
        self.done = False
        self.visited_final_state = False
        self.episode_steps = 0
        self.s = np.array(self.state)
        return self.s
