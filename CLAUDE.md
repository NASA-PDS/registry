# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the NASA PDS (Planetary Data System) Registry application repository. It's an **umbrella repository** that integrates multiple sub-components managed in their own repositories:

- **registry-loader**: Tools to load PDS4 products to the registry
- **opensearch**: Data store and search engine backend
- **registry-sweepers**: Suite of scripts consolidating PDS4 product descriptions in OpenSearch
- **registry-api**: PDS Search API service
- **registry-ref-data**: Reference datasets for application integration tests

The repository contains:
- User/administrator documentation (in `docs/`)
- Docker compose scripts for running the full application stack
- Integration tests (in `docker/postman`)
- Python utility scripts for Treks and GeoSTAC-Lola

## Development Setup

### Installation

Install in editable mode with dev dependencies:
```bash
pip install -e '.[dev]'
```

### Pre-commit Hooks

Configure pre-commit hooks (runs on commit and push):
```bash
pre-commit install
pre-commit install -t pre-push
pre-commit install -t prepare-commit-msg
pre-commit install -t commit-msg
```

The hooks check for:
- Secrets detection
- Code formatting
- PEP8 compliance via flake8
- Type hints via mypy
- Import ordering
- Test execution (on push)

## Common Development Commands

### Testing

Run all tests with pytest (uses parallel execution by default):
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=xml
```

Run a single test file:
```bash
pytest src/pds/registry/tests/test_true.py
```

### Linting

Run all linters via tox:
```bash
tox -e lint
```

Or run individual linters:
```bash
flake8 src
mypy src
```

### Testing with Tox

Run tests in Python 3.13 environment:
```bash
tox -e py313
```

Run all tox environments (tests, docs, lint):
```bash
tox
```

### Documentation

Build Sphinx documentation:
```bash
cd docs
make html
```

Generated documentation will be in `docs/build/html/`.

Alternatively, build docs via tox:
```bash
tox -e docs
```

### Docker Development

The `docker/` directory contains the full application stack. Key profiles:

**Start backend services (Elasticsearch + Registry API):**
```bash
cd docker
docker compose --profile=pds-core-registry up --detach
```

**Start development environment with test data (no API):**
```bash
docker compose --profile=dev-api up
```

**Run integration tests with test data:**
```bash
docker compose --profile=int-registry-batch-loader up
```

**Clean up deployment:**
```bash
docker compose --profile=int-registry-batch-loader down --volumes
```

**Note:** Before first run, generate certificates:
```bash
cd docker/certs
./generate-certs.sh
```

## Architecture Notes

### Python Package Structure

- **Namespace package**: Uses `pds` namespace with `pds.registry` package
- **Source layout**: Code is in `src/` directory (NOT flat layout)
- **Version management**: Version stored in `src/pds/registry/VERSION.txt`
- **Entry points**: Two CLI tools are defined:
  - `create-treks-pds4`: Creates PDS4 labels for Treks API layers
  - `create-lola-pds4`: Creates PDS4 labels for Lola point clouds

### Utilities

Two utility modules exist under `src/pds/registry/utils/`:
1. **treks**: Generate PDS4 labels from Treks API data
2. **geostac**: Generate PDS4 labels for Lola GeoSTAC data (requires LOLA GDR data loaded in registry)

### Docker Compose Architecture

The docker-compose.yml defines multiple profiles for different deployment scenarios:
- Components communicate via a Docker network named `pds`
- Elasticsearch/OpenSearch runs on port 9200
- Registry API published on port 8080 (HTTP) and 8443 (HTTPS with self-signed cert)
- Configuration files in `docker/default-config/`
- Environment variables in `docker/.env`

### Integration Testing

Integration tests use Postman collections located in `docker/postman/`. These tests verify the full stack including data loading and API queries.

**For detailed instructions on running and adding integration tests, see [Integration Testing Guide](https://nasa-pds.github.io/registry/developer/integration-testing.html) or [docs/source/developer/integration-testing.rst](docs/source/developer/integration-testing.rst).**

Key points:
- Tests run automatically on feature branches and main branch via GitHub Actions
- To add a test: update TestRail, create Postman request with TestRail ID in assertions, export collection
- Run tests locally: `docker compose --profile=int-registry-batch-loader up`

## Code Quality Standards

- **Python version**: Requires Python 3.13+
- **Line length**: 120 characters (configured in setup.cfg and pyproject.toml)
- **Type hints**: Required, checked by mypy
- **Docstring convention**: Google style
- **Import ordering**: Managed by reorder_python_imports pre-commit hook
- **Coverage**: Tests run with coverage reporting, omitting `__init__.py` and `_version.py`

## CI/CD

Two main workflows:
- **unstable-cicd**: Runs on push to `main`, creates SNAPSHOT releases
- **stable-cicd**: Runs on push to `release/<version>` branches

Both use the NASA-PDS Roundup action for building and releasing.

### Registry Status Reporting

`scripts/generate_registry_status_reports.py` — runs on a schedule to generate CSV reports in `docs/status/` tracking missing, staged, and loaded products, plus interactive burnup charts. Key details:

**Running the script:**
- Always run with the local `venv/`: `./venv/bin/python scripts/generate_registry_status_reports.py --no-commit`
- `pds-registry-client` is resolved from the **same venv as the running Python** (`sys.executable`); do not rely on shell PATH
- Requires AWS/Cognito credentials via `~/.pds/.registry-client` or `.env`
- Run with `--no-commit` to generate locally without pushing

**Query config files (`conf/status/*.json`):**
Each file is an OpenSearch DSL body passed directly to `pds-registry-client`. There are four categories:

| File | Endpoint | Purpose |
|------|----------|---------|
| `missing_bundles_per_node.json` | `/en-legacy-registry/_search` | All bundles from legacy Solr (includes `found_in_registry` field) |
| `missing_collections_per_node.json` | `/en-legacy-registry/_search` | All collections from legacy Solr |
| `staged_bundles_per_node.json` | `/*-registry/_search` | Bundles in new OpenSearch with `archive_status=staged` |
| `staged_collections_per_node.json` | `/*-registry/_search` | Collections with `archive_status=staged` |
| `loaded_bundles_per_node.json` | `/*-registry/_search` | **All** bundles in new OpenSearch (no `archive_status` filter); includes `sort` for pagination |
| `loaded_collections_per_node.json` | `/*-registry/_search` | **All** collections in new OpenSearch; includes `sort` for pagination |

**Data populations — critical distinction:**
- `en-legacy-registry`: populated by the `legacy_registry_sync` sweeper from `https://pds.nasa.gov/services/search/search` (legacy Solr). Each doc has `found_in_registry=true/false` indicating whether that LIDVID is in the new OpenSearch registry.
- `*-registry` (new OpenSearch): the target system. Contains products from legacy Solr migration **plus** products directly harvested from other sources (e.g., PSA/ESA ~900 bundles, ~4000 collections). The loaded count will therefore be **larger** than the legacy Solr count — do not compare them directly.
- Staged products are a subset of loaded products (loaded but `archive_status != archived`). They are an operator concern, not a loading-progress metric.

**Pagination:** The `loaded_*` queries use `run_query_paginated()` (search_after on `_id`) to page through results 10,000 at a time. The AOSS `max_result_window` hard limit is 10,000 — querying with `size > 10000` returns garbage results instead of an error. All other queries use a single-page `run_query()` and are currently limited to 10,000 records.

**Outputs generated:**

| File | Description |
|------|-------------|
| `missing_bundles_in_registry.csv` | Bundles in legacy Solr not yet in new registry, with `superseded` flag |
| `missing_collections_in_registry.csv` | Collections in legacy Solr not yet in new registry, with `superseded` flag |
| `staged_bundles_in_registry.csv` | Bundles in new registry with `archive_status=staged` |
| `staged_collections_in_registry.csv` | Collections in new registry with `archive_status=staged` |
| `loaded_bundles_in_registry.csv` | All bundles in new registry (paginated) |
| `loaded_collections_in_registry.csv` | All collections in new registry (paginated) |
| `counts_history.csv` | Append-only snapshot of missing/staged totals per run |
| `burnup_history.csv` | Cumulative loaded counts by date (all versions) |
| `burnup_by_node.csv` | Per-node cumulative loaded counts (all versions) |
| `burnup_history_latest.csv` | Cumulative loaded counts (latest version per LID only) |
| `burnup_by_node_latest.csv` | Per-node cumulative loaded counts (latest only) |
| `burnup_chart.html` | Interactive Chart.js burnup chart with date-range filtering |
| `README.md` | Auto-updated metrics summary table |

**Burnup chart:** Generated by `generate_burnup_chart_html()`. Uses `ops:Harvest_Info/ops:harvest_date_time` from `loaded_*` CSVs as the time axis. Target = loaded count + missing count per node. Chart defaults to 1-year view; all data is embedded as JSON so filtering is client-side with no regeneration needed.

`scripts/backfill_history.py` — one-off utility to populate `counts_history.csv` from git history of the status CSVs. Safe to re-run (skips dates already present).

```bash
python scripts/backfill_history.py --dry-run   # preview
python scripts/backfill_history.py              # write
```

## Important Notes

- **Secrets detection** is currently disabled in pre-commit (see comments in `.pre-commit-config.yaml`)
- **Black formatter** is disabled (see comments in `.pre-commit-config.yaml`)
- The repository requires several sub-component Docker images to be available for full integration testing
- Default Docker configurations use default passwords - **DO NOT use in production**
- Test data is downloaded from `https://pds-gamma.jpl.nasa.gov/` during integration tests
