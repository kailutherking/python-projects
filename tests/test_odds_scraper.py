"""Tests for OddsScraper — hardcoded sample data provider."""

import tempfile
from pathlib import Path

from backend.odds_scraping.odds_scraper import OddsScraper

_REQUIRED_KEYS = {
    'game_id',
    'date',
    'team',
    'opponent',
    'moneyline',
    'spread',
    'over_under',
    'sportsbook',
}


class TestOddsScraper:
    """Unit tests for OddsScraper."""

    def test_init_loads_config(self):
        scraper = OddsScraper(config_file='config.json')
        assert scraper.config == {
            'sportsbooks': {
                'espn': {'enabled': True, 'url': 'https://www.espn.com/nba/odds'},
                'draftkings': {'enabled': True},
                'fanduel': {'enabled': True},
            },
            'sport': 'NBA',
            'season': '2025-26',
            'export_format': 'csv',
        }

    def test_init_missing_config_returns_empty_dict(self):
        scraper = OddsScraper(config_file='nonexistent_config.json')
        assert scraper.config == {}

    def test_load_config_file_not_found(self):
        scraper = OddsScraper()
        result = scraper.load_config('nonexistent_file.json')
        assert result == {}

    def test_scrape_espn_odds_returns_list(self):
        scraper = OddsScraper()
        odds = scraper.scrape_espn_odds()
        assert isinstance(odds, list)
        assert len(odds) == 4

    def test_scrape_espn_odds_has_required_keys(self):
        scraper = OddsScraper()
        for game in scraper.scrape_espn_odds():
            assert _REQUIRED_KEYS.issubset(game.keys())

    def test_scrape_espn_odds_source_is_espn(self):
        scraper = OddsScraper()
        for game in scraper.scrape_espn_odds():
            assert game['sportsbook'] == 'ESPN'

    def test_scrape_draftkings_odds_returns_list(self):
        scraper = OddsScraper()
        odds = scraper.scrape_draftkings_odds()
        assert isinstance(odds, list)
        assert len(odds) == 4

    def test_scrape_draftkings_odds_source_is_draftkings(self):
        scraper = OddsScraper()
        for game in scraper.scrape_draftkings_odds():
            assert game['sportsbook'] == 'DraftKings'

    def test_scrape_fanduel_odds_returns_list(self):
        scraper = OddsScraper()
        odds = scraper.scrape_fanduel_odds()
        assert isinstance(odds, list)
        assert len(odds) == 4

    def test_scrape_fanduel_odds_source_is_fanduel(self):
        scraper = OddsScraper()
        for game in scraper.scrape_fanduel_odds():
            assert game['sportsbook'] == 'FanDuel'

    def test_all_odds_are_integers_or_floats(self):
        """Moneyline, spread, over_under should be numeric."""
        scraper = OddsScraper()
        for odds_list in [
            scraper.scrape_espn_odds(),
            scraper.scrape_draftkings_odds(),
            scraper.scrape_fanduel_odds(),
        ]:
            for game in odds_list:
                assert isinstance(game['moneyline'], int)
                assert isinstance(game['spread'], (int, float))
                assert isinstance(game['over_under'], (int, float))

    def test_get_all_odds_respects_config(self):
        """When all sportsbooks are enabled, 12 games are returned (4 per book)."""
        scraper = OddsScraper()
        odds = scraper.get_all_odds()
        assert len(odds) == 12

    def test_get_all_odds_with_disabled_books(self):
        """Test that disabled books are skipped."""
        scraper = OddsScraper()
        scraper.config = {
            'sportsbooks': {
                'espn': {'enabled': False},
                'draftkings': {'enabled': True},
                'fanduel': {'enabled': False},
            }
        }
        odds = scraper.get_all_odds()
        assert len(odds) == 4
        for game in odds:
            assert game['sportsbook'] == 'DraftKings'

    def test_export_to_csv_writes_file(self):
        """Export creates a CSV file in the temp directory."""
        scraper = OddsScraper()
        scraper.scraped_odds = scraper.scrape_espn_odds()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_odds.csv'
            scraper.export_to_csv(filename=str(filepath))
            assert filepath.exists()
            content = filepath.read_text()
            assert 'OKC Thunder' in content
            assert 'moneyline' in content

    def test_export_to_csv_no_data_does_nothing(self):
        """Export with no scraped data prints a message but doesn't crash."""
        scraper = OddsScraper()
        scraper.export_to_csv(filename='data/nonexistent.csv')
        # Should not raise — just prints warning

    def test_timestamp_is_set_on_init(self):
        scraper = OddsScraper()
        assert scraper.timestamp
        assert ':' in scraper.timestamp  # datetime format
