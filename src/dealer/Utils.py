from enum import Enum, auto


class OrderedEnum(Enum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class SUITS(Enum):
    DIAMONDS = auto()
    CLUBS = auto()
    HEARTS = auto()
    SPADES = auto()
    NEITHER = auto()


class GAMEMODE(Enum):
    NORMAL = "normal"
    SARAS = "saras"
    NARAS = "naras"
    ACE_NARAS = "acenaras"


class RankedValue:
    def __init__(self, name: str, normal_value: int, naras_value: int, ace_naras_value: int):
        self.name = name
        self.normal_value = normal_value
        self.naras_value = naras_value
        self.ace_naras_value = ace_naras_value

    # def get_value(self):
    #     from dealer.Game import game_mode
    #     if game_mode is None:
    #         raise RuntimeError('Game mode is not defined yet')
    #     if game_mode == GAMEMODE.NORMAL or game_mode == GAMEMODE.SARAS:
    #         return self.normal_value
    #     elif game_mode == GAMEMODE.NARAS:
    #         return self.naras_value
    #     elif game_mode == GAMEMODE.ACE_NARAS:
    #         return self.ace_naras_value
    #     else:
    #         raise NotImplementedError


class VALUES(Enum):
    ACE =   RankedValue("A ",   13, 1, 13)
    KING =  RankedValue("K ",  12, 2, 1)
    QUEEN = RankedValue("Q ", 11, 3, 2)
    JACK =  RankedValue("J ",  10, 4, 5)
    TEN =   RankedValue("10",    9,  5, 3)
    NINE =  RankedValue("9 ",     8,  6, 4)
    EIGHT = RankedValue("8 ",     7,  7, 5)
    SEVEN = RankedValue("7 ",     6,  8, 6)
    SIX =   RankedValue("6 ",     5,  9, 7)
    FIVE =  RankedValue("5 ",     4, 10, 8)
    FOUR =  RankedValue("4 ",     3, 11, 9)
    THREE = RankedValue("3 ",     2, 12, 10)
    TWO =   RankedValue("2 ",     1, 13, 11)
    JOKER = RankedValue("Jokers", 0,  0, 12)

NORMAL_RANKS = {
    "Ace": 13,
    "King": 12,
    "Queen": 11,
    "Jack": 10,
    "10": 9,
    "9": 8,
    "8": 7,
    "7": 6,
    "6": 5,
    "5": 4,
    "4": 3,
    "3": 2,
    "2": 1,
    "Joker": 0
}

SARAS_RANKS = NORMAL_RANKS

NARAS_RANKS = {
    "Ace": 1,
    "King": 2,
    "Queen": 3,
    "Jack": 4,
    "10": 5,
    "9": 6,
    "8": 7,
    "7": 8,
    "6": 9,
    "5": 10,
    "4": 11,
    "3": 12,
    "2": 13,
    "Joker": 0
}

ACE_NARAS_RANKS = {
    "King": 1,
    "Queen": 2,
    "Jack": 3,
    "10": 4,
    "9": 5,
    "8": 6,
    "7": 7,
    "6": 8,
    "5": 9,
    "4": 10,
    "3": 11,
    "2": 12,
    "Ace": 13,
    "Joker": 0
}


def _reverse_mapper(rank_set):
    return {v: k for k, v in rank_set.items()}


# REVERSE_SUITS = _reverse_mapper(SUITS)
REVERSE_ACE_NARAS_RANKS = _reverse_mapper(ACE_NARAS_RANKS)
REVERSE_NARAS_RANKS = _reverse_mapper(NARAS_RANKS)
REVERSE_NORMAL_RANKS = _reverse_mapper(NORMAL_RANKS)
REVERSE_SARAS_RANKS = _reverse_mapper(NARAS_RANKS)


class GameConfig:
    game_mode = None
    hokm_suit = None
