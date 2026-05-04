from backend.models.odds_enrichment import (
    enrich_live_odds_rows,
    merge_source_rows,
    parse_american_odds,
    recompute_ev,
)
from frontend.gui.pages.live_odds import SOURCE_BADGE_SLOT


def test_source_badge_slot_uses_valid_quasar_table_cell_template():
    assert '<q-td :props="props">' in SOURCE_BADGE_SLOT
    assert "props.value === 'ESPN' ? 'red' : 'blue'" in SOURCE_BADGE_SLOT
    assert '\\' not in SOURCE_BADGE_SLOT


def test_parse_american_odds_handles_positive_odds():
    assert parse_american_odds('+150') == 150


def test_parse_american_odds_handles_negative_odds():
    assert parse_american_odds('-110') == -110


def test_parse_american_odds_returns_none_for_invalid_input():
    assert parse_american_odds('N/A') is None


def test_enrich_live_odds_rows_adds_ev_per_100_from_away_moneyline():
    [row] = enrich_live_odds_rows(
        [
            {
                'date': '2026-04-30',
                'home_team': 'Boston Celtics',
                'away_team': 'OKC Thunder',
                'matchup': 'OKC Thunder @ Boston Celtics',
                'spread': '-2.5',
                'moneyline': '-110',
                'home_moneyline': '+120',
                'over_under': '223.5',
                'source': 'ESPN',
            }
        ],
        model_probability=0.55,
    )

    assert row['ev_per_100'] == '$5.00'
    assert row['home_ev_per_100'] == '$21.00'


def test_enrich_live_odds_rows_marks_unusable_moneyline_as_not_available():
    [row] = enrich_live_odds_rows(
        [
            {
                'date': '2026-04-30',
                'home_team': 'Boston Celtics',
                'away_team': 'OKC Thunder',
                'matchup': 'OKC Thunder @ Boston Celtics',
                'spread': '-2.5',
                'moneyline': 'N/A',
                'home_moneyline': '+120',
                'over_under': '223.5',
                'source': 'ESPN',
            }
        ],
        model_probability=0.55,
    )

    assert row['ev_per_100'] == 'N/A'
    assert row['home_ev_per_100'] == '$21.00'


def test_recompute_ev_updates_ev_columns_with_new_probability():
    rows = [
        {
            'matchup': 'LAL @ BOS',
            'moneyline': '-110',
            'home_moneyline': '+120',
            'ev_per_100': '$5.00',
            'home_ev_per_100': '$21.00',
        }
    ]

    updated = recompute_ev(rows, model_probability=0.60)

    assert updated[0]['ev_per_100'] != '$5.00'
    assert updated[0]['home_ev_per_100'] != '$21.00'


def test_merge_source_rows_replaces_only_refreshed_sportsbook_rows():
    existing_rows = [
        {'matchup': 'Old ESPN Game', 'source': 'ESPN', 'moneyline': '-110', 'ev_per_100': '$5.00'},
        {
            'matchup': 'DraftKings Game',
            'source': 'DraftKings',
            'moneyline': '+150',
            'ev_per_100': '$0.00',
        },
    ]
    new_espn_games = [
        {
            'date': '2026-04-30',
            'home_team': 'Boston Celtics',
            'away_team': 'OKC Thunder',
            'matchup': 'OKC Thunder @ Boston Celtics',
            'spread': '-2.5',
            'moneyline': '-110',
            'home_moneyline': '+120',
            'over_under': '223.5',
            'source': 'ESPN',
        }
    ]

    rows = merge_source_rows(existing_rows, new_espn_games, 'ESPN', model_probability=0.55)

    assert [row['matchup'] for row in rows] == [
        'DraftKings Game',
        'OKC Thunder @ Boston Celtics',
    ]
    assert rows[1]['ev_per_100'] == '$5.00'
    assert rows[1]['home_ev_per_100'] == '$21.00'


def test_merge_source_rows_recomputes_ev_for_preserved_rows():
    existing_rows = [
        {
            'matchup': 'DK Game',
            'source': 'DraftKings',
            'moneyline': '+150',
            'home_moneyline': '-200',
            'ev_per_100': '$0.00',  # stale EV computed at an old probability
        },
    ]
    new_espn_games = [
        {
            'date': '2026-04-30',
            'home_team': 'Boston Celtics',
            'away_team': 'OKC Thunder',
            'matchup': 'OKC Thunder @ Boston Celtics',
            'spread': '-2.5',
            'moneyline': '-110',
            'home_moneyline': '+120',
            'over_under': '223.5',
            'source': 'ESPN',
        }
    ]

    rows = merge_source_rows(existing_rows, new_espn_games, 'ESPN', model_probability=0.55)

    dk_row = rows[0]
    assert dk_row['source'] == 'DraftKings'
    assert dk_row['ev_per_100'] != '$0.00'  # EV recomputed with current probability
