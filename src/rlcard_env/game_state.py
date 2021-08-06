from enum import IntEnum, auto

from players.Enum import DECK_SIZE, NUM_SUITS, NUM_PLAYERS

NOT_SET = 0

class STATE(IntEnum):
    MY_CARDS = auto()
    LEADER = auto()
    CRR_TRUMP = auto()
    CRR_SUIT = auto()
    CRR_TRICK = auto()
    PLAYED_CARDS = auto()


Dimension = {
    STATE.MY_CARDS: DECK_SIZE,
    STATE.CRR_TRICK: 3*DECK_SIZE,
    STATE.PLAYED_CARDS: DECK_SIZE,
    STATE.CRR_TRUMP: NUM_SUITS,
    STATE.CRR_SUIT : NUM_SUITS,
    STATE.LEADER: NUM_PLAYERS,
}
Active = {
    STATE.MY_CARDS: True,
    STATE.CRR_TRICK: False,
    STATE.PLAYED_CARDS: True,
    STATE.CRR_TRUMP: True,
    STATE.CRR_SUIT : True,
    STATE.LEADER: True,
}

NUMBER_OF_PARAMS = 0
for d in Dimension:
    if Active[d]:
        NUMBER_OF_PARAMS += Dimension[d]

print(f"number of parameters: {NUMBER_OF_PARAMS}")


class GameState:

    def __init__(self):
        self.reset_state()
        self._state_index = {}
        cumulative_index = 0
        for d in Dimension:
            if Active[d]:
                self._state_index[d] = cumulative_index
                cumulative_index += Dimension[d]

    @property
    def state(self):
        return self._state

    def reset_state(self):
        self._state = [NOT_SET] * NUMBER_OF_PARAMS

    def set_state(self, sub_state: STATE, index: int, value: float):
        if not Active[sub_state]:
            return
        if index >= Dimension[sub_state]:
            raise RuntimeError("invalid sub-state index:{}->{}".format(sub_state, index))
        self._state[self._state_index[sub_state] + index] = value

