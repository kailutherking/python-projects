import pandas as pd


def _normalize_game(game: dict) -> dict:
    """Return a copy of *game* with unified 'team' and 'opponent' keys.

    Accepts both OddsScraper schema (team/opponent/sportsbook) and
    LiveOddsScraper schema (home_team/away_team/matchup/source) so that
    OddsComparison can consume output from either scraper.
    """
    if 'team' in game and 'opponent' in game:
        return game  # already canonical
    normalized = dict(game)
    normalized['team'] = game.get('away_team', game.get('home_team', 'Unknown'))
    normalized['opponent'] = game.get('home_team', 'Unknown')
    # Map 'source' -> 'sportsbook' if present
    if 'source' in normalized and 'sportsbook' not in normalized:
        normalized['sportsbook'] = normalized['source']
    return normalized


class OddsComparison:
    """Compare odds across multiple sportsbooks"""

    def __init__(self):
        """Initialize the odds comparison tool"""
        self.odds_by_book = {}
        self.comparison_results = []

    def add_odds(self, sportsbook: str, odds_list: list[dict]):
        """Add odds from a sportsbook"""
        self.odds_by_book[sportsbook] = odds_list
        print(f'[OK] Added {len(odds_list)} odds from {sportsbook}')

    def find_best_odds(self, bet_type: str = 'moneyline'):
        """Find the best odds for each matchup."""
        results = []

        if not self.odds_by_book:
            return results

        # Get all games
        first_book_odds = next(iter(self.odds_by_book.values()))
        games = {}

        for raw_game in first_book_odds:
            game = _normalize_game(raw_game)
            game_key = f'{game["team"]} vs {game["opponent"]}'
            if game_key not in games:
                games[game_key] = {
                    'date': game['date'],
                    'team': game['team'],
                    'opponent': game['opponent'],
                    'odds': {},
                }

        # Collect odds from all books
        for book, odds_list in self.odds_by_book.items():
            for raw_game in odds_list:
                game = _normalize_game(raw_game)
                game_key = f'{game["team"]} vs {game["opponent"]}'
                if game_key in games:
                    games[game_key]['odds'][book] = game[bet_type]

        # Find best odds for each game
        for _game_key, game_data in games.items():
            best_book = None
            best_value = None

            for book, odds in game_data['odds'].items():
                if best_value is None:
                    best_book = book
                    best_value = odds
                else:
                    # American odds: less-negative beats more-negative (e.g. -105 > -110);
                    # among positives, higher is better (e.g. +150 > +120).
                    # Sorting by numeric value handles both cases correctly.
                    if odds > best_value:
                        best_book = book
                        best_value = odds
            result = {
                'date': game_data['date'],
                'team': game_data['team'],
                'opponent': game_data['opponent'],
                'best_book': best_book,
                'best_odds': best_value,
                'bet_type': bet_type,
            }

            # Add all sportsbook odds to result
            for book, odds in game_data['odds'].items():
                result[f'{book}_odds'] = odds

            results.append(result)

        self.comparison_results = results
        return results

    def display_comparison(self, bet_type: str = 'moneyline'):
        """Display a formatted comparison of odds"""
        results = self.find_best_odds(bet_type)

        print(f'\n{"=" * 80}')
        print(f'ODDS COMPARISON ({bet_type.upper()})')
        print(f'{"=" * 80}\n')

        for result in results:
            print(f'{result["team"]} vs {result["opponent"]}')
            print(f'  Date: {result["date"]}')
            print(f'  Best: {result["best_book"]} ({result["best_odds"]})')

            for book, odds in result.items():
                if book.endswith('_odds'):
                    book_name = book.replace('_odds', '')
                    print(f'    {book_name}: {odds}')
            print()

    def export_to_csv(self, filename='data/odds_comparison_results.csv'):
        """Export comparison results to CSV"""
        if not self.comparison_results:
            print('No comparison results. Run find_best_odds() first.')
            return

        df = pd.DataFrame(self.comparison_results)
        df.to_csv(filename, index=False)
        print(f'[OK] Comparison exported to {filename}')
        print(f'  Total games: {len(df)}')
