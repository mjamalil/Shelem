from typing import Tuple, List
import numpy as np
from numpy import ndarray

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Logging import Logging
from dealer.Utils import get_round_payoff
from players.Player import Player, Bet
from players.Enum import *
from rlcard_env.game_state import GameState, NUMBER_OF_PARAMS, STATE, GameState2, CARD_STATE


class BaseIntelligentPlayer(Player):
    hokm_suit = SUITS.NOSUIT

    def __init__(self, player_id, team_mate_player_id):
        super().__init__(player_id, team_mate_player_id)
        self.build_model()
        self.observation1 = GameState()
        self.observation = GameState2()
        self.PLAYED_CARD_OFFSET = 16
        self.agent = False

    @property
    def action_mask(self):
        valid_actions = ACTION_SIZE * [False]
        for c in self.deck:
            valid_actions[c.id] = True
        return valid_actions

    def begin_round(self, deck: Deck):
        super().begin_round(deck)
        # a series of values storing all data of a round
        # game_state = my cards + ground cards + played tricks + game status
        self.observation1.reset_state()
        self.observation.reset_state()
        for i in range(len(deck.cards)):
            self.observation1.set_state(STATE.MY_HAND, deck.cards[i].id, 1)
            self.observation.set_state(deck.cards[i].id, CARD_STATE.MY_HAND)

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Score should be strictly > previous_last_bet
        """
        # TODO: NotImplemented
        return Bet(self.player_id, SAFE_BET)

    def decide_trump(self) -> SUITS:
        trump = super().decide_trump()
        # set new deck
        for i in range(DECK_SIZE):
            self.observation1.set_state(STATE.MY_HAND, i, 0)
        for i in range(len(self.deck.cards)):
            self.observation1.set_state(STATE.MY_HAND, self.deck.cards[i].id, 1)
            self.observation.set_state(self.deck.cards[i].id, CARD_STATE.MY_HAND)
        # set widow cards
        widow_size = 4
        for i in range(widow_size):
            self.observation1.set_state(STATE.PLAYED_CARDS, self.saved_deck[i].id, 1)
            self.observation.set_state(self.saved_deck[i].id, CARD_STATE.PLAYED)
        return trump

    def set_hokm_and_game_mode(self, game_mode: GAMEMODE, hokm_suit: SUITS, hakem: int):
        super().set_hokm_and_game_mode(game_mode, hokm_suit, hakem)
        self.game_mode = game_mode
        self.hokm_suit = hokm_suit
        for i in range(SUITS.SPADES):
            self.observation1.set_state(STATE.CRR_TRUMP, i, int(hokm_suit == SUITS(i+1)))
        for i in range(NUM_PLAYERS):
            self.observation1.set_state(STATE.LEADER, i, int(i == hakem))

    def play_a_card(self, current_hand: List, current_suit: SUITS) -> Card:
        return self.deck.pop_random_from_suit(current_suit)

    def card_has_been_played(self, current_hand: List, current_suit: SUITS):
        for i in range(SUITS.SPADES):
            self.observation1.set_state(STATE.CRR_SUIT, i, int(current_suit == SUITS(i+1)))
        for i in range(NUM_PLAYERS):
            if i == self.player_id or current_hand[i] is None:
                continue
            player_idx_in_trick = (i - self.player_id - 1 + NUM_PLAYERS) % NUM_PLAYERS
            self.observation1.set_state(STATE.CRR_TRICK, player_idx_in_trick*DECK_SIZE + current_hand[i].id, 1)
            self.observation.set_state(current_hand[i].id, CARD_STATE(player_idx_in_trick+1))

    def discard_cards_from_leader(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        # TODO: NotImplemented
        return super().discard_cards_from_leader()

    def end_trick(self, hand: List[Card], winner_id: int):
        super().end_trick(hand, winner_id)
        for c in hand:
            # remove card from my cards if I have it
            self.observation1.set_state(STATE.MY_HAND, c.id, 0)
            # add card to played cards
            self.observation1.set_state(STATE.PLAYED_CARDS, c.id, 1)
            self.observation.set_state(c.id, CARD_STATE.PLAYED)
        max_crr_trick_num = 3
        for i in range(max_crr_trick_num*DECK_SIZE):
            self.observation1.set_state(STATE.CRR_TRICK, i, 0)
        for i in range(SUITS.SPADES):
            self.observation1.set_state(STATE.CRR_SUIT, i, 0)

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

    def get_legal_actions(self, current_suit):
        valid_actions = []
        for c in self.deck.cards:
            if self.deck.has_suit(current_suit):
                if c.suit == current_suit:
                    valid_actions.append(c.id)
            else:
                valid_actions.append(c.id)
        return valid_actions

    def get_legal_actions2(self, current_suit):
        valid_actions = []
        for idx, c in enumerate(self.deck.cards):
            if self.deck.has_suit(current_suit):
                if c.suit == current_suit:
                    valid_actions.append(idx)
            else:
                valid_actions.append(idx)
        return valid_actions

    def build_model(self):
        pass


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
        n_latent_var = 64  # number of variables in hidden layer
        lr = 0.002
        betas = (0.9, 0.999)
        gamma = 0.99  # discount factor
        K_epochs = 4  # update policy for K epochs
        eps_clip = 0.2  # clip parameter for PPO
        #############################################
        from players.PPO import Memory, PPO
        self.memory = Memory()
        self.ppo = PPO(state_dim, action_dim, n_latent_var, lr, betas, gamma, K_epochs, eps_clip)

    def play_a_card(self, current_hand: List, current_suit: SUITS) -> Card:
        """
        :return: pops and plays the best available card in the current hand
        """
        invalid_card = True
        invalid_card_reward = -45 / self.hakem_bid.bet_score
        invalid_count = 1
        Logging.debug(self.deck)
        while invalid_card:
            try:
                valid_actions = self.get_valid_actions(current_suit)
                action = self.request_action(self.observation1, valid_actions)
                selected_card = self.deck.get_by_value(action)
            except ValueError as err:
                # print(err)
                pass

            else:
                if self.deck.has_suit(current_suit):
                    if selected_card.suit == current_suit:
                        invalid_card = False
                else:
                    invalid_card = False
            if invalid_card:
                # raise RuntimeError("invalid action")
                invalid_count += 1
                self.set_reward(invalid_card_reward, False)
        # if action >= 50:
        #     self.reward = 1
        # else:
        #     self.reward = -1
        # return self.deck.pop_random_from_suit(current_suit)
        return self.deck.pop_card_from_deck(selected_card)

    def set_reward(self, reward: float, done: bool):
        # print("reward: {}".format(reward))
        self.memory.rewards.append(reward)
        self.memory.is_terminals.append(done)

    def request_action(self, game_state: List, valid_actions: ndarray):
        action = self.ppo.policy_old.act(np.array(game_state), self.memory, valid_actions)
        # action = self.ppo.policy_old.act(np.array(game_state), self.memory)
        # idx = torch.argmax(self.ppo.policy_old.action_probs)
        # print("ideal card: {}".format(Card.description(idx.item())))
        # for idx, a in enumerate(self.ppo.policy_old.new_probs):
        #     if a.item() != 0.0:
        #         selected_card = self.deck.get_by_value(idx)
        #         print("{} ->{: .2f}%".format(selected_card, a.item() * 100))
        return action

    def begin_round(self, deck: Deck):
        super().begin_round(deck)
        self.reward = 0

    def end_round(self, hakem_id: int, team1_score: int, team2_score: int):
        super().end_round(hakem_id, team1_score, team2_score)
        # only works for first player as ppo
        final_score1, final_score2, round_reward = get_round_payoff(hakem_id, self.hakem_bid.bet_score, team1_score, team2_score)
        round_reward += self.reward
        round_reward = sorted((-1, (final_score1 - final_score2) / (2 * MAX_SCORE), 1))[1]
        self.set_reward(round_reward, True)
        self.ppo.update(self.memory)
        self.memory.clear_memory()

    def end_trick(self, hand: List[Card], winner_id: int):
        super().end_trick(hand, winner_id)
        if winner_id == self.player_id or winner_id == self.team_mate_player_id:
            self.reward = Deck(hand).get_deck_score() / MAX_SCORE
        else:
            self.reward = 0
        # self.reward = 0
        done = True if self.trick_number == PLAYER_INITIAL_CARDS else False
        if not done:
            self.set_reward(self.reward, done)


