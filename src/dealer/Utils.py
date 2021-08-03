class ThreeConsecutivePassesException(Exception):
    pass

class InvalidActionError(Exception):
    pass


def get_round_payoff(hakem_id: int, hakem_bet: int, team1_score: int, team2_score: int):
    if hakem_id in [0, 2]:
        if team2_score == 0:
            return 2 * hakem_bet, team2_score, 1.0
        elif team1_score >= hakem_bet:
            return hakem_bet, team2_score, 0.5
        elif team1_score > team2_score:
            return -hakem_bet, team2_score, -0.7
        else:
            return -2 * hakem_bet, team2_score, -1.0
    else:
        if team1_score == 0:
            return team1_score, 2 * hakem_bet, -0.5
        elif team2_score >= hakem_bet:
            return team1_score, hakem_bet, 0.0
        elif team2_score > team1_score:
            return team1_score, -hakem_bet, 0.5
        else:
            return team1_score, -2 * hakem_bet, 1.0
