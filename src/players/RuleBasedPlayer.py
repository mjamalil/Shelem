from typing import Tuple, List
from collections import Counter

from dealer.Card import Card
from dealer.Deck import Deck
from players.IntelligentPlayer import IntelligentPlayer
from players.Enum import *

class RuleBasedPlayer(IntelligentPlayer):

    def begin_round(self, deck: Deck):
        super().begin_round(deck)
        self.played_cards = ([], [], [], [], [])

    def win_trick(self, hand: List[Card], winner_id: int):
        super().win_trick(hand, winner_id)
        for c in hand:
            self.played_cards[c.suit].append(c.value)

    def discard_cards_from_leader_advanced(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        self.deck._cards = sorted(self.deck._cards)
        cnts = Counter()
        mappings = {}
        for ind, card in enumerate(self.deck._cards):
            cnts[card.suit] += 1
            if card.suit not in mappings:
                mappings[card.suit] = []
            mappings[card.suit].append(ind)
        hokm_suit = cnts.most_common()[0][0]
        saving_hand = []
        last_index = -1
        while len(saving_hand) < 4:
            lst = mappings[cnts.most_common()[last_index][0]]
            saving_hand.append(lst.pop())
            if not lst:
                last_index -= 1
        return tuple(saving_hand), self.game_mode, hokm_suit

    def play_a_card(self,  current_hand: List, current_suit: SUITS) -> Card:
        turn = len(current_hand)
        # print("*"*40)
        # print(self.deck)
        if turn == 0:
            card = self.play_turn0(current_suit)
        elif turn == 1:
            card = self.play_turn1(current_hand, current_suit)
        elif turn == 2:
            card = self.play_turn2(current_hand, current_suit)
        elif turn == 3:
            card = self.play_turn3(current_hand, current_suit)
        else:
            raise RuntimeError("Invalid turn")
        return self.deck.pop_card_from_deck(card)

    def play_turn0(self, current_suit):
        for c in reversed(self.deck.cards):
            if current_suit == SUITS.NOSUIT or c.suit == current_suit:
                if self.is_this_the_best_card(c):
                    if c.suit == self.hokm_suit:
                        if self.should_play_hokm():
                            return c
                    else:
                        return c
        return self.play_lowest_card(current_suit)

    def play_turn1(self, current_hand, current_suit):
        if self.deck.has_suit(current_suit):
            for c in reversed(self.deck.cards):
                same_suit_enforce = c.suit == current_suit
                if same_suit_enforce and self.is_this_the_best_card(c):
                    return c
        else:
            # Try to boresh
            best_card = self.best_card_in_trick(current_hand, current_suit)
            for c in self.deck.cards:
                if Card.compare(c, best_card, self.game_mode, self.hokm_suit, current_suit) > 0:
                    return c
        return self.play_lowest_card(current_suit)

    def play_turn2(self, current_hand, current_suit):
        teammate_card = current_hand[-2]
        opponent_card = current_hand[-1]
        if self.deck.has_suit(current_suit):
            for c in reversed(self.deck.cards):
                same_suit_enforce = c.suit == current_suit
                better_value = Card.compare(c, opponent_card, self.game_mode, self.hokm_suit, current_suit) > 0
                teammate_difference = Card.compare(c, teammate_card, self.game_mode, self.hokm_suit, current_suit) > 1
                if same_suit_enforce and better_value and teammate_difference:
                    return c
        else:
            is_teammate_good = self.is_this_the_best_card(teammate_card)
            for c in self.deck.cards:
                if is_teammate_good:
                    has_opponent_boresh = Card.compare(
                        opponent_card, teammate_card, self.game_mode, self.hokm_suit, current_suit) > 0
                    better_boresh = Card.compare(c, opponent_card, self.game_mode, self.hokm_suit, current_suit) > 0
                    if has_opponent_boresh and better_boresh:
                        return c
                else:
                    my_boresh = Card.compare(c, teammate_card, self.game_mode, self.hokm_suit, current_suit) > 0
                    better_boresh = Card.compare(c, opponent_card, self.game_mode, self.hokm_suit, current_suit) > 0
                    if my_boresh and better_boresh:
                        return c
        return self.play_lowest_card(current_suit)

    def play_turn3(self, current_hand, current_suit):
        best_card = self.best_card_in_trick(current_hand, current_suit)
        teammate_card = current_hand[-2]
        if teammate_card == best_card:
            return self.play_lowest_card(current_suit)
        for c in self.deck.cards:
            better_value = Card.compare(c, best_card, self.game_mode, self.hokm_suit, current_suit) > 0
            if self.deck.has_suit(current_suit):
                same_suit_enforce = c.suit == current_suit
                if same_suit_enforce and better_value:
                    return c
            elif better_value:
                return c
        return self.play_lowest_card(current_suit)

    def best_card_in_trick(self, current_hand: List, current_suit: SUITS):
        if len(current_hand) == 0:
            raise RuntimeError("nobody has played")
        best_card = current_hand[0]
        for c in current_hand:
            if Card.compare(c, best_card, self.game_mode, self.hokm_suit, current_suit) > 0:
                best_card = c
        return best_card

    def play_lowest_card(self, current_suit: SUITS):
        # print("Playing lowest card")
        for c in self.deck.cards:
            if c.suit == current_suit:
                return c
        return self.deck.cards[0]

    def is_this_the_best_card(self, card: Card):
        for value in VALUES:
            has_better_value = card.value.value.get_value(self.game_mode) < value.value.get_value(self.game_mode)
            has_not_been_played = value not in self.played_cards[card.suit]
            if has_better_value and has_not_been_played:
                return False
        return True

    def should_play_hokm(self):
        my_hokm_count = 0
        for c in self.deck.cards:
            if c.suit == self.hokm_suit:
                my_hokm_count += 1
        if len(self.played_cards[self.hokm_suit]) + my_hokm_count == NUM_HOKM_CARDS:
            return False
        return True
