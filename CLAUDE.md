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
docker compose --profile=pds-core-registry up -d
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
docker compose --profile=int-registry-batch-loader down --volume
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

`scripts/generate_registry_status_reports.py` — runs on a schedule to generate CSV reports in `docs/status/` tracking missing and staged products. Key details:

- Requires AWS/Cognito credentials via `~/.pds/.registry-client` or `.env`
- Uses `pds-registry-client` from the **same venv as the running Python** (resolved via `sys.executable`); do not rely on shell PATH
- Queries `conf/status/*.json` OpenSearch DSL files against the legacy and current registry indices
- For missing products, generates one CSV per type with a `superseded` column (`true`/`false`) indicating whether a LIDVID is the latest version for its LID or an older version
- Appends one row to `docs/status/counts_history.csv` on every run for burndown tracking — this file is **append-only, never overwritten**
- Run with `--no-commit` to generate locally without pushing

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
