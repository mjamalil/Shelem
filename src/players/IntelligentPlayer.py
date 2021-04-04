import random
from typing import Tuple, List
import numpy as np
from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Utils import GAMEMODE, SUITS
from players.Player import Player, Bet
from players.Env import ShelemEnv
from players.PPO import Memory, PPO
import torch
import torch.nn as nn
from torch.distributions import Categorical


class IntelligentPlayer(Player):
    def begin_game(self, deck: Deck):
        super().begin_game(deck)
        # print(self.deck)

    def __init__(self, player_id, team_mate_player_id):
        super().__init__(player_id, team_mate_player_id)
        self.init_ppo()

    def end_game(self):
        self.memory.is_terminals.append(True)

    def win_trick(self, hand: List[Card], winner_id: int):
        super().win_trick(hand, winner_id)
        if winner_id == self.player_id or winner_id == self.team_mate_player_id:
            reward = Deck(hand).get_deck_score()
        else:
            reward = -Deck(hand).get_deck_score()
        self.memory.rewards.append(reward)

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Score should be strictly > previous_last_bet
        """
        # TODO: NotImplemented
        return Bet(self.player_id, 120)

    def discard_cards_from_leader(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        # TODO: NotImplemented
        suit_select = random.randint(1, 4)
        if suit_select == 1:
            hokm_suit = SUITS.SPADES
        elif suit_select == 2:
            hokm_suit = SUITS.HEARTS
        elif suit_select == 3:
            hokm_suit = SUITS.DIAMONDS
        else:
            hokm_suit = SUITS.CLUBS
        return random.sample(range(16), 4), self.game_mode, hokm_suit

    def play_a_card(self, game_state: List, current_suit: SUITS) -> Card:
        """
        :return: pops and plays the best available card in the current hand  
        """
        # print(len(game_state))

        invalid_card = True
        invalid_card_reward = -1000
        invalid_count = 1
        while invalid_card:
            try:
                action = self.ppo.policy_old.act(np.array(game_state), self.memory)
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
                self.memory.rewards.append(invalid_card_reward)
        print(f"Good card aft?er {invalid_count} tries -> {selected_card}")

        return self.deck.pop_card_from_deck(selected_card)

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

    def init_ppo(self):
        state_dim = 71
        action_dim = 52
        env = ShelemEnv(action_dim, state_dim)
        env_name = env.environment_name

        render = False
        solved_reward = 230         # stop training if avg_reward > solved_reward
        log_interval = 20           # print avg reward in the interval
        max_episodes = 50000        # max training episodes
        max_timesteps = 300         # max timesteps in one episode
        update_timestep = 2000      # update policy every n timesteps
        random_seed = None
        #############################################
        n_latent_var = 64           # number of variables in hidden layer
        lr = 0.002
        betas = (0.9, 0.999)
        gamma = 0.99                # discount factor
        K_epochs = 4                # update policy for K epochs
        eps_clip = 0.2              # clip parameter for PPO
        #############################################

        # if random_seed:
        #     torch.manual_seed(random_seed)
        #     env.seed(random_seed)

        self.memory = Memory()
        self.ppo = PPO(state_dim, action_dim, n_latent_var, lr, betas, gamma, K_epochs, eps_clip)
        # print(lr, betas)

        # logging variables
        running_reward = 0
        avg_length = 0
        timestep = 0

        # training loop
        # for i_episode in range(1, max_episodes+1):
        #     state = env.reset()
        #     for t in range(max_timesteps):
        #         timestep += 1
        #
        #         # Running policy_old:
        #         action = self.ppo.policy_old.act(state, self.memory)
        #         state, reward, done, _ = env.step(action)
        #
        #         # Saving reward and is_terminal:
        #         self.memory.rewards.append(reward)
        #         self.memory.is_terminals.append(done)
        #
        #         # update if its time
        #         if timestep % update_timestep == 0:
        #             self.ppo.update(self.memory)
        #             self.memory.clear_memory()
        #             timestep = 0
        #
        #         running_reward += reward
        #         if render:
        #             env.render()
        #         if done:
        #             break
        #
        #     avg_length += t
        #
        #     # stop training if avg_reward > solved_reward
        #     if running_reward > (log_interval*solved_reward):
        #         print("########## Solved! ##########")
        #         torch.save(self.ppo.policy.state_dict(), './PPO_{}.pth'.format(env_name))
        #         break
        #
        #     # logging
        #     if i_episode % log_interval == 0:
        #         avg_length = int(avg_length/log_interval)
        #         running_reward = int((running_reward/log_interval))
        #
        #         print('Episode {} \t avg length: {} \t reward: {}'.format(i_episode, avg_length, running_reward))
        #         running_reward = 0
        #         avg_length = 0