# Registry Utility Scripts

This directory contains utility scripts for managing and reporting on the PDS Registry.

## Available Scripts

### Registry Status Report Generator

Generate CSV reports for missing and staged products in the PDS Registry.

**Script:** `generate_registry_status_reports.py`

#### Purpose

This script queries the PDS Registry OpenSearch instance to generate reports for:
1. **Missing products** - Product_Bundle and Product_Collection records marked as missing (`found_in_registry: false`)
2. **Staged products** - Product_Bundle and Product_Collection records with archive status "staged"

This helps track data gaps, identify products that need to be ingested, and monitor products that are staged for archiving.

#### Requirements

- Python 3.12 or higher
- [pds-registry-client](https://github.com/NASA-PDS/registry-client/) - Installation below
- Access credentials to the PDS Registry OpenSearch instance

### Installation

Clone this repo and checkout `develop` branch:

    git clone git@github.com:NASA-PDS/registry.git
    cd registry && git checkout develop

To isolate and be able to re-produce the environment for these scripts, you should use a [Python Virtual Environment](https://docs.python.org/3/tutorial/venv.html). To do so, run:

    python -m venv venv
    source bin/venv/activate  # Substitute with `source bin/venv/activate.csh` for csh/tcsh users

Install the dependencies:

    pip install -r scripts/requirements.txt


#### Configuration

The script requires these environment variables for authentication:

- `REQUEST_SIGNER_AWS_ACCOUNT`
- `REQUEST_SIGNER_AWS_REGION`
- `REQUEST_SIGNER_CLIENT_ID`
- `REQUEST_SIGNER_USER_POOL_ID`
- `REQUEST_SIGNER_IDENTITY_POOL_ID`
- `REQUEST_SIGNER_AOSS_ENDPOINT`
- `REQUEST_SIGNER_COGNITO_USER`
- `REQUEST_SIGNER_COGNITO_PASSWORD`

**Environment File Locations (checked in order):**
1. `$HOME/.pds/.registry-client` (recommended for personal credentials)
2. `./.env` (repository root)

**Example `.env` file:**
```bash
export REQUEST_SIGNER_AWS_ACCOUNT='your_aws_account_id'
export REQUEST_SIGNER_AWS_REGION='us-west-2'
export REQUEST_SIGNER_CLIENT_ID='your_cognito_client_id'
export REQUEST_SIGNER_USER_POOL_ID='your_user_pool_id'
export REQUEST_SIGNER_IDENTITY_POOL_ID='your_identity_pool_id'
export REQUEST_SIGNER_AOSS_ENDPOINT='https://your-opensearch-endpoint.amazonaws.com'
export REQUEST_SIGNER_COGNITO_USER='your_username'
export REQUEST_SIGNER_COGNITO_PASSWORD='your_password'
```

⚠️ **Security:** Never commit your `.env` file with real credentials to version control!

#### Usage

Run from the repository root:

```bash
# Generate reports and commit/push to GitHub (default behavior)
./scripts/generate_registry_status_reports.py

# Generate reports only, without committing to git
./scripts/generate_registry_status_reports.py --no-commit

# Show help
./scripts/generate_registry_status_reports.py --help
```

**Note:** By default, the script will commit and push the generated CSV files to GitHub. Use the `--no-commit` flag to disable this behavior.

#### Output

Generates nine CSV files in `docs/status/`, updates the metrics summary, and appends a row to the burndown history:

**Missing Products (queried from `/en-legacy-registry/_search`):**
1. **`missing_bundles_in_registry.csv`** - All missing Product_Bundle records (all versions)
2. **`missing_bundles_latest_in_registry.csv`** - Only the highest-versioned missing bundle per LID
3. **`missing_bundles_superseded_in_registry.csv`** - Older versions of missing bundles (superseded by a newer version)
4. **`missing_collections_in_registry.csv`** - All missing Product_Collection records (all versions)
5. **`missing_collections_latest_in_registry.csv`** - Only the highest-versioned missing collection per LID
6. **`missing_collections_superseded_in_registry.csv`** - Older versions of missing collections (superseded by a newer version)

**Staged Products (queried from `/*-registry/_search`):**
7. **`staged_bundles_in_registry.csv`** - Staged Product_Bundle records
8. **`staged_collections_in_registry.csv`** - Staged Product_Collection records

**Burndown History:**
9. **`counts_history.csv`** - One row appended per run with total counts per category; never overwritten

**Metrics Summary:**
10. **`README.md`** - Updated with metrics tables showing counts by node

**CSV Formats:**

Missing products — overall, latest, and superseded variants (3 columns each):
```
"NODE_ID","LIDVID","PRODUCT_CLASS"
```

Staged products (4 columns):
```
"NODE_ID","LIDVID","PRODUCT_CLASS","HARVEST_DATE_TIME"
```

Burndown history (one row per run, never overwritten):
```
date,missing_bundles_total,missing_bundles_latest,missing_bundles_superseded,missing_collections_total,missing_collections_latest,missing_collections_superseded,staged_bundles_total,staged_collections_total
```

**Examples:**

Missing products:
```
"PDS_PPI","urn:nasa:pds:maven.rose.raw::1.21","Product_Bundle"
"PDS_ENG","urn:nasa:pds:context::1.2","Product_Bundle"
```

Staged products:
```
"PDS_ATM","urn:nasa:pds:insight_rad::1.0","Product_Bundle","2024-03-15T10:30:00Z"
"PDS_GEO","urn:nasa:pds:mars2020_spice::2.1","Product_Bundle","2024-03-16T14:22:00Z"
```

#### How It Works

1. Loads environment variables from `.env` file (if present)
2. Verifies all required authentication variables are set
3. Executes OpenSearch DSL queries using `pds-registry-client` from:
   - `conf/status/missing_bundles_per_node.json` → `/en-legacy-registry/_search`
   - `conf/status/missing_collections_per_node.json` → `/en-legacy-registry/_search`
   - `conf/status/staged_bundles_per_node.json` → `/*-registry/_search`
   - `conf/status/staged_collections_per_node.json` → `/*-registry/_search`
4. Transforms JSON responses into CSV format
5. For missing products, splits rows by version: the highest LIDVID per LID goes into `*_latest_*` files; older versions go into `*_superseded_*` files
6. Saves all results to `docs/status/`
7. Generates metrics summary and updates `docs/status/README.md` with counts by node
8. Appends one row to `docs/status/counts_history.csv` for burndown tracking (never overwrites)
9. Commits and pushes changes to GitHub (unless `--no-commit` is specified)

#### Query Details

**Missing Products Queries:**
- Return up to 10000 results per query
- Filter by `product_class` (Product_Bundle or Product_Collection)
- Filter by `found_in_registry: false`
- Return fields: `node`, `lidvid`, `product_class`
- Query endpoint: `/en-legacy-registry/_search`

**Staged Products Queries:**
- Return up to 10000 results per query
- Filter by `product_class` (Product_Bundle or Product_Collection)
- Filter by `ops:Tracking_Meta/ops:archive_status: staged`
- Return fields: `ops:Harvest_Info/ops:node_name`, `lidvid`, `product_class`, `ops:Harvest_Info/ops:harvest_date_time`
- Query endpoint: `/*-registry/_search` (searches all registry indices)

**Note:** The script automatically handles the different field names for node information (`node` vs `ops:Harvest_Info/ops:node_name`).

#### Troubleshooting

**"pds-registry-client command not found"**
```bash
pip install pds-registry-client
```

**"Missing required environment variables"**

Ensure you have a `.env` file with all required variables at either:
- `$HOME/.pds/.registry-client` (recommended), or
- Repository root `./.env`

**Authentication errors**

Verify your credentials are correct in the `.env` file. Contact PDS operations if you need access credentials.
