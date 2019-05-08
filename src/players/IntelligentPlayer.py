import random
from typing import Tuple, List

from dealer.Card import Card
from dealer.Utils import GAMEMODE, SUITS
from players.Player import Player, Bet


class IntelligentPlayer(Player):
    def __init__(self, player_id, team_mate_player_id):
        super(IntelligentPlayer, self).__init__(player_id, team_mate_player_id)

    def make_bet(self, previous_last_bets: List[Bet]) -> Bet:
        """
        :return: Pass / 100 < score < 165 / Shelem / Sar-Shelem / Super-Shelem
         Base on a 12-card hand available
         Sacore should be strictly > previous_last_bet
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

    def discard_cards_decide_hokm(self) -> Tuple[Tuple[int, int, int, int], GAMEMODE, SUITS]:
        """
        if its a hakem hand, selects 4 indices out of 16 and removes them out of hand and saves them in saved_deck 
        :return: 
        """
        # TODO: NotImplemented
        suit_select = random.randint(1, 4)
        if suit_select == 1:
            hokm_suit = SUITS.SPADES
        elif suit_select == 2:
            hokm_suit = SUITS.HEARTS
        elif suit_select == 3:
            hokm_suit = SUITS.DIAMONDS
        else:
            hokm_suit = SUITS.CLUBS
        return random.sample(range(16), 4), self.game_mode, hokm_suit

    def play_a_card(self, hands_played: List[List[Card]], current_hand: List[Card]) -> Card:
        """
        :return: pops and plays the best available card in the current hand  
        """
        # TODO: NotImplemented
        return self.deck.cards.popleft()

    def encode_last_bets(self, all_bets: List[Bet]):
        score_mappings = {v: k for k, v in enumerate([x*5 for x in ([0] + list(range(20, 36)))])}
        opponent_1_id = (self.player_id + 1) % 4
        encoding_vector = [0] * (len(score_mappings)*4 + 52)
        for bet in all_bets:
            score_id = score_mappings[int(bet.bet)]
            if bet.id == self.player_id:
                encoding_vector[score_id] = 1
            elif bet.id == self.team_mate_player_id:
                encoding_vector[score_id + len(score_mappings)] = 1
            elif bet.id == opponent_1_id:
                encoding_vector[score_id + 2 * len(score_mappings)] = 1
            else:
                encoding_vector[score_id + 3 * len(score_mappings)] = 1
        for card in self.deck:
            val = card.value.value.normal_value
            st = card.suit.value - 1
            encoding_vector[st * 13 + val + len(score_mappings)*4] = 1
        return encoding_vector