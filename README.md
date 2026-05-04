# 🏀 NBA Odds Scraper & Expected Value Calculator

A Python project for scraping NBA odds from multiple sportsbooks and calculating expected value for sports bets.

[![CI](https://github.com/nickth3man/odds-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/nickth3man/odds-scraper/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/nickth3man/odds-scraper/actions/workflows/ci.yml)

## 📊 Features

- **NiceGUI Dashboard** — Browser-based GUI for live odds with always-on EV/100 analysis (`python -m frontend.gui.main`)
- **Sample Odds Scraper** — Multi-sportsbook odds collection (ESPN, DraftKings, FanDuel)
- **Live Odds Scraper** — Real-time scraping from ESPN's JSON API + DraftKings via Selenium
- **TLS Impersonation** — `curl_cffi` browser fingerprinting bypasses bot-detection on protected endpoints
- **Fast JSON Parsing** — `orjson` replaces stdlib `json` for faster response deserialization
- **HTML Parsing** — `parsel` CSS-selector parser extracts DraftKings odds without chained Selenium queries
- **Unified Schema** — `OddsComparison` accepts output from both scrapers transparently
- **Odds Comparison** — Find the best lines across sportsbooks with correct American odds logic
- **Expected Value Calculator** — Identify profitable betting opportunities using American odds math
- **Kelly Criterion** — Optimal bet sizing for bankroll management
- **CSV Export** — Power BI-ready data files

## 🛠️ Tech Stack

| Tool                | Purpose                                          |
| ------------------- | ------------------------------------------------ |
| Python **3.12+**    | Runtime                                          |
| **uv**              | Package manager                                  |
| **ruff**            | Linter + formatter                               |
| **ty**              | Fast type checker                                |
| **pyright**         | Static type checker                              |
| nicegui             | Browser-based GUI dashboard                      |
| selenium            | Browser automation (DraftKings)                  |
| httpx               | Async-capable HTTP client with retry logic       |
| curl-cffi           | TLS fingerprint impersonation (anti-bot bypass)  |
| orjson              | Fast JSON serialization/deserialization          |
| parsel              | CSS/XPath HTML parsing (Scrapy-style)            |
| tenacity            | Retry logic with exponential backoff             |
| fake-useragent      | Rotating User-Agent strings                      |
| courlan             | Domain extraction for per-domain rate limiting   |
| pandas              | Data manipulation & CSV export                   |
| pytest              | Testing framework                                |

## 📁 Project Structure

```
odds-scraper/
├── src/
│   ├── frontend/
│   │   └── gui/
│   │       ├── main.py          # NiceGUI entry point (python -m frontend.gui.main → localhost:8080)
│   │       └── pages/
│   │           ├── home.py      # Landing page with navigation
│   │           └── live_odds.py # Live odds table (ESPN + DraftKings + EV/100)
│   └── backend/
│       ├── odds_scraping/
│       │   ├── __init__.py
│       │   ├── odds_scraper.py          # Sample odds data provider
│       │   ├── odds_comparison.py       # Cross-sportsbook comparison (unified schema)
│       │   ├── http_client.py           # Resilient HTTP client (retry, rate-limit, UA rotation)
│       │   ├── parsers.py               # Shared odds parsing/formatting helpers
│       │   ├── espn_scraper.py          # ESPN JSON API adapter + scoreboard fallback
│       │   ├── draftkings_scraper.py    # DraftKings Selenium/parsel source adapter
│       │   └── live_odds_scraper.py     # Thin live scraper orchestrator
│       ├── models/
│       │   └── ev_calculator.py         # Expected Value & Kelly Criterion
│       └── fixtures/                    # HTML/JSON fixtures for offline tests
├── data/
│   ├── sample_odds_data.csv
│   ├── odds_comparison_results.csv
│   └── nba_standings_2025_26.csv
├── tests/                       # pytest test suite (62 tests)
├── .claude/
│   └── launch.json              # Dev server configurations
├── config.json                  # Sportsbook configuration
├── pyproject.toml               # Project metadata & tool config
├── uv.lock                      # Dependency lock file
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- Chrome (for DraftKings live scraping — Selenium Manager auto-downloads ChromeDriver)

### Setup

```bash
# Clone and enter the project
git clone https://github.com/yourusername/odds-scraper.git
cd odds-scraper

# Install all dependencies (creates .venv + uv.lock)
uv sync

# Run quality checks
uv run pytest
```

### GUI Dashboard

```bash
python -m frontend.gui.main
# Open http://localhost:8080
```

- **`/`** — Home: navigate to Live Odds
- **`/odds`** — Scrape ESPN and/or DraftKings odds into a searchable table with EV/100 analysis

### Quality Checks

```bash
uv run ruff format .         # Format
uv run ruff format --check . # Check formatting
uv run ruff check .          # Lint
uv run ruff check --fix      # Auto-fix safe lint issues
uv run ty check              # Fast type check
uv run pyright               # Static type check
uv run pytest                # Run tests (65 tests)
```


## ⚙️ Configuration

```json
{
  "sportsbooks": {
    "espn": { "enabled": true },
    "draftkings": { "enabled": true },
    "fanduel": { "enabled": true }
  }
}
```

## 🧪 Development

### Toolchain

| Command                | What it does                 |
| ---------------------- | ---------------------------- |
| `uv sync`                   | Install all dependencies        |
| `uv run ruff format .`      | Auto-format code                |
| `uv run ruff format --check .` | Check formatting             |
| `uv run ruff check .`       | Lint the codebase               |
| `uv run ty check`           | Fast type check                 |
| `uv run pyright`            | Static type check               |
| `uv run pytest`             | Run 65 tests                    |
| `uv lock --upgrade`         | Update all deps to latest       |

Dependencies use `>=` constraints in `pyproject.toml`. Exact versions are pinned in `uv.lock` (commit this file).

### Architecture

```
LiveOddsScraper
├── scrape_espn_nba_odds()       delegates to EspnOddsScraper
├── scrape_draftkings_odds()     delegates to DraftKingsScraper
├── parse_draftkings_html()      compatibility wrapper for offline HTML parsing
└── get_all_games()              orchestrates ESPN + DraftKings and displays results

EspnOddsScraper
├── scrape_nba_odds()            ESPN header API → JSON
├── scrape_scoreboard_fallback() ESPN scoreboard fallback
├── parse_header_events()        normalize header API events
└── parse_scoreboard_events()    normalize scoreboard API events

DraftKingsScraper
├── scrape_odds()                Selenium page load and browser lifecycle
└── parse_games()                parser fallback chain
    ├── parse_html()             parsel path (fast, testable) ← preferred
    ├── parse_cb_market()        Selenium cb-market path
    └── parse_event_cells()      Selenium legacy fallback

HttpClient
├── get()                        httpx + tenacity retry + per-domain rate limiting + UA rotation
└── get_json()                   orjson fast parse; curl_cffi impersonation when impersonate= set

OddsComparison
└── find_best_odds()             _normalize_game() maps both scraper schemas → unified view
```

### External Data Caveats

- **Sportsbook pages can change**: DraftKings selectors are parsed defensively with three fallback layers (parsel → cb-market Selenium → event-cell Selenium), but DOM changes or geo/bot gating can still hide odds
- **ESPN odds endpoints are unofficial**: The live scraper calls ESPN's header API first and falls back to the scoreboard API with the same normalized output schema; both endpoints can change without notice
- **curl_cffi impersonation**: Effective against TLS fingerprint checks, not against login walls or account-based rate limits

## 📈 Future Enhancements

- [ ] Add more sportsbooks (BetMGM, PointsBet)
- [ ] Backtesting framework
- [x] Web dashboard with live EV/100 analysis (NiceGUI — `src/frontend/gui/`)
- [ ] Machine learning win probability model
- [ ] Automated daily scraping schedule
- [ ] Playwright network interception replacing Selenium

## ⚠️ Important Notes

- **Legal**: Web scraping odds is legal in most jurisdictions — check local laws
- **Rate Limiting**: The `HttpClient` enforces per-domain minimum delays automatically
- **Terms of Service**: Review each site's ToS before scraping
Found a bug or want to improve it? PRs welcome — just make sure `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check`, `uv run pyright`, and `uv run pytest` pass.

---

Built with ❤️ for sports analytics enthusiasts
