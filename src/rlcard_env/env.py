import numpy as np

from rlcard.envs import Env

from players.Enum import NUMBER_OF_PARAMS
from rlcard_env.game import ShelemGame

DEFAULT_GAME_CONFIG = {
    'game_num_players': 4,
}

class ShelemRlEnv(Env):

    def __init__(self, config):
        self.name = 'shelem-rlcard'
        self.default_game_config = DEFAULT_GAME_CONFIG
        self.game = ShelemGame()
        super().__init__(config)
        self.state_shape = [[NUMBER_OF_PARAMS]]
        self.action_shape = [None for _ in range(self.num_players)]

    def _extract_state(self, state):
        legal_action_id = self._get_legal_actions()
        extracted_state = {'obs': state, 'legal_actions': legal_action_id}
        return extracted_state

    def get_payoffs(self):
        return np.array(self.game.get_payoffs())

    def _decode_action(self, action_id):
        return action_id

    def _get_legal_actions(self):
        return self.game.get_legal_actions()
