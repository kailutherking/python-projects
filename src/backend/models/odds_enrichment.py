from __future__ import annotations

from collections.abc import Mapping, Sequence

from backend.models.ev_calculator import EVCalculator


def parse_american_odds(value: object) -> int | None:
    """Parse an American odds string (e.g. '+150', '-110') into an integer.

    Args:
        value: Raw odds value, typically a string like '+150' or '-110'.

    Returns:
        The odds as an integer, or ``None`` when *value* cannot be parsed.
    """
    try:
        return int(str(value).replace('+', ''))
    except (TypeError, ValueError):
        return None


def format_ev_per_100(calculator: EVCalculator, moneyline: object, model_probability: float) -> str:
    """Compute the expected value per $100 staked for a single moneyline.

    Args:
        calculator: ``EVCalculator`` instance used for the computation.
        moneyline: Raw moneyline value (e.g. ``'-110'`` or ``'+150'``).
    model_probability: Win probability from the model (0.0-1.0).

    Returns:
        A formatted dollar string such as ``'$5.00'``, or ``'N/A'`` when the
        moneyline cannot be parsed.
    """
    american_odds = parse_american_odds(moneyline)
    if american_odds is None:
        return 'N/A'

    ev = calculator.calculate_ev(model_probability, american_odds, stake=100)
    return f'${ev:.2f}'


def enrich_live_odds_rows(
    games: Sequence[Mapping[str, object]], model_probability: float
) -> list[dict]:
    """Convert raw scraper game mappings into display rows with EV enrichment.

    Each row gets ``ev_per_100`` (away moneyline EV) and ``home_ev_per_100``
    (home moneyline EV) columns added.

    Args:
        games: Sequence of game dictionaries from a scraper.
    model_probability: Win probability from the model (0.0-1.0).

    Returns:
        List of enriched row dictionaries ready for the odds table.
    """
    calculator = EVCalculator()
    rows: list[dict] = []
    for game in games:
        row = dict(game)
        row['ev_per_100'] = format_ev_per_100(calculator, row.get('moneyline'), model_probability)
        row['home_ev_per_100'] = format_ev_per_100(
            calculator, row.get('home_moneyline'), model_probability
        )
        rows.append(row)
    return rows


def recompute_ev(rows: list[dict], model_probability: float) -> list[dict]:
    """Re-compute EV columns for existing table rows using a new probability.

    Args:
        rows: Current table rows (each must contain ``moneyline`` and
            ``home_moneyline`` keys).
    model_probability: Updated win probability (0.0-1.0).

    Returns:
        New list of rows with refreshed ``ev_per_100`` and
        ``home_ev_per_100`` values.
    """
    calculator = EVCalculator()
    return [
        {
            **row,
            'ev_per_100': format_ev_per_100(calculator, row.get('moneyline'), model_probability),
            'home_ev_per_100': format_ev_per_100(
                calculator, row.get('home_moneyline'), model_probability
            ),
        }
        for row in rows
    ]


def merge_source_rows(
    existing_rows: list[dict],
    games: Sequence[Mapping[str, object]],
    source: str,
    model_probability: float,
) -> list[dict]:
    """Merge newly scraped games into the existing table rows.

    Rows whose *source* matches *source* are replaced by the fresh *games*.
    Rows from other sources are preserved and their EV values are recomputed
    with the current *model_probability*.

    Args:
        existing_rows: Rows currently displayed in the odds table.
        games: Freshly scraped game dictionaries.
        source: Name of the sportsbook being refreshed (e.g. ``'ESPN'``).
    model_probability: Win probability from the model (0.0-1.0).

    Returns:
        Merged list of rows ready for ``table.update_rows``.
    """
    rows_from_other_sources = [dict(row) for row in existing_rows if row.get('source') != source]
    re_enriched = recompute_ev(rows_from_other_sources, model_probability)
    return re_enriched + enrich_live_odds_rows(games, model_probability)
