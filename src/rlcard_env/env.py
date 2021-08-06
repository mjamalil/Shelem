import numpy as np

from rlcard.envs import Env

from rlcard_env.game import ShelemGame
from rlcard_env.game_state import NUMBER_OF_PARAMS


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
