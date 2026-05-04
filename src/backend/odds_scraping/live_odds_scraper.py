import logging

import pandas as pd

from .draftkings_scraper import DraftKingsScraper
from .espn_scraper import EspnOddsScraper
from .http_client import HttpClient
from .parsers import GameOdds

logger = logging.getLogger(__name__)


class LiveOddsScraper:
    """Scrape live odds from ESPN and DraftKings for real games."""

    def __init__(self, http: HttpClient | None = None):
        self._http = http or HttpClient()
        self._espn = EspnOddsScraper(self._http)
        self._dk = DraftKingsScraper()
        self.all_games = []

    # ============ ESPN SCRAPING (JSON API) ============

    def scrape_espn_nba_odds(self):
        """Scrape live NBA odds from ESPN's JSON API."""
        games = self._espn.scrape_nba_odds()
        self.all_games.extend(games)
        return games

    # ============ DRAFTKINGS SCRAPING (Selenium) ============

    def scrape_draftkings_odds(self):
        """Scrape live odds from DraftKings using Selenium."""
        games = self._dk.scrape_odds()
        if games:
            self.all_games.extend(games)
        return games

    @staticmethod
    def parse_draftkings_html(html: str) -> list[GameOdds]:
        """Compatibility wrapper for offline HTML parsing.

        Delegates to DraftKingsScraper.parse_html for consumers that still
        call LiveOddsScraper.parse_draftkings_html(...).
        """
        return DraftKingsScraper.parse_html(html)

    # ============ EXPORT & DISPLAY ============

    def export_to_csv(self, games, filename='data/live_odds.csv'):
        """Export live odds to CSV."""
        if not games:
            print('No games to export')
            return None

        df = pd.DataFrame(games)
        df.to_csv(filename, index=False)
        print(f'[OK] Live odds exported to {filename}')
        print(f'   Total games: {len(df)}\n')

        return df

    def display_games(self, games, source=''):
        """Display games in a formatted table."""
        if not games:
            return

        df = pd.DataFrame(games)

        print('=' * 100)
        print(f'LIVE {source} GAMES')
        print('=' * 100)
        print(df.to_string(index=False))
        print()

    def get_all_games(self):
        """Scrape both ESPN and DraftKings."""
        print('NBA Live odds from all sources\n')
        self.all_games = []

        espn_games = self.scrape_espn_nba_odds()
        if espn_games:
            self.display_games(espn_games, 'ESPN')

        dk_games = self.scrape_draftkings_odds()
        if dk_games:
            self.display_games(dk_games, 'DRAFTKINGS')

        return self.all_games
