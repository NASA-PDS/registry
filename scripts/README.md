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

Diagnose product count discrepancies and unusable file paths or checksums for one or more PDS4 collections.

**Script:** `audit_collection.py`

#### Purpose

Compares product counts across four independent sources to identify where a discrepancy originates:

| Source | What it checks |
|---|---|
| Label (`pds:records`) | Count stated in the collection label |
| Inventory file | Row count of the downloaded PDS4 inventory CSV |
| API `/members` | Total hits from the PDS Search API members endpoint |
| Registry wildcard | OpenSearch `_count` queries (raw, superseded, non-archived, API-visible) |

With `--diff`, fetches the complete LIDVID sets from the inventory file and registry to produce a diff — identifying which specific products are missing from the registry (and therefore absent from the API) and which non-superseded registry products are unexpectedly absent from the inventory.

With `--check-files`, pages through the collection and every member product in the PDS Search API and reports the file paths and checksums that a Deep Archive (AIP/SIP) cannot use:

| Problem | Example |
|---|---|
| `file_ref` is not an absolute URL | The literal string `null`, or a bare path with no scheme and host |
| `md5_checksum` is not an MD5 digest | The literal string `null`, an empty string, or anything other than 32 hexadecimal digits |
| Data `file_ref`s and `md5_checksum`s do not pair up | Two data files but one checksum |
| Label has no `file_ref`, or no `md5_checksum` | A product registered without its label file |

The check reports how many products it examined against the total the API reports, so a failed page or a paging gap is flagged rather than passing as a clean result. It needs no registry credentials, but it reads about 1,000 products per request and so can take a long time for large collections (roughly 40 minutes for a collection of 1.4 million products).

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
python scripts/audit_collection.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \
    --no-registry
```

**Full audit including registry counts:**

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"
python scripts/audit_collection.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0
```

**Audit multiple collections:**

```bash
# Pass LIDVIDs directly
python scripts/audit_collection.py \
    urn:nasa:pds:bundle_a:collection_x::2.0 \
    urn:nasa:pds:bundle_b:collection_y::1.0

# Or supply a file (blank lines and # comments are ignored)
python scripts/audit_collection.py --from-file collections.txt
```

**LIDVID-level diff with file output:**

```bash
python scripts/audit_collection.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \
    --diff \
    --output-dir ./audit_results/
```

**File path and checksum check (no registry credentials needed):**

```bash
python scripts/audit_collection.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \
    --no-registry \
    --check-files \
    --output-dir ./audit_results/
```

**Plain-language explanation of the results:**

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"
python scripts/audit_collection.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \
    --verbose-report
```

**All options:**

```
usage: audit_collection.py [-h] [--api-base URL] [--registry-index INDEX]
                           [--wildcard PAT] [--timeout N] [--no-registry]
                           [--from-file FILE] [--env-file FILE]
                           [--log-level LEVEL] [--diff] [--check-files]
                           [--output-dir DIR] [--verbose-report]
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
  --check-files         Report file_refs that are not absolute URLs and md5_checksums that are not MD5 digests
  --output-dir DIR      Write summary.csv and per-collection diff and file problem CSVs to DIR
  --verbose-report      Explain each source in plain language and, when the API
                        /members count is short, compare harvest times to judge
                        whether the shortfall will resolve on its own
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
  ℹ    ↳ superseded                    2,090
  ℹ    ↳ not archived/certified        0
  ✗  Registry lid:* (API-visible) ¹    1,359,767

  ⚠  Sources disagree — investigate discrepancies above
  ¹  Registry rows use a lid wildcard (...) — approximate, not guaranteed
     to match exact collection membership
```

**With `--check-files`**, a second section reports the file paths and checksums.

When every file reference and checksum is usable:

```
File paths and checksums
──────────────────────────────────────────────────────────────────────
  Products examined                   :  1,359,768
  ✓  Every file_ref is an absolute URL and every md5_checksum is an MD5 digest
```

When there are problems and no `--output-dir` was given, up to 50 are listed, one per line, as `<lidvid>: <kind> <problem>: '<value>'`. This example is a product whose data file has `null` for its `file_ref` and `md5_checksum` and whose label `file_ref` is a bare path with no scheme or host:

```
File paths and checksums
──────────────────────────────────────────────────────────────────────
  Products examined                   :  1,359,768
  ✗  3 problem(s) in 1 product(s) — a Deep Archive cannot be generated
       urn:nasa:pds:mars2020_navcam_ops_stereo:data:nrm_0929_0749414183_910ruc_n0452105vce_15900_0a02llj::1.0: data file file_ref is not an absolute URL: 'null'
       urn:nasa:pds:mars2020_navcam_ops_stereo:data:nrm_0929_0749414183_910ruc_n0452105vce_15900_0a02llj::1.0: data file md5_checksum is not an MD5 digest: 'null'
       urn:nasa:pds:mars2020_navcam_ops_stereo:data:nrm_0929_0749414183_910ruc_n0452105vce_15900_0a02llj::1.0: label file file_ref is not an absolute URL: '/mars2020_navcam_ops_stereo/data/sol/00929/ids/rdr/ncam/NRM_0929_0749414183_910RUC_N0452105VCE_15900_0A02LLJ01.xml'
```

With more than 50 problems, only the count is printed, followed by `(use --output-dir to write the full list to CSV)`. With `--output-dir`, the list is always written to `file_problems.csv` and the report points to it:

```
File paths and checksums
──────────────────────────────────────────────────────────────────────
  Products examined                   :  1,359,768
  ✗  3 problem(s) in 1 product(s) — a Deep Archive cannot be generated
       → audit_results/mars2020_navcam_ops_stereo-data/file_problems.csv
```

The CSV has one row per problem (the `kind` is `data file` or `label file`):

```
lidvid,kind,problem,value
urn:nasa:pds:mars2020_navcam_ops_stereo:data:nrm_0929_0749414183_910ruc_n0452105vce_15900_0a02llj::1.0,data file,file_ref is not an absolute URL,null
urn:nasa:pds:mars2020_navcam_ops_stereo:data:nrm_0929_0749414183_910ruc_n0452105vce_15900_0a02llj::1.0,data file,md5_checksum is not an MD5 digest,null
urn:nasa:pds:mars2020_navcam_ops_stereo:data:nrm_0929_0749414183_910ruc_n0452105vce_15900_0a02llj::1.0,label file,file_ref is not an absolute URL,/mars2020_navcam_ops_stereo/data/sol/00929/ids/rdr/ncam/NRM_0929_0749414183_910RUC_N0452105VCE_15900_0A02LLJ01.xml
```

If a page of members fails to load, or paging misses or repeats products, fewer products are examined than the API reports. The problems found so far are still reported, with a warning in place of a clean result:

```
File paths and checksums
──────────────────────────────────────────────────────────────────────
  Products examined                   :  1,200,000
  ⚠  The API reports 1,359,768 products, so this check is incomplete — a page failed to load or paging missed or repeated products
  ⚠  No problems found in the products that were examined
```

The other problems it can report are `number of file_refs and md5_checksums differ` (for example two data files but one checksum), `no file_ref` (a product with no label file reference) and `no md5_checksum` (a label with no checksum).

**With `--verbose-report`:**

Printed after the table above. It has three parts:

1. **What each source says** — for every count, where it came from and how it compares to the others. For example, the inventory line reports that the table was downloaded from its URL and confirmed to contain N data rows, and whether N matches the label.
2. **What this means** — whether the submitted data is internally consistent (label vs. inventory), and whether the API `/members` total is short of, equal to, or above the expected count. When the API is short, it also states whether the registry holds enough API-visible products to cover the inventory.
3. **Will the `/members` shortfall resolve on its own?** — shown only when the API is short. It compares the collection's `ops:Harvest_Info.ops:harvest_date_time` with the latest harvest time among its non-superseded member products (a registry query, so it needs registry access).

Example, for a collection whose inventory lists 1,359,767 products but whose API `/members` total is 636 short, with registry access:

```
Verbose report: urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0
──────────────────────────────────────────────────────────────────────

What each source says

  Label (pds:records): 1,359,767
      The number of member records the data provider declared in the collection label
      (pds:Inventory/pds:records). This is a claim by the provider and is not verified by anything
      else.

  Inventory file rows: 1,359,767
      The inventory table was downloaded from <inventory-url> and confirmed to contain 1,359,767
      data rows (header excluded). This matches the label.

  API /members hits: 1,359,131
      The total reported by the Search API's /members endpoint for this collection, which is what
      API users see. The members relationship is built by the registry sweepers after the collection
      has been processed, so this count can lag what is actually in the registry. This is 636 fewer
      than the inventory file (1,359,767).

  Registry lid:* (all): 1,361,857
      Every registry product whose LID matches urn:nasa:pds:mars2020_navcam_ops_stereo:data:*,
      including superseded versions and products in any archive status. A wildcard match is
      approximate, not exact collection membership. This is 2,090 more than the inventory file
      (1,359,767). It breaks down into 2,090 superseded, 0 not archived/certified, and 1,359,767
      API-visible.

    of which superseded: 2,090
      Products replaced by a newer version. They are not expected in the current inventory or the
      API. These 2,090 of the 1,361,857 registry products are excluded from the API-visible count.

    of which not archived/certified: 0
      Non-superseded products whose archive status is neither archived nor certified (for example
      staged). They are in the registry but the API does not expose them.

  Registry lid:* (API-visible): 1,359,767
      Non-superseded products with archive status archived or certified: the set the API is able to
      expose. This matches the inventory file. This is 636 more than the API /members total
      (1,359,131). The registry has as many API-visible products as expected, so the /members
      shortfall looks like a gap in the members relationship rather than in loading (this wildcard
      count is approximate; use --diff to confirm).

What this means

  ✓ The label and the downloaded inventory file agree on 1,359,767 members, so the
  submitted data is internally consistent.

  ✗ The API is missing 636 of the 1,359,767 members listed in the inventory file.

  The registry wildcard matches 1,359,767 API-visible products, enough to cover the expected count
  of 1,359,767, but that approximate count does not prove this collection's products are loaded. Use
  --diff to verify the exact LIDVIDs before treating this as a members-relationship gap.

Will the /members shortfall resolve on its own?

  The members relationship is only populated when the registry sweepers process a collection.
  Sweepers do not revisit a collection that has already been processed, so if member products were
  overwritten after that, /members stays stale until the collection itself is re-harvested.
  Comparing harvest times (ops:Harvest_Info/ops:harvest_date_time) shows which situation applies.

  Collection harvested       : 2026-10-01T12:00:00+00:00
  Latest member harvested    : 2026-11-03T22:57:26.477893+00:00  (<latest-member-lidvid>)

  The collection was harvested 33 days, 10:57:26.477893 BEFORE the most recent member product, and
  /members is 636 short. Two explanations fit:

    (1) Sweepers have not yet processed the remaining members listed in the inventory. This should
    resolve once the sweepers finish; recheck after their next run.
    (2) The latest products were overwritten after the collection was processed. The collection will
    not be processed again unless it is also rewritten, so /members will stay short. Re-harvest the
    collection (label and inventory) to fix it.

  If the shortfall is unchanged after the next sweeper run, treat it as (2).
```

Without registry access, the registry entries read "The registry was not queried" and the harvest-time section says it cannot tell, because the latest member's harvest time comes from the registry. When the API total matches the inventory, "What this means" only confirms that the data is consistent and the API total matches, and the harvest-time section is omitted.

The harvest-time comparison matters because the members relationship is populated when the registry sweepers process a collection, and a collection that has already been processed is not processed again. Products that are overwritten without also rewriting the collection therefore leave `/members` stale.

| Collection harvested… | Meaning |
|---|---|
| **before** the latest member | Either (1) sweepers have not yet processed the remaining members and the shortfall should resolve on its own, or (2) the latest products were overwritten after the collection was processed and `/members` will stay short until the collection is re-harvested. If the shortfall is unchanged after the next sweeper run, treat it as (2). |
| **at or after** the latest member | Load order does not explain the shortfall. Check whether the missing products are loaded, superseded, or not archived/certified (use `--diff`). |

**With `--output-dir DIR`:**

| File | Description |
|---|---|
| `summary.csv` | One row per collection with all count columns |
| `<slug>/diff_inventory_not_registry.csv` | LIDVIDs in inventory but missing from registry — these are absent from the API |
| `<slug>/diff_registry_not_inventory.csv` | Non-superseded registry LIDVIDs absent from the inventory — genuinely unexpected |
| `<slug>/file_problems.csv` | With `--check-files`: one row per unusable file path or checksum (`lidvid`, `kind`, `problem`, `value`) |

Where `<slug>` is derived from the last two segments of the collection LID, e.g. `mars2020_navcam_ops_stereo-data`.

**`summary.csv` columns:**

```
lidvid, label, inventory, api_members, registry_all, registry_superseded,
registry_not_archived, registry_api_visible,
diff_inventory_not_registry, diff_registry_not_inventory,
files_examined, file_problems
```

The `diff_*` columns are empty unless `--diff` was passed, and `files_examined` and `file_problems` are empty unless `--check-files` was passed.

#### Interpreting Results

- **`diff_inventory_not_registry`** — products listed in the collection inventory that are not indexed in the registry. These are missing from the API. Investigate whether they were harvested.
- **`diff_registry_not_inventory`** — non-superseded registry products not claimed by the collection inventory. These exist in the registry but the collection does not reference them. Investigate whether they belong to a different collection version.
- **`file_problems.csv`** — products whose registry record has a `file_ref` or `md5_checksum` that cannot go into a manifest. A Deep Archive of any bundle containing them will fail until the records are corrected or the products re-registered. The `value` column holds the offending value (for example `null`). If `Products examined` is lower than the total the API reports, the check did not finish; re-run it.
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
