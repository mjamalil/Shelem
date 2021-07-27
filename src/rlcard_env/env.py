import numpy as np

from rlcard.envs import Env

from players.Enum import *
from rlcard_env.game import ShelemGame


class ShelemRlEnv(Env):
    state_shape_x = 1

    def __init__(self, config):
        self.name = 'shelem-rlcard'
        self.game = ShelemGame(game_end=0, verbose=1)
        super().__init__(config)
        self.state_shape = [[self.state_shape_x, NUMBER_OF_PARAMS] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def _extract_state(self, state):
        legal_action_id = self._get_legal_actions()
        # obs = np.zeros((self.state_shape_x, DECK_SIZE), dtype=int)
        # obs[0] = np.array(state[:STATE_CRR_TRICK_IDX])  # my cards
        # obs[1] = np.array(state[STATE_CRR_TRICK_IDX:STATE_CRR_TRICK_IDX+DECK_SIZE])  # current trick
        # obs[2] = np.array(state[STATE_CRR_TRICK_IDX+DECK_SIZE:STATE_CRR_TRICK_IDX+2*DECK_SIZE])
        # obs[3] = np.array(state[STATE_CRR_TRICK_IDX+2*DECK_SIZE:STATE_CRR_TRICK_IDX+3*DECK_SIZE])
        # obs[4] = np.array(state[STATE_PLAYED_CARDS_IDX:STATE_PLAYED_CARDS_IDX+DECK_SIZE])  # Dead cards
        # obs[5] = np.array(state[STATE_TRUMP_IDX:STATE_TRUMP_IDX+4] + state[STATE_SUIT_IDX:STATE_SUIT_IDX+4] + [0] * 48)  # Trump
        obs = np.array(state)
        extracted_state = {
            'obs': obs,
            'legal_actions': legal_action_id,
            'raw_obs': state,
            'raw_legal_actions': list(legal_action_id.keys()),
        }
        return extracted_state

    def get_payoffs(self):
        return np.array(self.game.get_payoffs())

    def _decode_action(self, action_id):
        return action_id

    def _get_legal_actions(self):
        legal_ids = {action: None for action in self.game.get_legal_actions()}
        return legal_ids
