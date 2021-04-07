import random
from typing import Tuple, List
import numpy as np
from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Utils import GAMEMODE, SUITS, PLAYER_INITIAL_CARDS
from players.Player import Player, Bet
from players.PPO import Memory, PPO

number_of_params = 12
NOT_SET = 255
ACTION_DIM = 52

class IntelligentPlayer(Player):

    def __init__(self, player_id, team_mate_player_id):
        super().__init__(player_id, team_mate_player_id)
        self.build_model()
        self.game_state = []
        self.PLAYED_CARD_OFFSET = 16

    def begin_round(self, deck: Deck):
        super().begin_round(deck)
        # a series of values storing all data of a round
        # game_state = my cards + ground cards + played tricks + game status
        self.game_state = [NOT_SET] * number_of_params
        for i in range(len(deck.cards)):
            self.game_state[i] = deck.cards[i].id

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

    def make_hakem(self, middle_hand: Deck) -> Tuple[GAMEMODE, SUITS]:
        """
        :return: Game mode and hokm suit
        """
        result = super().make_hakem(middle_hand)

        # set new deck
        for i in range(len(self.deck.cards)):
            self.game_state[i] = self.deck.cards[i].id
        # set widow cards
        # for i in range(4):
        #     self.game_state[PLAYER_INITIAL_CARDS+i] = self.saved_deck[i].id
        return result

    def hokm_has_been_determined(self, game_mode, hokm_suit):
        # self.game_state[-1] = game_mode
        # self.game_state[-2] = hokm_suit
        pass

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

    def win_trick(self, hand: List[Card], winner_id: int, first_player: int):
        # for i in range(len(hand)):
        #     self.game_state[self.PLAYED_CARD_OFFSET + self.trick_number * 4 + (first_player + i) % 4] = hand[i].id

        super().win_trick(hand, winner_id, first_player)

    def build_model(self):
        pass

class PPOPlayer(IntelligentPlayer):

    def build_model(self):
        state_dim = number_of_params
        action_dim = ACTION_DIM
        #############################################
        n_latent_var = 64           # number of variables in hidden layer
        lr = 0.002
        betas = (0.9, 0.999)
        gamma = 0.99                # discount factor
        K_epochs = 4                # update policy for K epochs
        eps_clip = 0.2              # clip parameter for PPO
        #############################################
        self.memory = Memory()
        self.ppo = PPO(state_dim, action_dim, n_latent_var, lr, betas, gamma, K_epochs, eps_clip)

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
        copy_current_hand = current_hand[:]
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
                self.give_reward(invalid_card_reward, False)
        print(f"Good card after {invalid_count} tries -> {selected_card.id}")
        # remove card from game state
        for i in range(PLAYER_INITIAL_CARDS):
            if self.game_state[i] == selected_card.id:
                self.game_state[i] = NOT_SET
                break
        else:
            raise ValueError("can't find selected card: {}".format(selected_card.id))

        return self.deck.pop_card_from_deck(selected_card)

    def give_reward(self, reward: int, done: bool):
        self.memory.rewards.append(reward)
        self.memory.is_terminals.append(done)

    def request_action(self, game_state: List):
        return self.ppo.policy.act(np.array(game_state), self.memory)

    def end_round(self, team1_score: int, team2_score: int):
        if self.player_id in [0, 2]:
            for i in range(PLAYER_INITIAL_CARDS-1):
                self.give_reward(team1_score - team2_score, False)
            self.give_reward(team1_score - team2_score, True)
        else:
            for i in range(PLAYER_INITIAL_CARDS-1):
                self.give_reward(team2_score - team1_score, False)
            self.give_reward(team1_score - team2_score, True)
        self.ppo.update(self.memory)
        self.memory.clear_memory()

    def win_trick(self, hand: List[Card], winner_id: int, first_player: int):
        # for i in range(len(hand)):
        #     self.game_state[self.PLAYED_CARD_OFFSET + self.trick_number * 4 + (first_player + i) % 4] = hand[i].id

        super().win_trick(hand, winner_id, first_player)

        if winner_id == self.player_id or winner_id == self.team_mate_player_id:
            reward = Deck(hand).get_deck_score()
        else:
            reward = -Deck(hand).get_deck_score()
        done = True if self.trick_number == PLAYER_INITIAL_CARDS else False
        # self.give_reward(reward, done)

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
        self.q_table = np.zeros(number_of_params*(ACTION_DIM,))

    def give_reward(self, action: int, reward: int, state: List, next_state: List):
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

    def win_trick(self, hand: List[Card], winner_id: int, first_player: int):
        super().win_trick(hand, winner_id, first_player)

        if winner_id == self.player_id or winner_id == self.team_mate_player_id:
            reward = Deck(hand).get_deck_score()
        else:
            reward = -Deck(hand).get_deck_score()

        done = True if self.trick_number == PLAYER_INITIAL_CARDS else False
        self.give_reward(self.current_action, reward, self.current_state, self.game_state)

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
                self.give_reward(action, invalid_card_reward, self.game_state, self.game_state)
        print(f"Good card after {invalid_count} tries -> {selected_card.id}")
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


