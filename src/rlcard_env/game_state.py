from enum import IntEnum, auto

from dealer.Deck import Deck
from dealer.Logging import Logging
from players.Enum import DECK_SIZE, NUM_SUITS, NUM_PLAYERS

NOT_SET = 0

class STATE(IntEnum):
    MY_HAND = auto()
    LEADER = auto()
    CRR_TRUMP = auto()
    CRR_SUIT = auto()
    CRR_TRICK = auto()
    PLAYED_CARDS = auto()


Dimension = {
    STATE.MY_HAND: DECK_SIZE,
    STATE.CRR_TRICK: 3*DECK_SIZE,
    STATE.PLAYED_CARDS: DECK_SIZE,
    STATE.CRR_TRUMP: NUM_SUITS,
    STATE.CRR_SUIT : NUM_SUITS,
    STATE.LEADER: NUM_PLAYERS,
}
Active = {
    STATE.MY_HAND: True,
    STATE.CRR_TRICK: True,
    STATE.PLAYED_CARDS: True,
    STATE.CRR_TRUMP: False,
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
        self.played_card_cutoff = 36
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
        if sub_state == STATE.PLAYED_CARDS and index < self.played_card_cutoff:
            return
        self._state[self._state_index[sub_state] + index] = value

    def log(self):
        DummyDeck = Deck()
        DummyDeck.deal()
        for d in Dimension:
            if Active[d]:
                idx1 = self._state_index[d]
                idx2 = idx1 + Dimension[d]
                if d in [STATE.MY_HAND, STATE.PLAYED_CARDS]:
                    my_hand = []
                    for i in range(idx1, idx2):
                        if self._state[i] == 1:
                            my_hand.append(DummyDeck.get_by_value(i-idx1))
                    Logging.debug("{} -> {}".format(d.name, my_hand))
                elif d == STATE.CRR_TRICK:
                    current_trick = []
                    for i in range(idx1, idx2):
                        card_idx = (i - idx1) % DECK_SIZE
                        if self._state[i] == 1:
                            current_trick.append(DummyDeck.get_by_value(card_idx))
                    Logging.debug("{} -> {}".format(d.name, current_trick))
                else:
                    Logging.debug("{} -> {}".format(d.name, self._state[idx1:idx2]))



