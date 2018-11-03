from unicards import unicard
from dealer.Utils import SUITS, GAMEMODE, VALUES


class Card(object):
    def __init__(self, value: VALUES, suit: SUITS):
        """
        :param value: one of the key/vlues in Utils.VALUES 
        :param suit: one of the key/vlues in Utils.SUITS
        """
        self.suit = suit
        self.value = value
        self.repr = unicard(self.card_abbrev(value, suit))
        if self.value == 0:
            self.name = "Joker"
        else:
            self.name = "%s of %s" % (value.value.name.title(), suit.name.title())

    def __eq__(self, other):
        return isinstance(other, Card) and self.value == other.value and self.suit == other.suit

    def __ne__(self, other):
        return not isinstance(other, Card) or self.value != other.value or self.suit != other.suit

    def __ge__(self, other):
        if isinstance(other, Card):
            return self.value > other.value or (self.value >= other.value and self.suit >= other.suit)
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, Card):
            return self.value > other.value or (self.value >= other.value and self.suit > other.suit)
        else:
            return False

    def __hash__(self):
        return hash((self.value, self.suit))

    def __repr__(self):
        return "Card(value=%r, suit=%r)" % (self.value.name, self.suit.name)

    def __str__(self):
        return self.name

    def __lt__(self, other):
        if isinstance(other, Card):
            return True
        else:
            return False

    def compare(self, other, game_mode, hokm_suit):
        """
        Only the first players card is supposed to call the compare function to other cards
        :param other: another card to be compared
        :param game_mode: the mode in which the game is being played
        :param hokm_suit: the hokm suit is considered only if is_naras=False / can be None[saras] 
        :return:    1: self is greater
                    0: equal [must not happen]
                    -1: other is greater
                    -2: other if not a Card [error]
        """
        if isinstance(other, Card):
            my_value = self.value.value.get_value(game_mode)
            other_value = other.value.value.get_value(game_mode)
            if self.suit == other.suit:
                if my_value > other_value:
                    return 1
                elif my_value == other_value:
                    return 0
                else:
                    return -1
            elif game_mode == GAMEMODE.NORMAL:
                if hokm_suit == SUITS.NEITHER:
                    raise ValueError("In normal game mode you cannot have Hokm == Neither")
                if self.suit == hokm_suit:
                    return 1
                elif other.suit == hokm_suit:
                    return -1
                else:
                    return 1
            else:
                return 1
        else:
            return -2

    @staticmethod
    def card_abbrev(value, suit):
        if value.value.name.lower() == "joker":
            return "C"
        elif value.value.name == "10":
            return "T%s" % (suit.name[0])
        else:
            return "%s%s" % (value.value.name[0], suit.name[0])
