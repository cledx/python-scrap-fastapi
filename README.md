# python-scrap-fastapi

FastAPI + Python scraping service for job listings, with a small CLI for scraping and printing normalized JSON.

## What is included

- FastAPI app with a health endpoint at `/health`
- Job scrapers under `scraper/`:
  - `gaijinpot.py`
  - `daijob.py`
- CLI entrypoint in `cli.py` (currently wired for GaijinPot command)

## Tech stack

- Python 3.11+
- FastAPI
- SQLModel (installed, data layer scaffolding in progress)
- httpx
- BeautifulSoup4
- APScheduler
- python-dotenv
- Uvicorn

## Project layout

- `api/main.py` - FastAPI app entrypoint
- `cli.py` - command-line interface
- `scraper/` - parsing + fetch logic for job sources
- `models/` - model package placeholder
- `scheduler/` - scheduler package placeholder

## Setup

1. Create and activate a virtual environment.
2. Install the project in editable mode:

```bash
pip install -e .
```

This installs dependencies from `pyproject.toml` and registers the `python-scrap-fastapi` CLI command.

## Run the API

From the repository root:

```bash
uvicorn api.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## CLI usage

Run the built-in scraper command:

```bash
python-scrap-fastapi gaijinpot
```

Optional arguments:

- `--url` - override the source URL
- `--timeout` - request timeout in seconds (default: `20.0`)

Example:

```bash
python-scrap-fastapi gaijinpot --timeout 30
```

Output is a JSON array of normalized listings with fields like:

- `title`
- `company`
- `location`
- `url`
- `date_posted`
- `description_snippet`

## Development notes

- Environment variables are loaded from `.env` at API startup via `python-dotenv`.
- Current CLI command coverage is GaijinPot; Daijob scraper logic exists and can be integrated into CLI/API routes next.
- Parser selectors are intentionally resilient and include fallbacks for partial/mixed markup structures.

## Next recommended improvements

- Add API route(s) that return scraper output directly.
- Add CLI subcommand for Daijob.
- Add tests for `parse_gaijinpot_jobs` and `parse_daijob_jobs`.
- Define and persist models using SQLModel.
- Add scheduled scraping with APScheduler.
