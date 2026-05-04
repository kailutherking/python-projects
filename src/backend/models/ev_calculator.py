class EVCalculator:
    """Calculate Expected Value for sports bets"""

    def __init__(self):
        """Initialize EV calculator"""
        self.bets = []

    def american_to_probability(self, american_odds: int | float) -> float:
        """
        Convert American odds to implied probability

        Example:
        -110 odds → 52.4% probability
        +150 odds → 40.0% probability
        """
        if not isinstance(american_odds, (int, float)):
            raise TypeError(f'american_odds must be numeric, got {type(american_odds).__name__}')
        if american_odds == 0:
            return 1.0
        if american_odds < 0:
            probability = abs(american_odds) / (abs(american_odds) + 100)
        else:
            probability = 100 / (american_odds + 100)

        return probability

    def calculate_ev(self, model_prob: float, american_odds: int, stake: float = 100) -> float:
        """
        Calculate Expected Value of a bet

        EV = (Win Probability x Payout) - (Loss Probability x Stake)

        Args:
            model_prob: Your predicted win probability (0.0 - 1.0)
            american_odds: Sportsbook odds (e.g., -110, +150)
            stake: Amount wagered

        Returns:
            Expected value in dollars
        """
        # Convert odds to payout
        if american_odds < 0:
            payout = stake * (100 / abs(american_odds))
        else:
            payout = stake * (american_odds / 100)

        # Calculate EV
        win_value = model_prob * payout
        loss_value = (1 - model_prob) * stake
        ev = win_value - loss_value

        return ev

    def evaluate_bet(
        self, team: str, model_prob: float, american_odds: int, stake: float = 100
    ) -> dict:
        """
        Full evaluation of a potential bet

        Returns a dictionary with:
        - Team
        - Model probability
        - Sportsbook implied probability
        - EV and EV%
        - Recommendation
        """
        book_prob = self.american_to_probability(american_odds)
        ev = self.calculate_ev(model_prob, american_odds, stake)
        ev_percent = (ev / stake) * 100

        # Determine recommendation
        if ev > 0:
            recommendation = '[BET] Positive EV'
        elif ev < -5:
            recommendation = '[AVOID] Strong Negative EV'
        else:
            recommendation = '[PASS] Slight Negative EV'

        result = {
            'team': team,
            'model_prob': f'{model_prob * 100:.1f}%',
            'book_prob': f'{book_prob * 100:.1f}%',
            'american_odds': american_odds,
            'ev_per_stake': f'${ev:.2f}',
            'ev_percent': f'{ev_percent:.1f}%',
            'recommendation': recommendation,
        }

        self.bets.append(result)
        return result

    def kelly_criterion(self, win_probability: float, american_odds: int) -> float:
        """
        Calculate optimal bet size using Kelly Criterion

        Prevents overbetting and bankroll ruin

        Kelly % = (Probability x Odds - (1 - Probability)) / Odds
        """
        decimal_odds = 100 / abs(american_odds) if american_odds < 0 else 1 + american_odds / 100

        kelly = (win_probability * decimal_odds - (1 - win_probability)) / decimal_odds

        # Return as percentage of bankroll (cap at 5% for safety)
        kelly_percent = max(0, min(kelly, 0.05))

        return kelly_percent

    def display_bet_analysis(self, bets_list: list[dict]):
        """Display formatted bet analysis"""
        print(f'\n{"=" * 100}')
        print('BET ANALYSIS')
        print(f'{"=" * 100}\n')

        for bet in bets_list:
            print(f'TEAM: {bet["team"]}')
            print(f'  Model Probability:     {bet["model_prob"]}')
            print(f'  Sportsbook Probability: {bet["book_prob"]}')
            print(f'  Odds:                  {bet["american_odds"]}')
            print(f'  EV per $100:           {bet["ev_per_stake"]}')
            print(f'  EV Percentage:         {bet["ev_percent"]}')
            print(f'  Recommendation:        {bet["recommendation"]}\n')
