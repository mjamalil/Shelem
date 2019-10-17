from dealer.Utils import SUITS
from players.Player import BEST_SUIT


class RuleException(Exception):
    pass


def max_at_the_moment(**kwargs):
    remained_cards = kwargs['remained_cards']
    suit = kwargs['follow_suit']
    if remained_cards[suit]:
        return max(remained_cards[suit])
    raise RuleException(f'no cards remained in this suit[{suit}]')


def return_max_in_suit(**kwargs):
    my_cards = kwargs['my_cards']
    suit = kwargs['follow_suit']
    if my_cards[suit]:
        return suit, -1
    raise RuleException(f'no cards remained in this suit[{suit}]')


def return_min_in_suit(**kwargs):
    my_cards = kwargs['my_cards']
    suit = kwargs['follow_suit']
    if my_cards[suit]:
        return suit, -1
    raise RuleException(f'no cards remained in this suit[{suit}]')


def return_min_in_any_suit(**kwargs):
    my_cards = kwargs['my_cards']
    suit = kwargs['follow_suit']
    if suit == SUITS.NEITHER:
        return None
    suit = my_cards.most_common[BEST_SUIT][0]
    return suit, 0


def return_best_if_adds_value(**kwargs):
    """
    assuming we have the suit
    """
    my_cards = kwargs['my_cards']
    suit = kwargs['follow_suit']
    current_hand = kwargs['current_hand']
    if max(my_cards[suit]) > max(current_hand):
        return suit, -1
    return suit, 0


class Rule:
    rules = [
        {
            'description': '2nd_player',
            'condition': {
                'turn': 2,
                'have_suit': True,
                'max_card': max_at_the_moment
            },
            'action': return_max_in_suit
        },
        {
            'description': '3rd_player',
            'condition': {
                'turn': 3,
                'have_suit': True,
                'max_card': max_at_the_moment
            },
            'action': return_max_in_suit
        },
        {
            'description': '3rd_player should play his max',
            'condition': {
                'turn': 3,
                'have_suit': True,
            },
            'action': return_best_if_adds_value
        },
        {
            'description': '4th_player',
            'condition': {
                'turn': 4,
                'have_suit': True,
                'max_card': max_at_the_moment
            },
            'action': return_max_in_suit
        },
        {
            'description': 'return min if no option',
            'condition': {
                'have_suit': True,
            },
            'action': return_min_in_suit
        },
        {
            'description': 'default',
            'condition': {
                'have_suit': False,
            },
            'action': return_min_in_any_suit
        },
    ]
    @staticmethod
    def get_the_value(value, **kwargs):
        if callable(value):
            return value(**kwargs)
        return value

    @classmethod
    def apply_knowledge(cls, **kwargs):
        """
        apply the current knowledge on the game to perform the best action
        :param kwargs: misc arguments needed as inputs
        :return: return a card
        """
        applied = []
        for rule in cls.rules:
            applied.clear()
            for condition in rule['condition']:
                try:
                    result = kwargs.get(condition) == cls.get_the_value(rule['condition'][condition], **kwargs)
                except RuleException:
                    break
                if result is False:
                    break
            else:
                return cls.get_the_value(rule['action'], **kwargs)
        return None
