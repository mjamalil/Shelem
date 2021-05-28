from enum import Enum, auto, IntEnum

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


class SUITS(IntEnum):
    DIAMONDS = auto()
    CLUBS = auto()
    HEARTS = auto()
    SPADES = auto()
    NOSUIT = auto()


class GAMEMODE(IntEnum):
    NORMAL = auto()
    SARAS = auto()
    NARAS = auto()
    ACE_NARAS = auto()


class RankedValue:
    def __init__(self, name: str, normal_value: int, naras_value: int, ace_naras_value: int):
        self.name = name
        self.normal_value = normal_value
        self.naras_value = naras_value
        self.ace_naras_value = ace_naras_value

    def get_value(self, g_mode: GAMEMODE):
        if g_mode == GAMEMODE.NORMAL or g_mode == GAMEMODE.SARAS:
            return self.normal_value
        elif g_mode == GAMEMODE.NARAS:
            return self.naras_value
        elif g_mode == GAMEMODE.ACE_NARAS:
            return self.ace_naras_value
        else:
            raise NotImplementedError


class VALUES(Enum):
    Two =   RankedValue("2 ",   1, 13, 11)
    Three = RankedValue("3 ",   2, 12, 10)
    Four =  RankedValue("4 ",   3, 11, 9)
    Five =  RankedValue("5 ",   4, 10, 8)
    Six =   RankedValue("6 ",   5, 9, 7)
    Seven = RankedValue("7 ",   6, 8, 6)
    Eight = RankedValue("8 ",   7, 7, 5)
    Nine =  RankedValue("9 ",   8, 6, 4)
    Ten =   RankedValue("10",   9, 5, 3)
    Jack =  RankedValue("J ",  10, 4, 5)
    Queen = RankedValue("Q ",  11, 3, 2)
    King =  RankedValue("K ",  12, 2, 1)
    Ace =   RankedValue("A ",  13, 1, 13)
    Joker = RankedValue("Jokers", 0, 0, 12)

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
    "2": 13,
    "3": 12,
    "4": 11,
    "5": 10,
    "6": 9,
    "7": 8,
    "8": 7,
    "9": 6,
    "10": 5,
    "Jack": 4,
    "Queen": 3,
    "King": 2,
    "Ace": 1,
    "Joker": 0
}

ACE_NARAS_RANKS = {
    "Ace": 13,
    "2": 12,
    "3": 11,
    "4": 10,
    "5": 9,
    "6": 8,
    "7": 7,
    "8": 6,
    "9": 5,
    "10": 4,
    "Jack": 3,
    "Queen": 2,
    "King": 1,
    "Joker": 0,
}

GAME_MODES = {

}