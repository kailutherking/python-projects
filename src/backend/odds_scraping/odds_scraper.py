import json
from datetime import datetime

import pandas as pd


class OddsScraper:
    """Scrapes NBA odds from ESPN and other sportsbooks"""

    def __init__(self, config_file='config.json'):
        """Initialize the odds scraper"""
        self.config = self.load_config(config_file)
        self.scraped_odds = []
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f'Config file not found: {config_file}')
            return {}

    def scrape_espn_odds(self):
        """Scrape NBA odds from ESPN"""
        print('Scraping ESPN odds...')

        # Sample NBA odds data for 2025-26 season
        espn_odds = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'team': 'OKC Thunder',
                'opponent': 'Boston Celtics',
                'moneyline': -180,
                'spread': -7.5,
                'over_under': 214.5,
                'sportsbook': 'ESPN',
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'team': 'Denver Nuggets',
                'opponent': 'Lakers',
                'moneyline': 150,
                'spread': 4.5,
                'over_under': 223.5,
                'sportsbook': 'ESPN',
            },
            {
                'game_id': 3,
                'date': '2026-04-30',
                'team': 'Boston Celtics',
                'opponent': 'OKC Thunder',
                'moneyline': 150,
                'spread': 7.5,
                'over_under': 214.5,
                'sportsbook': 'ESPN',
            },
            {
                'game_id': 4,
                'date': '2026-04-30',
                'team': 'Lakers',
                'opponent': 'Denver Nuggets',
                'moneyline': -130,
                'spread': -4.5,
                'over_under': 223.5,
                'sportsbook': 'ESPN',
            },
        ]

        return espn_odds

    def scrape_draftkings_odds(self):
        """Scrape NBA odds from DraftKings"""
        print('Scraping DraftKings odds...')

        # Sample DraftKings odds (slightly different lines)
        dk_odds = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'team': 'OKC Thunder',
                'opponent': 'Boston Celtics',
                'moneyline': -175,
                'spread': -7.0,
                'over_under': 214.0,
                'sportsbook': 'DraftKings',
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'team': 'Denver Nuggets',
                'opponent': 'Lakers',
                'moneyline': 155,
                'spread': 4.0,
                'over_under': 223.0,
                'sportsbook': 'DraftKings',
            },
            {
                'game_id': 3,
                'date': '2026-04-30',
                'team': 'Boston Celtics',
                'opponent': 'OKC Thunder',
                'moneyline': 155,
                'spread': 7.0,
                'over_under': 214.0,
                'sportsbook': 'DraftKings',
            },
            {
                'game_id': 4,
                'date': '2026-04-30',
                'team': 'Lakers',
                'opponent': 'Denver Nuggets',
                'moneyline': -125,
                'spread': -4.0,
                'over_under': 223.0,
                'sportsbook': 'DraftKings',
            },
        ]

        return dk_odds

    def scrape_fanduel_odds(self):
        """Scrape NBA odds from FanDuel"""
        print('Scraping FanDuel odds...')

        # Sample FanDuel odds
        fanduel_odds = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'team': 'OKC Thunder',
                'opponent': 'Boston Celtics',
                'moneyline': -178,
                'spread': -7.0,
                'over_under': 214.5,
                'sportsbook': 'FanDuel',
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'team': 'Denver Nuggets',
                'opponent': 'Lakers',
                'moneyline': 152,
                'spread': 4.5,
                'over_under': 223.5,
                'sportsbook': 'FanDuel',
            },
            {
                'game_id': 3,
                'date': '2026-04-30',
                'team': 'Boston Celtics',
                'opponent': 'OKC Thunder',
                'moneyline': 152,
                'spread': 7.0,
                'over_under': 214.5,
                'sportsbook': 'FanDuel',
            },
            {
                'game_id': 4,
                'date': '2026-04-30',
                'team': 'Lakers',
                'opponent': 'Denver Nuggets',
                'moneyline': -128,
                'spread': -4.5,
                'over_under': 223.5,
                'sportsbook': 'FanDuel',
            },
        ]

        return fanduel_odds

    def get_all_odds(self):
        """Get odds from all enabled sportsbooks"""
        all_odds = []

        if self.config['sportsbooks']['espn']['enabled']:
            all_odds.extend(self.scrape_espn_odds())

        if self.config['sportsbooks']['draftkings']['enabled']:
            all_odds.extend(self.scrape_draftkings_odds())

        if self.config['sportsbooks']['fanduel']['enabled']:
            all_odds.extend(self.scrape_fanduel_odds())

        self.scraped_odds = all_odds
        return all_odds

    def export_to_csv(self, filename='data/sample_odds_data.csv'):
        """Export scraped odds to CSV file"""
        if not self.scraped_odds:
            print('No odds to export. Run get_all_odds() first.')
            return

        df = pd.DataFrame(self.scraped_odds)
        df.to_csv(filename, index=False)
        print(f'[OK] Odds exported to {filename}')
        print(f'  Total records: {len(df)}')
        print(f'  Sportsbooks: {df["sportsbook"].unique().tolist()}')
