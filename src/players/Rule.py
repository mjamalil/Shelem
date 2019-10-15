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


class Rule:
    rules = [
        {'name': 'first',
         'condition': {
            'turn': 2,
            'have_suit': True,
            'max_card': max_at_the_moment
            },
         'action': return_max_in_suit
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

