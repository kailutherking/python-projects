import json
from pathlib import Path

from backend.odds_scraping.draftkings_scraper import DraftKingsScraper
from backend.odds_scraping.espn_scraper import EspnOddsScraper
from backend.odds_scraping.live_odds_scraper import LiveOddsScraper
from tests.selenium_fakes import FakeDriver, FakeWebElement


def _load_fixture(filename: str) -> dict:
    fixture_path = Path(__file__).parent.parent / 'src' / 'backend' / 'fixtures' / filename
    with open(fixture_path) as f:
        return json.load(f)


def test_get_all_games_resets_previous_results(monkeypatch):
    scraper = LiveOddsScraper()
    game = {
        'date': '2026-04-30',
        'home_team': 'Boston Celtics',
        'away_team': 'OKC Thunder',
        'matchup': 'OKC Thunder @ Boston Celtics',
        'spread': '-2.5',
        'moneyline': '-135',
        'over_under': '223.5',
        'source': 'ESPN',
    }

    def scrape_espn(self):
        self.all_games.extend([game])
        return [game]

    monkeypatch.setattr(LiveOddsScraper, 'scrape_espn_nba_odds', scrape_espn)
    monkeypatch.setattr(LiveOddsScraper, 'scrape_draftkings_odds', lambda self: [])
    monkeypatch.setattr(LiveOddsScraper, 'display_games', lambda *_args: None)

    assert scraper.get_all_games() == [game]
    assert scraper.get_all_games() == [game]


def test_parse_draftkings_games_extracts_spread_moneyline_and_total():
    outcome_cells = [
        FakeWebElement(
            text='OKC Thunder -2.5\n-110',
            attrs={'aria-label': 'OKC Thunder Spread -2.5 -110'},
        ),
        FakeWebElement(
            text='OKC Thunder\n-135',
            attrs={'aria-label': 'OKC Thunder Moneyline -135'},
        ),
        FakeWebElement(
            text='Over 223.5\n-110',
            attrs={'aria-label': 'Over 223.5 Total Points -110'},
        ),
    ]
    game_block = FakeWebElement(children=outcome_cells)
    team_elements = [
        FakeWebElement(text='OKC Thunder', parent=game_block),
        FakeWebElement(text='Boston Celtics', parent=game_block),
    ]
    driver = FakeDriver(team_elements)

    [game] = DraftKingsScraper().parse_games(driver)

    assert game['away_team'] == 'OKC Thunder'
    assert game['home_team'] == 'Boston Celtics'
    assert game['spread'] == '-2.5'
    assert game['moneyline'] == '-135'
    assert game['over_under'] == '223.5'


def test_scrape_espn_uses_scoreboard_fallback_when_header_api_returns_non_json(monkeypatch):
    class HeaderResponse:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError('not json')

    class ScoreboardResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'events': [
                    {
                        'date': '2026-04-30T23:00Z',
                        'competitions': [
                            {
                                'competitors': [
                                    {
                                        'homeAway': 'away',
                                        'team': {'displayName': 'OKC Thunder'},
                                    },
                                    {
                                        'homeAway': 'home',
                                        'team': {'displayName': 'Boston Celtics'},
                                    },
                                ],
                                'odds': [
                                    {
                                        'provider': {'displayName': 'Draft Kings'},
                                        'moneyline': {
                                            'away': {'close': {'odds': -135}},
                                            'home': {'close': {'odds': 120}},
                                        },
                                        'pointSpread': {
                                            'away': {'close': {'line': -2.5}},
                                        },
                                        'total': {
                                            'over': {'close': {'line': 223.5}},
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }

    scraper = LiveOddsScraper()
    responses = iter([HeaderResponse(), ScoreboardResponse()])
    monkeypatch.setattr(scraper._http, 'get', lambda *_args, **_kwargs: next(responses))

    [game] = scraper.scrape_espn_nba_odds()

    assert game['matchup'] == 'OKC Thunder @ Boston Celtics'
    assert game['spread'] == '-2.5'
    assert game['moneyline'] == '-135'
    assert game['home_moneyline'] == '+120'
    assert game['over_under'] == '223.5'


def test_parse_espn_header_api_fixture():
    scraper = EspnOddsScraper()
    data = _load_fixture('espn_header_api.json')
    events = data['sports'][0]['leagues'][0]['events']

    games = scraper.parse_header_events(events)

    assert len(games) == 3

    # DET @ ORL -- away (DET) favored by 3.5
    det_orl = games[0]
    assert det_orl['matchup'] == 'Detroit Pistons @ Orlando Magic'
    assert det_orl['spread'] == '-3.5'
    assert det_orl['moneyline'] == '-162'
    assert det_orl['home_moneyline'] == '+136'
    assert det_orl['over_under'] == '210.5'

    # CLE @ TOR -- away (CLE) favored by 4.5
    cle_tor = games[1]
    assert cle_tor['matchup'] == 'Cleveland Cavaliers @ Toronto Raptors'
    assert cle_tor['spread'] == '-4.5'
    assert cle_tor['moneyline'] == '-198'
    assert cle_tor['home_moneyline'] == '+164'
    assert cle_tor['over_under'] == '218.5'

    # LAL @ HOU -- home (HOU) favored by 5.5, so away is +5.5
    lal_hou = games[2]
    assert lal_hou['matchup'] == 'Los Angeles Lakers @ Houston Rockets'
    assert lal_hou['spread'] == '+5.5'
    assert lal_hou['moneyline'] == '+160'
    assert lal_hou['home_moneyline'] == '-192'
    assert lal_hou['over_under'] == '203.5'

    for game in games:
        assert game['source'] == 'ESPN'
        assert game['date']
        assert game['home_team']
        assert game['away_team']


def test_parse_espn_scoreboard_api_fixture():
    scraper = EspnOddsScraper()
    data = _load_fixture('espn_scoreboard_api.json')
    events = data.get('events', [])

    games = scraper.parse_scoreboard_events(events)

    assert len(games) == 1

    game = games[0]
    assert game['matchup'] == 'Philadelphia 76ers @ Boston Celtics'
    assert game['spread'] == '+7.5'
    assert game['over_under'] == '205.5'
    assert game['moneyline'] != 'N/A'
    assert game['home_moneyline'] != 'N/A'
    assert game['source'] == 'ESPN'
    assert game['away_team'] == 'Philadelphia 76ers'
    assert game['home_team'] == 'Boston Celtics'


def test_draftkings_fixture_no_odds_table_fails_gracefully():
    fixture_path = (
        Path(__file__).parent.parent / 'src' / 'backend' / 'fixtures' / 'dk-game-lines.html'
    )
    with open(fixture_path, encoding='utf-8') as f:
        html = f.read()

    assert len(html) > 10000
    assert 'DraftKings' in html
    assert 'NBA' in html
    # event-cell__name-text (what the Selenium scraper looks for) is NOT present
    assert 'event-cell__name-text' not in html


def test_select_scoreboard_odds_prefers_draftkings():
    scraper = EspnOddsScraper()
    odds_list = [
        {'provider': {'displayName': 'Caesars'}, 'id': '1'},
        {'provider': {'name': 'Draft Kings'}, 'id': '2'},
        {'provider': {'displayName': 'FanDuel'}, 'id': '3'},
    ]
    selected = scraper.select_scoreboard_odds(odds_list)
    assert selected is not None
    assert selected['id'] == '2'


def test_select_scoreboard_odds_falls_back_to_first():
    scraper = EspnOddsScraper()
    odds_list = [
        {'provider': {'displayName': 'Caesars'}, 'id': '1'},
        {'provider': {'displayName': 'FanDuel'}, 'id': '2'},
    ]
    selected = scraper.select_scoreboard_odds(odds_list)
    assert selected is not None
    assert selected['id'] == '1'


# ============ cb-market (component-builder) structure tests ============


def test_parse_draftkings_cb_market_structure():
    """Test parsing DraftKings cb-market template (component-builder layout)."""
    away_spread_btn = FakeWebElement(
        text='+7.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0HC84578437P750_1'},
    )
    away_spread_btn._children = [
        FakeWebElement(text='+7.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeWebElement(text='-102', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    home_spread_btn = FakeWebElement(
        text='-7.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0HC84578437N750_3'},
    )
    home_spread_btn._children = [
        FakeWebElement(text='-7.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeWebElement(text='-118', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    over_btn = FakeWebElement(
        text='O 205.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0OU84578437O20550_1'},
    )
    over_btn._children = [
        FakeWebElement(text='O', attrs={'data-testid': 'button-title-market-board'}),
        FakeWebElement(text='205.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeWebElement(text='-110', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    away_ml_btn = FakeWebElement(
        text='+215', attrs={'data-testid': 'component-builder-market-button-34077039-0ML84578437_1'}
    )
    away_ml_btn._children = [
        FakeWebElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    home_ml_btn = FakeWebElement(
        text='-265', attrs={'data-testid': 'component-builder-market-button-34077039-0ML84578437_3'}
    )
    home_ml_btn._children = [
        FakeWebElement(text='-265', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    away_team = FakeWebElement(text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'})
    home_team = FakeWebElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )

    game_template = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[
            away_team,
            home_team,
            away_spread_btn,
            home_spread_btn,
            over_btn,
            away_ml_btn,
            home_ml_btn,
        ],
    )

    driver = FakeDriver([game_template])
    games = DraftKingsScraper().parse_cb_market(driver)

    assert len(games) == 1
    game = games[0]
    assert game['away_team'] == 'PHI 76ers'
    assert game['home_team'] == 'BOS Celtics'
    assert game['matchup'] == 'PHI 76ers @ BOS Celtics'
    assert game['spread'] == '+7.5'
    assert game['moneyline'] == '+215'
    assert game['home_moneyline'] == '-265'
    assert game['over_under'] == '205.5'
    assert game['source'] == 'DraftKings'


def test_parse_draftkings_games_prefers_cb_market():
    """Test parse_games tries cb-market first, then falls back."""
    away_team = FakeWebElement(text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'})
    home_team = FakeWebElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_ml_btn = FakeWebElement(
        text='+215', attrs={'data-testid': 'component-builder-market-button-0ML_1'}
    )
    away_ml_btn._children = [
        FakeWebElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    home_ml_btn = FakeWebElement(
        text='-265', attrs={'data-testid': 'component-builder-market-button-0ML_3'}
    )
    home_ml_btn._children = [
        FakeWebElement(text='-265', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    game_template = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team, home_team, away_ml_btn, home_ml_btn],
    )

    driver = FakeDriver([game_template])
    games = DraftKingsScraper().parse_games(driver)

    assert len(games) == 1
    assert games[0]['away_team'] == 'PHI 76ers'
    assert games[0]['home_team'] == 'BOS Celtics'


def test_parse_draftkings_cb_market_skips_incomplete_games():
    """Games with fewer than 2 teams are skipped."""
    away_team = FakeWebElement(text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'})
    game_template = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team],
    )

    driver = FakeDriver([game_template])
    games = DraftKingsScraper().parse_cb_market(driver)
    assert len(games) == 0


def test_parse_draftkings_cb_market_multiple_games():
    """Parse multiple games from cb-market templates."""
    away_team1 = FakeWebElement(text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'})
    home_team1 = FakeWebElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_ml1 = FakeWebElement(
        text='+215', attrs={'data-testid': 'component-builder-market-button-game1-0ML_1'}
    )
    away_ml1._children = [
        FakeWebElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    template1 = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team1, home_team1, away_ml1],
    )

    away_team2 = FakeWebElement(text='ORL Magic', attrs={'class': 'cb-market__label-inner--parlay'})
    home_team2 = FakeWebElement(
        text='DET Pistons', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_ml2 = FakeWebElement(
        text='+280', attrs={'data-testid': 'component-builder-market-button-game2-0ML_1'}
    )
    away_ml2._children = [
        FakeWebElement(text='+280', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    template2 = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team2, home_team2, away_ml2],
    )

    driver = FakeDriver([template1, template2])
    games = DraftKingsScraper().parse_cb_market(driver)

    assert len(games) == 2
    assert games[0]['matchup'] == 'PHI 76ers @ BOS Celtics'
    assert games[1]['matchup'] == 'ORL Magic @ DET Pistons'


# ============ futures champion tests ============


def test_parse_futures_champion_extracts_team_and_odds():
    """Parse DraftKings futures champion market structure."""
    # Each button has: button-title-market-board (team) + button-odds-market-board (odds)
    team1 = FakeWebElement(text='OKC Thunder', attrs={'data-testid': 'button-title-market-board'})
    odds1 = FakeWebElement(text='-130', attrs={'data-testid': 'button-odds-market-board'})
    btn1 = FakeWebElement(
        attrs={'class': 'cb-market__button cb-market__button--regular'},
        children=[team1, odds1],
    )

    team2 = FakeWebElement(text='BOS Celtics', attrs={'data-testid': 'button-title-market-board'})
    odds2 = FakeWebElement(text='+650', attrs={'data-testid': 'button-odds-market-board'})
    btn2 = FakeWebElement(
        attrs={'class': 'cb-market__button cb-market__button--regular'},
        children=[team2, odds2],
    )

    team3 = FakeWebElement(text='NY Knicks', attrs={'data-testid': 'button-title-market-board'})
    odds3 = FakeWebElement(text='  +1800  ', attrs={'data-testid': 'button-odds-market-board'})
    btn3 = FakeWebElement(
        attrs={'class': 'cb-market__button cb-market__button--regular'},
        children=[team3, odds3],
    )

    template = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[btn1, btn2, btn3],
    )

    driver = FakeDriver([template])
    results = DraftKingsScraper().parse_futures_champion(driver)

    assert len(results) == 3
    assert results[0] == {
        'team': 'OKC Thunder',
        'odds': '-130',
        'bet_type': 'champion',
        'source': 'DraftKings',
    }
    assert results[1]['team'] == 'BOS Celtics'
    assert results[1]['odds'] == '+650'
    assert results[2]['team'] == 'NY Knicks'
    assert results[2]['odds'] == '+1800'


def test_parse_futures_champion_empty_when_no_button_elements():
    """Return empty list when no champion market buttons exist."""
    driver = FakeDriver([])
    results = DraftKingsScraper().parse_futures_champion(driver)
    assert results == []


def test_parse_futures_category_passes_bet_type():
    """Verify bet_type parameter is set in each output dict."""
    team = FakeWebElement(text='LAL Lakers', attrs={'data-testid': 'button-title-market-board'})
    odds = FakeWebElement(text='+1200', attrs={'data-testid': 'button-odds-market-board'})
    btn = FakeWebElement(
        attrs={'class': 'cb-market__button cb-market__button--regular'},
        children=[team, odds],
    )
    template = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[btn],
    )
    driver = FakeDriver([template])
    results = DraftKingsScraper().parse_futures_category(driver, 'playoffs')

    assert len(results) == 1
    assert results[0]['bet_type'] == 'playoffs'
    assert results[0]['team'] == 'LAL Lakers'
    assert results[0]['odds'] == '+1200'
    assert results[0]['source'] == 'DraftKings'
