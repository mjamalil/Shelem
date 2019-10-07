from unicards import unicard

from dealer.Utils import SUITS, GAMEMODE, VALUES


class Card:
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

    # def __gt__(self, other):
    #     from dealer.Game import game_mode, hokm_suit
    #     if isinstance(other, Card):
    #         if game_mode == GAMEMODE.NORMAL:
    #             return (self.suit == other.suit and self.ranked_value > other.ranked_value) or \
    #                    (self.suit != other.suit and self.suit == hokm_suit)
    #         else:
    #             return self.suit == other.suit and self.ranked_value > other.ranked_value
    #     raise RuntimeError('Comparing card with something else')
    #
    # def __lt__(self, other):
    #     if isinstance(other, Card):
    #         if game_mode == GAMEMODE.NORMAL:
    #             return (self.suit == other.suit and self.ranked_value < other.ranked_value) or \
    #                    (self.suit != other.suit and other.suit == hokm_suit)
    #         else:
    #             return self.suit == other.suit and self.ranked_value < other.ranked_value
    #     raise RuntimeError('Comparing card with something else')

    def __hash__(self):
        return hash((self.value, self.suit))

    def __repr__(self):
        return "Card(value=%r, suit=%r)" % (self.value.name, self.suit.name)

    def __str__(self):
        return self.name

    def ranked_value(self, game_mode):
        if game_mode is None:
            raise RuntimeError('Game mode is not defined yet')
        if game_mode == GAMEMODE.NORMAL or game_mode == GAMEMODE.SARAS:
            return self.value.value.normal_value
        elif game_mode == GAMEMODE.NARAS:
            return self.value.value.naras_value
        elif game_mode == GAMEMODE.ACE_NARAS:
            return self.value.value.ace_naras_value
        else:
            raise NotImplementedError

    def is_greater(self, other, game_mode, hokm_suit):
        """
        Only the first players card is supposed to call the is_greater function to other cards
        :param other: another card to be compared
        :param game_mode: the mode in which the game is being played
        :param hokm_suit: the hokm suit is considered only if is_naras=False / can be None[saras] 
        :return:    True: self is greater
                    False: other is greater
        """
        if isinstance(other, Card):
            if game_mode == GAMEMODE.NORMAL:
                return (self.suit == other.suit and self.ranked_value(game_mode) > other.ranked_value(game_mode)) or \
                       (self.suit != other.suit and self.suit == hokm_suit)
            else:
                return self.suit == other.suit and self.ranked_value(game_mode) > other.ranked_value(game_mode)
        raise RuntimeError('Comparing card with something else')

    @staticmethod
    def card_abbrev(value, suit):
        if value.value.name.lower() == "joker":
            return "C"
        elif value.value.name == "10":
            return "T%s" % (suit.name[0])
        else:
            return "%s%s" % (value.value.name[0], suit.name[0])