"""Unit tests for EVCalculator — expected value, Kelly criterion, and bet evaluation."""

import pytest

from backend.models.ev_calculator import EVCalculator

# ---------------------------------------------------------------------------
# american_to_probability
# ---------------------------------------------------------------------------


def test_american_to_probability_negative_odds():
    """Convert negative American odds (-110, -200) to implied probability."""
    calc = EVCalculator()
    assert calc.american_to_probability(-110) == pytest.approx(110 / 210)
    assert calc.american_to_probability(-200) == pytest.approx(200 / 300)


def test_american_to_probability_positive_odds():
    """Convert positive American odds (+150, +200) to implied probability."""
    calc = EVCalculator()
    assert calc.american_to_probability(150) == pytest.approx(100 / 250)
    assert calc.american_to_probability(200) == pytest.approx(100 / 300)


def test_american_to_probability_zero():
    """Odds of 0 → 100% implied probability (degenerate)."""
    calc = EVCalculator()
    assert calc.american_to_probability(0) == pytest.approx(1.0)


def test_american_to_probability_extreme():
    """Very large positive/negative odds map to near-0 and near-1."""
    calc = EVCalculator()
    assert calc.american_to_probability(10000) == pytest.approx(100 / 10100)
    assert calc.american_to_probability(-10000) == pytest.approx(10000 / 10100)


# ---------------------------------------------------------------------------
# calculate_ev
# ---------------------------------------------------------------------------


def test_calculate_ev_positive_scenario():
    """EV is positive when model probability exceeds implied probability."""
    calc = EVCalculator()
    # -110 → implied 52.38%.  Model says 60%.  Edge → positive EV.
    ev = calc.calculate_ev(model_prob=0.60, american_odds=-110, stake=100)
    # payout = 100 * (100/110) = 90.909...
    # EV = 0.60 * 90.909 - 0.40 * 100 = 54.545 - 40 = 14.545...
    assert ev > 0
    assert ev == pytest.approx(14.545, abs=0.01)


def test_calculate_ev_negative_scenario():
    """EV is negative when model probability is below implied probability."""
    calc = EVCalculator()
    # -110 → implied 52.38%.  Model says 40%.  Edge → negative EV.
    ev = calc.calculate_ev(model_prob=0.40, american_odds=-110, stake=100)
    assert ev < 0
    assert ev == pytest.approx(-23.636, abs=0.01)


def test_calculate_ev_break_even():
    """EV ≈ 0 when model probability matches the implied probability."""
    calc = EVCalculator()
    # +150 → implied 40%.  Use model_prob=0.40 → breakeven.
    ev = calc.calculate_ev(model_prob=0.40, american_odds=150, stake=100)
    assert ev == pytest.approx(0.0, abs=1e-9)


def test_calculate_ev_positive_odds_payout():
    """Positive American odds produce correct payout and EV."""
    calc = EVCalculator()
    # +200 → payout = stake * (200/100) = 200 on $100
    ev = calc.calculate_ev(model_prob=0.50, american_odds=200, stake=100)
    # EV = 0.50 * 200 - 0.50 * 100 = 100 - 50 = 50
    assert ev == pytest.approx(50.0)


def test_calculate_ev_with_extreme_odds():
    """Extreme odds (+10000) produce very large positive EV for high model prob."""
    calc = EVCalculator()
    # +10000 → payout = 100 * 100 = 10000 on $100, EV = 0.95*10000 - 0.05*100
    ev = calc.calculate_ev(model_prob=0.95, american_odds=10000, stake=100)
    assert ev == pytest.approx(9495.0, abs=0.01)


def test_calculate_ev_zero_stake():
    """Zero stake produces zero EV regardless of odds or probability."""
    calc = EVCalculator()
    ev = calc.calculate_ev(model_prob=0.50, american_odds=-110, stake=0)
    assert ev == 0.0


# ---------------------------------------------------------------------------
# evaluate_bet
# ---------------------------------------------------------------------------


def test_evaluate_bet_positive_ev():
    """Full evaluation returns correct dict when EV > 0."""
    calc = EVCalculator()
    result = calc.evaluate_bet(team='OKC Thunder', model_prob=0.78, american_odds=-175, stake=100)

    assert result['team'] == 'OKC Thunder'
    assert result['model_prob'] == '78.0%'
    assert result['book_prob'] == '63.6%'  # 175/275 ≈ 63.6%
    assert result['american_odds'] == -175
    assert result['ev_per_stake'] == '$22.57'
    assert result['ev_percent'] == '22.6%'
    assert result['recommendation'] == '[BET] Positive EV'


def test_evaluate_bet_book_prob_field_is_float_str():
    """book_prob in result dict is the formatted string of the float value."""
    calc = EVCalculator()
    result = calc.evaluate_bet(team='Test', model_prob=0.5, american_odds=200, stake=100)
    # 200 → implied = 100/300 = 33.333... → '33.3%'
    assert result['book_prob'] == '33.3%'


def test_evaluate_bet_strong_negative_ev():
    """Recommendation is Strong Negative EV when EV < -5."""
    calc = EVCalculator()
    # -110, model_prob=0.20 → EV ≈ -61.82 → < -5 → Strong Negative
    result = calc.evaluate_bet(team='Bad Bet', model_prob=0.20, american_odds=-110, stake=100)
    assert result['recommendation'] == '[AVOID] Strong Negative EV'


def test_evaluate_bet_slight_negative_ev():
    """Recommendation is Slight Negative EV when -5 <= EV <= 0."""
    calc = EVCalculator()
    # -110, model_prob=0.50 → EV ≈ -4.55 → > -5 → Slight Negative
    result = calc.evaluate_bet(team='Meh', model_prob=0.50, american_odds=-110, stake=100)
    assert result['recommendation'] == '[PASS] Slight Negative EV'


def test_evaluate_bet_appends_to_bets_list():
    """Each evaluation appends to the instance bets list."""
    calc = EVCalculator()
    assert len(calc.bets) == 0
    calc.evaluate_bet(team='A', model_prob=0.5, american_odds=-110)
    assert len(calc.bets) == 1
    calc.evaluate_bet(team='B', model_prob=0.5, american_odds=-110)
    assert len(calc.bets) == 2
    assert calc.bets[0]['team'] == 'A'
    assert calc.bets[1]['team'] == 'B'


# ---------------------------------------------------------------------------
# kelly_criterion
# ---------------------------------------------------------------------------


def test_kelly_criterion_capped_at_five_percent():
    """Full Kelly above 5% is capped at 0.05 for bankroll safety."""
    calc = EVCalculator()
    # win_prob=0.60, odds=-110 → full Kelly ≈ 16%, capped at 5%
    kelly = calc.kelly_criterion(win_probability=0.60, american_odds=-110)
    assert kelly == pytest.approx(0.05)


def test_kelly_criterion_below_cap():
    """Kelly below 5% returns the uncapped value."""
    calc = EVCalculator()
    # win_prob=0.525, odds=-105 → full Kelly = 2.625% (below cap)
    kelly = calc.kelly_criterion(win_probability=0.525, american_odds=-105)
    assert 0 < kelly < 0.05
    # decimal_odds = 100/105 = 20/21; kelly = (0.525*20/21 - 0.475) / (20/21)
    # 0.525 * 20/21 = 0.5; kelly = (0.5-0.475) * 21/20 = 0.025 * 21/20 = 0.02625
    assert kelly == pytest.approx(0.02625, rel=1e-5)


def test_kelly_criterion_positive_odds():
    """Kelly works correctly with positive American odds."""
    calc = EVCalculator()
    # win_prob=0.45, odds=+150 → full Kelly ≈ 23%, capped at 5%
    kelly = calc.kelly_criterion(win_probability=0.45, american_odds=150)
    assert kelly == pytest.approx(0.05)


def test_kelly_criterion_zero_probability():
    """Probability of 0 yields Kelly of 0 (no bet)."""
    calc = EVCalculator()
    kelly = calc.kelly_criterion(win_probability=0.0, american_odds=-110)
    assert kelly == 0.0


def test_kelly_criterion_certainty():
    """Probability of 1.0 → uncapped Kelly > 5%, returns capped 0.05."""
    calc = EVCalculator()
    kelly = calc.kelly_criterion(win_probability=1.0, american_odds=-110)
    assert kelly == pytest.approx(0.05)


def test_kelly_criterion_negative_expected_value():
    """When EV is negative, Kelly returns 0 (no bet recommended)."""
    calc = EVCalculator()
    # win_prob=0.30, odds=-110 → negative EV, Kelly should be 0
    kelly = calc.kelly_criterion(win_probability=0.30, american_odds=-110)
    assert kelly == 0.0
