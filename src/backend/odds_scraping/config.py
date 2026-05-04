"""Source-specific URLs and request parameters for odds adapters."""

from __future__ import annotations

ESPN_API_URL = 'https://site.web.api.espn.com/apis/v2/scoreboard/header'
ESPN_SCOREBOARD_API_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
ESPN_API_PARAMS: dict[str, str] = {
    'sport': 'basketball',
    'league': 'nba',
    'region': 'us',
    'lang': 'en',
    'contentorigin': 'espn',
    'buyWindow': '1m',
    'showAirings': 'buy,live,replay',
    'tz': 'America/New_York',
}

DK_BASE_URL = 'https://sportsbook.draftkings.com/leagues/basketball/nba'
DK_FUTURES_CHAMPION_URL = DK_BASE_URL + '?category=futures&subcategory=champion'
