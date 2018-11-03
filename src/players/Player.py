import random
from typing import Tuple, List

from dealer.Card import Card
from dealer.Deck import Deck, SortedCards
from dealer.Utils import GAMEMODE, SUITS


class Bet(object):
    def __init__(self, player_id, bet_score):
        self.player_id = player_id
        self.bet_score = bet_score

    @property
    def id(self):
        return self.player_id

    @property
    def bet(self):
        return self.bet_score

    def __repr__(self):
        return "Bet(player_id=%r, score=%r)" % (self.id, self.bet)


class Player(object):
    def __init__(self, player_id, team_mate_player_id):
        self.cards = SortedCards()
        self.saved_deck = Deck()
        self.is_hakem = False
        self.game_has_begun = False
        self.game_mode = GAMEMODE.NORMAL
        self.hokm_suit = SUITS.NEITHER
        self.player_id = player_id
        self.team_mate_player_id = team_mate_player_id

    def begin_game(self, deck: Deck):
        self.cards += Deck
        self.game_has_begun = True
        self.saved_deck = Deck()

    def set_hokm_and_game_mode(self, game_mode: GAMEMODE, hokm_suit: SUITS):
        self.game_mode = game_mode
        self.hokm_suit = hokm_suit

    def store_hand(self, hand: List[Card]):
        self.saved_deck += hand

    def init_hakem(self, middle_hand: Deck)-> Tuple[GAMEMODE, SUITS]:
        """ 
        :return: Game mode and hokm suit 
        """
        if not self.game_has_begun:
            raise ValueError("Game has not started yet")
        self.is_hakem = True
        self.cards += middle_hand

        discarding_cards, game_mode, hokm_suit = self.decide_hokm()
        for card in discarding_cards:
            self.saved_deck += self.cards[card[0]][card[1]]

        for card in discarding_cards:
            self.cards[card[0]].pop(card[1])
            
        return game_mode, hokm_suit

    def play_a_card(self, hands_played: List[List[Card]], current_hand: List[Card]) -> Card:
        """
        :return: pops and plays the best available card in the current hand  
        """
        # TODO: NotImplemented

        if current_hand:
            suit = current_hand[0].suit
        # first player and first hand
        elif not hands_played and not current_hand:
            suit = self.hokm_suit
        else:
            suit = SUITS.NEITHER
        return self.cards.pop_random_from_suit(suit)

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Score should be strictly > previous_last_bet
        """
        # TODO: NotImplemented
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

    def decide_hokm(self) -> Tuple[List[Tuple[SUITS, int]], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        if self.is_hakem == False:
            raise Exception("non-hakem player is discarding cards")
        random_list = []
        indices = random.sample(range(16), 4)
        for ind in indices:
            try:
                random_list.append(self.cards.get_suit_number(ind))
            except KeyError:
                raise RuntimeError("not enough cards in hakem's hand")

        return random_list, self.game_mode, self.cards[0].suit
        
