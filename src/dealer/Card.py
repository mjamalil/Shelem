from unicards import unicard
from dealer.Utils import SUITS, GAMEMODE, VALUES, NORMAL_RANKS


class Card:
    def __init__(self, id: int, value: VALUES, suit: SUITS):
        """
        :param value: one of the key/values in Utils.VALUES
        :param suit: one of the key/values in Utils.SUITS
        """
        self.id = id
        self.suit = suit
        self.value = value
        self.repr = unicard(self.card_abbrev(value, suit))
        if self.value == 0:
            self.name = "Joker"
        else:
            self.name = "%sof %s" % (value.value.name.title(), suit.name.title())

    def __eq__(self, other):
        return isinstance(other, Card) and self.value == other.value and self.suit == other.suit

    def __ne__(self, other):
        return not isinstance(other, Card) or self.value != other.value or self.suit != other.suit

    def __ge__(self, other):
        return self.id >= other.id

    def __gt__(self, other):
        return self.id > other.id

    def __le__(self, other):
        return self.id <= other.id

    def __lt__(self, other):
        return self.id < other.id

    def __hash__(self):
        return hash((self.value, self.suit))

    def __repr__(self):
        return "({}-{})".format(self.id, self.name)

    def __str__(self):
        return self.name

    @staticmethod
    def compare(first, second, game_mode, hokm_suit, current_suit):
        """
        :param first : first card to be compared
        :param second: another card to be compared
        :param game_mode: the mode in which the game is being played
        :param hokm_suit: the hokm suit is considered only if is_naras=False / can be None[saras] 
        :return:    15, -15 boresh
                    14 , -14: different suit and it's a higher card therefore
                    > 1 , < -1: same suit value difference is returned
                    0: none is bigger than the other
        """
        hokm_difference = 15
        suit_difference = 14
        if isinstance(first, Card) and isinstance(second, Card):
            my_value = first.value.value.get_value(game_mode)
            second_value = second.value.value.get_value(game_mode)
            if first.suit == second.suit:
                return my_value - second_value
            if game_mode == GAMEMODE.NORMAL:
                if hokm_suit == SUITS.NOSUIT:
                    raise ValueError("In normal game mode you cannot have Hokm == NOSUIT")
                if first.suit == hokm_suit:
                    return hokm_difference
                elif second.suit == hokm_suit:
                    return -hokm_difference
            if first.suit == current_suit:
                return suit_difference
            if second.suit == current_suit:
                return -suit_difference
            return 0
        else:
            raise ValueError("invalid value for cards")

    @staticmethod
    def card_abbrev(value, suit):
        if value.value.name.lower() == "joker":
            return "C"
        elif value.value.name == "10":
            return "T%s" % (suit.name[0])
        else:
            return "%s%s" % (value.value.name[0], suit.name[0])

    @staticmethod
    def description(value):
        suit = (SUITS)(value % 4 + 1)
        values = {v: k for k, v in NORMAL_RANKS.items()}
        value = value // 4
        return "{} of {}".format(values[value+1], suit.name)
