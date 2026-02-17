# AGENTS.md

This file provides guidance for AI coding agents working with this repository.

## Project Overview

Doudarr is a FastAPI-based web service that converts Douban movie lists (collections, doulists) into Radarr-compatible lists. It fetches IMDb IDs for Douban movies to enable automatic monitoring and downloading via Radarr.

## Package Management

This project uses **uv** for dependency management. Key files:
- `pyproject.toml`: Project metadata and dependencies
- `uv.lock`: Locked dependency versions (auto-generated)
- Dependencies are managed via `uv add`, not manual editing of requirements.txt

## Development Commands

```bash
# Setup and initialization
./scripts/init_repo.sh          # Initialize repository and setup environment
uv sync                          # Install all dependencies (including dev)

# Code quality
./scripts/lint.sh               # Run linting and auto-fix formatting issues
./scripts/lint.sh --check       # Check only (no auto-fix) - used in CI/CD

# Testing
./scripts/test.sh               # Run pytest test suite
uv run pytest                   # Run tests directly with pytest
uv run pytest tests/test_config.py  # Run specific test file
uv run pytest -v                # Run tests with verbose output
uv run pytest -k "test_throttler"   # Run tests matching pattern

# Running the application
./scripts/local_run.sh          # Start FastAPI development server locally
uv run uvicorn src.main:app --reload   # Alternative way to start server

# Documentation updates
uv run python scripts/update_readme.py # Regenerate README with updated config descriptions

# Dependency management
uv add <package>                # Add runtime dependency
uv add --dev <package>          # Add dev dependency
uv sync                         # Sync dependencies from lock file
```

## Architecture Overview

### Core Components

1. **API Layer** (`src/main.py`): FastAPI application exposing collection and doulist endpoints
2. **Configuration** (`src/config.py`): Environment-based configuration with pydantic-settings
3. **Lists API** (`src/lists.py`): Fetches Douban collections, doulists, and discovers new lists
4. **IMDb API** (`src/imdb.py`): Retrieves IMDb IDs for Douban movies (supports both HTML scraping and douban-idatabase API)
5. **Throttler** (`src/throttler.py`): Rate limiting and retry logic for external API calls
6. **Bootstrap** (`src/bootstrap.py`): Background task for pre-warming IMDb cache
7. **Sync** (`src/sync.py`): Synchronizes IMDb cache across multiple Doudarr instances

### Data Flow

- **List Fetching**: Calls Douban mobile API to get movie lists from collections/doulists
- **IMDb Lookup**: 
  - If `douban_idatabase_url` configured: Calls douban-idatabase API for IMDb IDs
  - Otherwise: Scrapes Douban movie pages to extract IMDb IDs
- **Caching**: Uses diskcache for persistent caching of lists and IMDb IDs
- **API Response**: Returns list of movies with IMDb IDs for Radarr consumption

## Key Design Patterns

### IMDb ID Lookup Strategy

The service supports two methods for IMDb ID retrieval:

1. **douban-idatabase Integration** (recommended): Fast API-based lookup when `douban_idatabase_url` is configured
2. **HTML Scraping Fallback**: Parses Douban movie pages when douban-idatabase is not available

The factory pattern in `get_imdb_api()` selects the appropriate implementation based on configuration.

### Caching Strategy

Three-level caching:
- **List Cache**: Caches Douban list contents with configurable TTL
- **IMDb Cache**: Permanently caches found IMDb IDs, temporary cache for not-found cases
- **Throttler State**: Tracks rate limiting status per host

### Rate Limiting

Multi-host throttler that handles:
- **Douban-specific**: Detects 302 redirects to `sec.douban.com`
- **Standard HTTP 429**: Respects `Retry-After` and `X-RateLimit-Reset` headers
- **Per-host tracking**: Independent rate limit state for each external service

## Configuration Management

All configuration is done via environment variables with `DOUDARR_` prefix. The configuration is automatically documented in README.md via `scripts/update_readme.py`.

**Important**: After adding or modifying configuration fields in `src/config.py`, always run:
```bash
python scripts/update_readme.py
```

## Docker Deployment

The application is containerized with Docker. The Dockerfile uses multi-stage builds and the service can be deployed via:
```bash
docker run -d --name doudarr -p 8000:8000 -v /path/to/cache:/app/cache kfstorm/doudarr:latest
```

## Integration with douban-idatabase

Doudarr can integrate with [douban-idatabase](https://github.com/kfstorm/douban-idatabase) to fetch IMDb IDs via API instead of scraping.

When `DOUDARR_DOUBAN_IDATABASE_URL` is configured, Doudarr calls the douban-idatabase API instead of scraping Douban HTML:

- **Endpoint**: `GET /api/item?douban_id={douban_id}`
- **Authentication**: Optional via `X-API-Key` header
- **Benefits**: Faster lookups, no HTML parsing, centralized rate limiting
- **Fallback**: None - when configured, douban-idatabase becomes single source of truth

## Important Files

- `src/config.py`: Configuration definitions (update this, then run `update_readme.py`)
- `src/main.py`: FastAPI application and API endpoints
- `src/imdb.py`: IMDb ID lookup implementations (HTML scraping + API)
- `src/throttler.py`: Rate limiting middleware
- `scripts/update_readme.py`: Auto-generates configuration documentation

## API Endpoints

### Collection
- **URL**: `/collection/{id}`
- **Query Params**: `min_rating` (optional) - Filter movies by minimum rating
- **Example**: `http://localhost:8000/collection/movie_weekly_best?min_rating=8`

### Doulist
- **URL**: `/doulist/{id}`
- **Query Params**: `min_rating` (optional) - Filter movies by minimum rating
- **Example**: `http://localhost:8000/doulist/43556565?min_rating=7`

### Stats
- **URL**: `/` or `/stats`
- **Returns**: Cache sizes and throttler status

### Sync (Internal)
- **URL**: `/sync`
- **Method**: POST
- **Purpose**: Receives IMDb cache from other Doudarr instances
- **Auth**: Requires `apikey` query parameter

## Background Tasks

### Bootstrap Task
Periodically discovers new Douban lists and pre-warms IMDb cache to improve response times. Controlled by:
- `DOUDARR_BOOTSTRAP_INTERVAL_SECONDS`
- `DOUDARR_BOOTSTRAP_LIST_INTERVAL_SECONDS`
- `DOUDARR_BOOTSTRAP_LISTS_MAX`

### Sync Task
Synchronizes IMDb cache to other Doudarr instances for distributed caching. Controlled by:
- `DOUDARR_SYNC_IMDB_CACHE_INTERVAL_SECONDS`
- `DOUDARR_SYNC_IMDB_CACHE_TO`

## Testing

The project uses pytest for unit testing with comprehensive test coverage:

- **Test Framework**: pytest with pytest-asyncio for async tests
- **Test Location**: `tests/` directory
- **Test Files**:
  - `tests/test_config.py`: Configuration tests
  - `tests/test_throttler.py`: Throttler and rate limiting tests
  - `tests/test_imdb.py`: IMDb API implementation tests (both HTML and database)
- **Running Tests**: Use `./scripts/test.sh` or `pytest` directly
- **Test Coverage**: 
  - Configuration loading and validation
  - HTTP 429 rate limiting (new)
  - Douban rate limiting (302 redirects)
  - IMDb ID lookup via HTML scraping
  - IMDb ID lookup via douban-idatabase API (new)
  - Caching behavior
  - Error handling

## Testing Considerations

When testing:
1. Cache directory is required - mount `/app/cache` volume
2. First requests are slow due to IMDb lookup delays
3. Rate limiting can cause delays - adjust `*_DELAY_MAX_SECONDS` configs for testing
4. Test both with and without `douban_idatabase_url` to verify both code paths

## Common Development Tasks

### Adding New Configuration
1. Add field to `AppConfig` in `src/config.py`
2. Use Chinese descriptions for consistency
3. Run `python scripts/update_readme.py` to update documentation
4. Test with environment variable: `DOUDARR_YOUR_NEW_FIELD=value`

### Modifying IMDb Lookup
- Both implementations in `src/imdb.py` extend `ImdbApi` base class
- Must implement `fetch_imdb_id(douban_id, douban_item)` method
- Factory `get_imdb_api()` selects implementation based on config
- Caching is handled by base class `get_imdb_id()` method

### Adding New List Source
- Extend `BaseApi` in `src/lists.py`
- Implement specific API endpoints and parsing logic
- Add new route in `src/main.py`
- Follow existing patterns for caching and filtering
