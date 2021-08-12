import random
from typing import Tuple, List

from dealer.Card import Card
from dealer.Deck import Deck
from dealer.Utils import InvalidActionError
from players.Enum import GAMEMODE, SUITS, colors, SAFE_BET


class Bet:
    def __init__(self, player_id, bet_score):
        self.player_id = player_id
        self.bet_score = bet_score

    @property
    def id(self):
        return self.player_id

    @property
    def bet(self):
        return self.bet_score

    def __str__(self):
        return "Bet(player_id=%r, score=%r)" % (self.id, self.bet)


class Player:
    def __init__(self, player_id, team_mate_player_id):
        self.deck = Deck()
        self.saved_deck = Deck()
        self.is_hakem = False
        self.game_has_begun = False
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NOSUIT
        self.player_id = player_id
        self.team_mate_player_id = team_mate_player_id
        self.trick_number = 0
        self.hakem_bid = 0
        # stat variables
        self.nl_double = 0
        self.l_shelem = 0
        self.nl_success = 0
        self.l_success = 0
        self.nl_fail = 0
        self.l_fail = 0
        self.nl_shelem = 0
        self.l_double = 0

    def __str__(self):
        return f"Player{self.player_id}"

    def begin_round(self, deck: Deck):
        self.deck = deck
        self.game_has_begun = True
        self.saved_deck = Deck()
        self.trick_number = 0

    def end_round(self, hakem_id: int, team1_score: int, team2_score: int):
        if hakem_id in [self.player_id, self.team_mate_player_id]:
            if team2_score == 0:
                self.l_shelem += 1
            elif team1_score >= self.hakem_bid.bet_score:
                self.l_success += 1
            elif team1_score > team2_score:
                self.l_fail += 1
            else:
                self.l_double += 1
        else:
            if team1_score == 0:
                self.nl_shelem += 1
            elif team2_score >= self.hakem_bid.bet_score:
                self.nl_fail += 1
            elif team2_score > team1_score:
                self.nl_success += 1
            else:
                self.nl_double += 1

    def set_hokm_and_game_mode(self, game_mode: GAMEMODE, hokm_suit: SUITS, hakem: int):
        self.game_mode = game_mode
        self.hokm_suit = hokm_suit

    def card_has_been_played(self, current_hand: List, current_suit: SUITS):
        pass

    def end_trick(self, hand: List[Card], winner_id: int):
        # calculate reward
        self.trick_number += 1
        if self.player_id == winner_id:
            self.saved_deck += hand

    def play_random_card(self, current_hand: List, current_suit: SUITS) -> Card:
        return self.deck.pop_random_from_suit(current_suit)

    def pop_card_from_deck(self, card: int, current_suit: SUITS):
        try:
            selected_card = self.deck.get_by_value(card)
            if self.deck.has_suit(current_suit):
                if selected_card.suit != current_suit:
                    raise InvalidActionError
        except ValueError:
            raise InvalidActionError
        return self.deck.pop_card_from_deck(selected_card)

    def pop_card_from_deck2(self, card: int, current_suit: SUITS):
        try:
            selected_card = self.deck.get_by_index(card)
            if self.deck.has_suit(current_suit):
                if selected_card.suit != current_suit:
                    raise InvalidActionError
        except IndexError:
            raise InvalidActionError
        return self.deck.pop_card_from_deck(selected_card)

    def decide_game_mode(self, middle_hand: Deck):
        self.deck += middle_hand
        return GAMEMODE.SARAS

    def decide_trump(self) -> SUITS:
        """
        :return: Game mode and hokm suit 
        """
        if not self.game_has_begun:
            raise ValueError("Game has not started yet")
        self.is_hakem = True

        new_deck = Deck([])
        discarding_indices, game_mode, hokm_suit = self.discard_cards_from_leader()
        for ind in range(16):
            if ind in discarding_indices:
                self.saved_deck += self.deck[ind]
            else:
                new_deck += self.deck[ind]
        self.deck = new_deck
        return hokm_suit

    def hokm_has_been_determined(self, game_mode: GAMEMODE, hokm_suit: SUITS, bid: Bet):
        self.hakem_bid = bid

    def play_a_card(self, current_hand: List, current_suit: SUITS) -> Card:
        """
        :return: pops and plays the best available card in the current hand
        request action
        """
        return self.deck.pop_random_from_suit(current_suit)

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Score should be strictly > previous_last_bet
        """
        # TODO: NotImplemented
        return Bet(self.player_id, SAFE_BET)
        choice = random.random()
        if choice < 0.4:
            return Bet(self.player_id, 0)
        elif choice < 0.7:
            return Bet(self.player_id, random.randint(20, 22) * 5)
        elif choice < 0.9:
            return Bet(self.player_id, random.randint(23, 25) * 5)
        elif choice < 0.97:
            return Bet(self.player_id, random.randint(26, 30) * 5)
        else:
            return Bet(self.player_id, random.randint(31, 33) * 5)

    def discard_cards_from_leader(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        return random.sample(range(16), 4), self.game_mode, self.deck.cards[0].suit

    def print_game_stat(self):
        print()
        print(f"{colors.GREEN}Non-Leader Double:\t{self.nl_double}{colors.ENDC}")
        print(f"{colors.GREEN}Leader Shelem:\t{self.l_shelem}{colors.ENDC}")
        print(f"{colors.GREEN}Non-Leader Success:\t{self.nl_success}{colors.ENDC}")
        print(f"{colors.GREEN}Leader Success:\t{self.l_success}{colors.ENDC}")
        print("--------------------")
        print(f"{colors.RED}Non-Leader fail:\t{self.nl_fail}{colors.ENDC}")
        print(f"{colors.RED}Leader fail:\t{self.l_fail}{colors.ENDC}")
        print(f"{colors.RED}Non-Leader Shelem:\t{self.nl_shelem}{colors.ENDC}")
        print(f"{colors.RED}Leader Double:\t{self.l_double}{colors.ENDC}")