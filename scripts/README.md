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
    source venv/bin/activate  # Substitute with `source venv/bin/activate.csh` for csh/tcsh users

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

Generates four CSV files in `docs/status/` and updates the metrics summary:

**Missing Products (queried from `/en-legacy-registry/_search`):**
1. **`missing_bundles_in_registry.csv`** - Missing Product_Bundle records
2. **`missing_collections_in_registry.csv`** - Missing Product_Collection records

**Staged Products (queried from `/*-registry/_search`):**
3. **`staged_bundles_in_registry.csv`** - Staged Product_Bundle records
4. **`staged_collections_in_registry.csv`** - Staged Product_Collection records

**Metrics Summary:**
5. **`README.md`** - Updated with metrics tables showing counts by node

**CSV Formats:**

Missing products (3 columns):
```
"NODE_ID","LIDVID","PRODUCT_CLASS"
```

Staged products (4 columns):
```
"NODE_ID","LIDVID","PRODUCT_CLASS","HARVEST_DATE_TIME"
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
5. Saves results to `docs/status/`
6. Generates metrics summary and updates `docs/status/README.md` with counts by node
7. Commits and pushes changes to GitHub (unless `--no-commit` is specified)

#### Query Details

**Missing Products Queries:**
- Return up to 2000 results per query
- Filter by `product_class` (Product_Bundle or Product_Collection)
- Filter by `found_in_registry: false`
- Return fields: `node`, `lidvid`, `product_class`
- Query endpoint: `/en-legacy-registry/_search`

**Staged Products Queries:**
- Return up to 2000 results per query
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

---

### Collection Audit Script

Diagnose product count discrepancies for one or more PDS4 collections.

**Script:** `audit_collection_counts.py`

#### Purpose

Compares product counts across four independent sources to identify where a discrepancy originates:

| Source | What it checks |
|---|---|
| Label (`pds:records`) | Count stated in the collection label |
| Inventory file | Row count of the downloaded PDS4 inventory CSV |
| API `/members` | Total hits from the PDS Search API members endpoint |
| Registry wildcard | OpenSearch `_count` queries (raw, superseded, non-archived, API-visible) |

With `--diff`, fetches the complete LIDVID sets from the inventory file and registry to produce a diff — identifying which specific products are missing from the registry (and therefore absent from the API) and which non-superseded registry products are unexpectedly absent from the inventory.

#### Requirements

- Python 3.9 or higher
- [pds-registry-client](https://github.com/NASA-PDS/registry-client/) — provides the `pds.aossrequestsigner` library used for signed OpenSearch requests
- Access credentials to the PDS Registry OpenSearch instance

#### Installation

Follow the shared installation steps in the [Installation](#installation) section above, then verify the registry client library is available:

```bash
python -c "import pds.aossrequestsigner; print('OK')"
```

If the import fails, ensure `pds.registry-client` is listed in `scripts/requirements.txt` and re-run:

```bash
pip install -r scripts/requirements.txt
```

#### Configuration

The script reads credentials **from the shell environment**. Source your credentials file before running — do not rely on the optional `--env-file` flag for routine use:

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"
```

The following environment variables must be set:

- `REQUEST_SIGNER_AWS_ACCOUNT`
- `REQUEST_SIGNER_AWS_REGION`
- `REQUEST_SIGNER_CLIENT_ID`
- `REQUEST_SIGNER_USER_POOL_ID`
- `REQUEST_SIGNER_IDENTITY_POOL_ID`
- `REQUEST_SIGNER_AOSS_ENDPOINT`
- `REQUEST_SIGNER_COGNITO_USER`
- `REQUEST_SIGNER_COGNITO_PASSWORD`

#### Usage

**Count comparison only (no registry queries):**

```bash
python scripts/audit_collection_counts.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \
    --no-registry
```

**Full audit including registry counts:**

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"
python scripts/audit_collection_counts.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0
```

**Audit multiple collections:**

```bash
# Pass LIDVIDs directly
python scripts/audit_collection_counts.py \
    urn:nasa:pds:bundle_a:collection_x::2.0 \
    urn:nasa:pds:bundle_b:collection_y::1.0

# Or supply a file (blank lines and # comments are ignored)
python scripts/audit_collection_counts.py --from-file collections.txt
```

**LIDVID-level diff with file output:**

```bash
python scripts/audit_collection_counts.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \
    --diff \
    --output-dir ./audit_results/
```

**All options:**

```
usage: audit_collection_counts.py [-h] [--api-base URL] [--registry-index INDEX]
                                  [--wildcard PAT] [--timeout N] [--no-registry]
                                  [--from-file FILE] [--env-file FILE]
                                  [--log-level LEVEL] [--diff] [--output-dir DIR]
                                  [LIDVID ...]

positional arguments:
  LIDVID                One or more collection LIDVIDs to audit

options:
  --api-base URL        PDS Search API base URL (default: https://pds.mcp.nasa.gov/api/search/1)
  --registry-index IDX  OpenSearch index path (default: /*-registry/_count)
  --wildcard PAT        Override lid wildcard pattern (single LIDVID only)
  --timeout N           Per-request timeout in seconds (default: 30)
  --no-registry         Skip all registry queries
  --from-file FILE      Newline-separated file of collection LIDVIDs
  --env-file FILE       Supplement shell credentials from a file (optional)
  --log-level LEVEL     debug, info, warn, warning (default: info)
  --diff                Fetch full LIDVID sets and compute inventory vs. registry diff
  --output-dir DIR      Write summary.csv and per-collection diff CSVs to DIR
```

#### Output

**Terminal report** (always printed):

```
Collection audit: urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0
──────────────────────────────────────────────────────────────────────
  ✓  Label (pds:records)               1,359,767
  ✓  Inventory file rows               1,359,767
  ✗  API /members hits                 1,359,131
  ℹ  Registry lid:* (all)              1,361,857
  ℹ    ↳ superseded                    2,089
  ℹ    ↳ not archived/certified        0
  ✗  Registry lid:* (API-visible) ¹    1,359,767

  ⚠  Sources disagree — investigate discrepancies above
  ¹  Registry rows use a lid wildcard (...) — approximate, not guaranteed
     to match exact collection membership
```

**With `--output-dir DIR`:**

| File | Description |
|---|---|
| `summary.csv` | One row per collection with all count columns |
| `<slug>/diff_inventory_not_registry.csv` | LIDVIDs in inventory but missing from registry — these are absent from the API |
| `<slug>/diff_registry_not_inventory.csv` | Non-superseded registry LIDVIDs absent from the inventory — genuinely unexpected |

Where `<slug>` is derived from the last two segments of the collection LID, e.g. `mars2020_navcam_ops_stereo-data`.

**`summary.csv` columns:**

```
lidvid, label, inventory, api_members, registry_all, registry_superseded,
registry_not_archived, registry_api_visible,
diff_inventory_not_registry, diff_registry_not_inventory
```

#### Interpreting Results

- **`diff_inventory_not_registry`** — products listed in the collection inventory that are not indexed in the registry. These are missing from the API. Investigate whether they were harvested.
- **`diff_registry_not_inventory`** — non-superseded registry products not claimed by the collection inventory. These exist in the registry but the collection does not reference them. Investigate whether they belong to a different collection version.
- **Registry lid:* counts are approximate** — the wildcard `<collection_lid>:*` matches any product whose LID begins with that prefix. It does not guarantee exact membership in the audited collection version.

#### Troubleshooting

**`ModuleNotFoundError: No module named 'pds'`**

The `pds.aossrequestsigner` library is not installed. Run:

```bash
pip install -r scripts/requirements.txt
```

**`ERROR Missing required environment variables`**

Source your credentials file before running the script:

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"
```

**`ERROR Registry authentication failed`**

Verify your Cognito credentials are current. Temporary credentials expire; re-source your credentials file.
