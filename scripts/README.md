# Registry Utility Scripts

This directory contains utility scripts for managing and reporting on the PDS Registry.

## Available Scripts

### Registry Status Report Generator

Generate CSV reports for missing, staged, loaded and invalid-`file_ref` products in the PDS Registry.

**Script:** `generate_registry_status_reports.py`

#### Purpose

This script queries the PDS Registry OpenSearch instance to generate reports for:
1. **Missing products** - Product_Bundle and Product_Collection records marked as missing (`found_in_registry: false`)
2. **Staged products** - Product_Bundle and Product_Collection records with archive status "staged"
3. **Loaded products** - all Product_Bundle and Product_Collection records in the registry, used for the burnup chart
4. **Invalid `file_ref` products** - products whose label or data `file_ref` does not start with `https://`

This helps track data gaps, identify products that need to be ingested, monitor products that are staged for archiving, and find products whose files cannot be served.

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
# Generate reports only, without committing to git (default behavior)
./scripts/generate_registry_status_reports.py

# Generate reports and commit/push to GitHub
./scripts/generate_registry_status_reports.py --commit

# Show help
./scripts/generate_registry_status_reports.py --help
```

**Note:** By default, the script does not commit or push anything. Use the `--commit` flag to commit and push the generated files to GitHub.

#### Output

Generates CSV files in `docs/status/` and updates the metrics summary:

**Missing Products (queried from `/en-legacy-registry/_search`):**
1. **`missing_bundles_in_registry.csv`** - Missing Product_Bundle records
2. **`missing_collections_in_registry.csv`** - Missing Product_Collection records

**Staged Products (queried from `/*-registry/_search`):**
3. **`staged_bundles_in_registry.csv`** - Staged Product_Bundle records
4. **`staged_collections_in_registry.csv`** - Staged Product_Collection records

**Loaded Products (queried from `/*-registry/_search`, paginated):**
5. **`loaded_bundles_in_registry.csv`** - All Product_Bundle records
6. **`loaded_collections_in_registry.csv`** - All Product_Collection records

**Invalid `file_ref` Products (queried from `/*-registry/_search`, paginated):**
7. **`bad_file_ref_bundles_in_registry.csv`** - One row per invalid `file_ref` value on a Product_Bundle
8. **`bad_file_ref_collections_in_registry.csv`** - One row per invalid `file_ref` value on a Product_Collection
9. **`bad_file_ref_products_in_registry.csv`** - All other product classes, grouped by node, bundle, collection and archive status

**Metrics Summary and History:**
10. **`README.md`** - Updated with metrics tables showing counts by node
11. **`counts_history.csv`**, **`burnup_*.csv`** and **`burnup_chart.html`** - Count history and the burnup chart

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

Invalid `file_ref` bundles and collections (6 columns, one row per invalid value):
```
node,lidvid,product_class,archive_status,file_ref_field,file_ref
PDS_ATM,urn:nasa:pds:insight_rad::1.0,Product_Bundle,archived,Label_File_Info,.../insight_rad_bundle.xml
PDS_GEO,urn:nasa:pds:mars2020_spice::2.1,Product_Bundle,staged,Label_File_Info,s3://.../mars2020_spice_bundle.xml
```

Invalid `file_ref` other products (10 columns, one row per node, bundle, collection and archive status):
```
node,bundle_lid,collection_lid,archive_status,products,values,value_kinds,file_ref_fields,example_lidvid,example_file_ref
PDS_GEO,urn:nasa:pds:mars2020_spice,urn:nasa:pds:mars2020_spice:data,archived,120,240,local path,Data_File_Info; Label_File_Info,urn:nasa:pds:mars2020_spice:data:p001::1.0,.../p001.xml
```

Only `https://` file references are valid, because the archive is served through CloudFront. Any other value is reported, including `s3://`, regardless of archive status. Empty values and the placeholder `null` are ignored. The directory part of a reported value is a path on the harvesting machine, so the reports keep only the scheme and the file name.

#### How It Works

1. Loads environment variables from `.env` file (if present)
2. Verifies all required authentication variables are set
3. Executes OpenSearch DSL queries using `pds-registry-client` from:
   - `conf/status/missing_bundles_per_node.json` → `/en-legacy-registry/_search`
   - `conf/status/missing_collections_per_node.json` → `/en-legacy-registry/_search`
   - `conf/status/staged_bundles_per_node.json` → `/*-registry/_search`
   - `conf/status/staged_collections_per_node.json` → `/*-registry/_search`
   - `conf/status/loaded_bundles_per_node.json` and `loaded_collections_per_node.json` → `/*-registry/_search`
   - `conf/status/bad_file_ref_bundles_per_node.json`, `bad_file_ref_collections_per_node.json` and `bad_file_ref_products_per_node.json` → `/*-registry/_search`
4. Transforms JSON responses into CSV format
5. Saves results to `docs/status/`
6. Generates metrics summary and updates `docs/status/README.md` with counts by node
7. Commits and pushes changes to GitHub (only if `--commit` is specified)

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

**Invalid `file_ref` Queries:**
- Paginate with `search_after` on `_id`, 10,000 results per page
- Match Product_Bundle, Product_Collection, or all other product classes
- Match any product where `ops:Label_File_Info/ops:file_ref` or `ops:Data_File_Info/ops:file_ref` does not match the regular expression `https://.*`, with no condition on `archive_status`
- Return fields: `ops:Harvest_Info/ops:node_name`, `lidvid`, `product_class`, `ops:Tracking_Meta/ops:archive_status`, `ops:Label_File_Info/ops:file_ref`, `ops:Data_File_Info/ops:file_ref`
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

**Is the inventory still being loaded? (needs registry credentials):**

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"
python scripts/audit_collection.py \
    urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \
    --load-status --active-days 3
```

`--load-status` finds the products that are in the inventory *and* in the registry, takes the newest `harvest_date_time` among them, and says whether the collection is:

| Verdict | Meaning |
|---|---|
| `complete` | Every inventory product is loaded |
| `not_started` | No inventory product is in the registry |
| `loading` | Partially loaded; the newest loaded member was harvested within `--active-days` (default 3), so loading looks active |
| `stalled` | Partially loaded; nothing in the inventory has been harvested for longer than `--active-days`, so the node needs to load the rest |

Registry products that the inventory does not list (for example an older version of a product) are ignored for the verdict, because their harvest times say nothing about whether the current inventory is being loaded. The report also gives the newest harvest time among those other products. The verdict is added to `summary.csv` (`inventory_loaded`, `inventory_not_loaded`, `latest_member_harvest`, `load_verdict`).

**All options:**

```
usage: audit_collection.py [-h] [--api-base URL] [--registry-index INDEX]
                           [--wildcard PAT] [--timeout N] [--no-registry]
                           [--from-file FILE] [--env-file FILE]
                           [--log-level LEVEL] [--diff] [--load-status]
                           [--active-days N] [--check-files]
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
  --load-status         Report how much of the inventory is loaded and whether loading looks active
  --active-days N       With --load-status, "still loading" means the newest loaded member was
                        harvested within N days (default: 3)
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
- **Superseded counts on the ATM registry** — on that index `ops:Provenance/ops:superseded_by` can be read but not searched, so the `_count` queries report `superseded` as 0 and the "API-visible" count includes superseded products. The `--diff` and `--load-status` LIDVID sets are filtered client-side and are not affected.

#### Troubleshooting

**`ModuleNotFoundError: No module named 'pds'`**

The `pds.aossrequestsigner` library is not installed. Run:

```bash
pip install -r scripts/requirements.txt
```

**`ModuleNotFoundError: No module named 'pds.aossrequestsigner'`** (the package is installed)

This repository installs its own `pds` package in editable mode, which hides the registry client's
`pds.aossrequestsigner` in the same virtualenv. Run the audit scripts with a virtualenv that has the
registry client but not this repository's editable install, for example the `registry-client` checkout's
virtualenv:

```bash
REGISTRY_CLIENT_VENV="<path-to-registry-client-venv>"
"${REGISTRY_CLIENT_VENV}/bin/python" scripts/audit_unprocessed_products.py --output-dir ./audit_unprocessed/
```

**`ERROR Missing required environment variables`**

Source your credentials file before running the script:

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"
```

**`ERROR Registry authentication failed`**

Verify your Cognito credentials are current. Temporary credentials expire; re-source your credentials file.

---

### Unprocessed Product Audit

Find API-visible products that the registry sweepers' ancestry sweeper has not processed, and say why.

**Script:** `audit_unprocessed_products.py` (helpers in `unprocessed_audit/`). Design: [`docs/developer/audit-unprocessed-products-design.md`](../docs/developer/audit-unprocessed-products-design.md). Column meanings, the technical meaning of each rule and step-by-step checks for every CSV rationale: [`docs/developer/audit-unprocessed-products-reference.md`](../docs/developer/audit-unprocessed-products-reference.md).

#### Purpose

Products without `ops:Provenance/ops:ancestor_refs` and a current `ops:Provenance/ops:registry_sweepers_ancestry_version` stamp are missing from `/members` and related API results. Some are waiting on the sweeper or on a parent collection that is still loading; others are broken. The audit reads the registry and `registry-refs` indices directly (the public API does not expose refs), groups products by parent collection, and gives each product one rule, a severity (`expected` or `anomalous`) and a one-line rationale:

| Rule | Severity | Meaning |
|---|---|---|
| `no_parent_by_design` | expected | Product class never belongs to a collection |
| `collection_not_loaded_pending` / `_overdue` | expected / anomalous | Parent collection not in the registry; overdue after `--product-grace-days` |
| `collection_pending` / `collection_overdue` | expected / anomalous | Parent collection unprocessed; overdue after `--collection-grace-days` |
| `reloaded_after_collection` | anomalous | Collection was processed, then the product was re-harvested; re-harvesting the collection fixes it |
| `inventory_version_mismatch` | anomalous | The collection's inventory lists the product at a different version than the registry holds; load that version (re-harvesting the collection does not help) |
| `not_in_collection_inventory` | anomalous | The product is registered under the collection but its current inventory does not list it under any version; the node decides whether to add it to the inventory or remove it |
| `bare_lid_in_inventory` | anomalous | The collection's inventory lists the product by LID without a version, which the sweepers do not follow; re-harvesting writes the same refs |
| `sweeper_miss` | anomalous | Collection processed at or after the product's harvest and the product is in refs, but has no ancestry |
| `refs_missing_pending` / `refs_missing` | expected / anomalous | No `registry-refs` document lists the product |
| `stale_stamp` | anomalous | Product stamped with an older ancestry version than its processed collection |

Only non-superseded products with archive status `archived` or `certified` are examined. The audit is read-only.

**Reading the report.** `summary.md` opens with a "What needs to happen" table in plain language, grouped by who can fix each problem:

| Who | Problems |
|---|---|
| Node | A collection is not loaded, the inventory lists a different version, or the inventory does not list the product; stale or missing refs, products loaded after their collection was processed, or an older stamp (the node re-harvests the collection, then EN runs the sweepers) |
| EN | A collection stamped without a link to its bundle (a sweepers bug; EN re-harvests it and runs the fixed sweepers); a loaded collection the sweepers have not processed; fixes to the registry itself |
| Sweepers team | `sweeper_miss`, or an inventory that lists products by LID without a version |
| Needs a closer look | `refs_missing` products that could not be checked against the collection inventory |
| No action | Products loaded recently |

Each problem is marked **Orphaned** (no registry record confirms the product's collection; the collection named for it is a best guess from its identifier) or **Not processed** (the refs list the product but the sweepers never processed it). The same counts are in `metrics.json` under `owners`. `refs_missing` needs the collection inventory to be classified, so run without `--no-inventory` when owners matter.

```bash
AUDITS_DIR="<directory containing one sub-directory per node, each with the audit output>"
python scripts/audit_rollup.py --audits-dir "${AUDITS_DIR}"
```

`audit_rollup.py` reads each node's `metrics.json` and prints one table of those counts, node by node.

A per-product CSV can hold millions of rows. `audit_product_samples.py` reads the per-product CSV of every node and writes `<node>/product_samples.csv`: for each group of anomalous products (one rule in one collection) the group's size and up to `--per-group` example products (the lowest LIDVIDs, so reruns match), each with its owner and the reason. It is small enough to commit.

```bash
python scripts/audit_product_samples.py --audits-dir "${AUDITS_DIR}" --output-dir "${AUDITS_DIR}" --per-group 10
```

#### Usage

Credentials come from the shell environment, as for the collection audit (`pip install -r scripts/requirements.txt` first).

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"

# Dry run: one node, stop after 5,000 candidates
NODE="<node-name>"
python scripts/audit_unprocessed_products.py \
    --output-dir ./audit_unprocessed/ --node "${NODE}" --max-products 5000

# Full run; compare with a previous run
PREVIOUS_CSV="<path-to-previous-unprocessed_products.csv>"
python scripts/audit_unprocessed_products.py \
    --output-dir ./audit_unprocessed/ --previous-csv "${PREVIOUS_CSV}" --gzip
```

Run `python scripts/audit_unprocessed_products.py --help` for all options.

When a product is in no `registry-refs` document, the audit reads the current inventory of its collection (the URL is on the collection's registry document) to tell stale refs, a product listed under another version, and a product the inventory does not list. Inventories come from the data providers' servers and can be slow to download (tens of megabytes for the large collections). Pass `--no-inventory` to skip the downloads; such products are then reported as `refs_missing`. Pass `--inventory-cache-dir DIR` to keep the downloaded inventories and reuse them in later runs (a kept file is never refreshed; delete it to fetch the current one). The login credentials expire after about an hour, so the audit renews them automatically during a long run.

#### Output

Written to `--output-dir`; none of it is meant to be committed (the products CSV can reach hundreds of MB).

| File | Content |
|---|---|
| `summary.md` | The report (also printed): anomalies by rule and node, anomalous collections with their bundles, stamped collections with empty refs, expected-pending counts, orphans, class and age breakdowns, diff against the previous run |
| `unprocessed_products.csv` | One row per product, including `rule`, `severity` and `rationale` |
| `collections.csv` | One row per collection with state, bundles and refs coverage |
| `anomalous_collections.txt` | Collection LIDVIDs to look at or re-harvest, for `audit_collection.py --from-file`: those rooting anomalous products, and those stamped with empty refs that have a bundle |
| `metrics.json` | Machine-readable totals, anomalous counts per rule, and the anomalous and empty-refs collection lists; the baseline for a later `--check` |

#### Regression check

`--check` turns the audit into a pass/fail test that can run unattended. It evaluates these invariants and exits with code 2 when one is violated (0 when all hold, 1 on an error):

| Invariant | Fails when |
|---|---|
| `no_anomalous_products` | Any product is anomalous (no baseline) |
| `no_new_anomalies` | A collection newly roots anomalous products, or a rule's anomalous count grew (baseline) |
| `no_empty_refs_collection_with_bundle` | A collection with a bundle is stamped with empty refs (no baseline), or newly so (baseline) |
| `superseded_by_mapped` | A node's registry index does not map `ops:Provenance/ops:superseded_by`, so the API cannot exclude superseded products there (always) |

Without `--baseline` every anomaly fails the check. Pass the `metrics.json` of an earlier run to fail only for what is new since then, so a known backlog does not fail every run. The baseline must cover the same nodes and ancestry version. `--check` cannot be combined with `--max-products`. `--no-mapping-check` skips reading the index mappings. `--history-csv FILE` appends one row of totals per run, with a column per rule, for trend charts.

```bash
BASELINE="<path-to-the-previous-metrics.json>"
HISTORY="<path-to-the-history.csv>"
python scripts/audit_unprocessed_products.py \
    --output-dir ./audit_unprocessed/ --check --baseline "${BASELINE}" --history-csv "${HISTORY}" \
    --inventory-cache-dir ./inventory_cache/
echo "exit code: $?"
```

The check result is also appended to `summary.md` under "Regression check".

---

### Collection Re-harvest Download

Download the label and inventory of collections that need to be re-harvested, from the URLs the registry holds for them.

**Script:** `download_collection_files.py`

#### Purpose

Re-harvesting a collection rewrites its collection document (clearing its ancestry stamp) and regenerates its `registry-refs` documents from the inventory, so the registry sweepers process the collection and its members again. This script asks the PDS Search API where each collection's label and inventory are, downloads them, and checks them against the registry. It only needs the public API and the data providers' servers; no registry credentials.

Files are stored mirrored under the URL they came from:

```
<output-dir>/files/<host>/<url path>   ->   <scheme>://<host>/<url path>
```

so one Harvest `fileRef` per host maps every local path back to the original URL. The label and inventory of a collection always land in the same directory, which Harvest requires.

#### Usage

```bash
OUTPUT_DIR="./reharvest"
COLLECTIONS_FILE="./audit_unprocessed/anomalous_collections.txt"

# Show URLs and the fileRef prefixes first; nothing is downloaded
python scripts/download_collection_files.py --list-only --output-dir "${OUTPUT_DIR}" --from-file "${COLLECTIONS_FILE}"

# Download the label and inventory of every collection in the list
python scripts/download_collection_files.py --output-dir "${OUTPUT_DIR}" --from-file "${COLLECTIONS_FILE}"

# Or take the collections straight from an audit (default rules: refs_missing, reloaded_after_collection,
# sweeper_miss, stale_stamp)
AUDIT_CSV="./audit_unprocessed/unprocessed_products.csv.gz"
python scripts/download_collection_files.py --output-dir "${OUTPUT_DIR}" --from-audit-csv "${AUDIT_CSV}"
```

Use `--skip-existing` to resume an interrupted run. Inventories can be large (hundreds of thousands of rows).

#### Output

| File | Content |
|---|---|
| `files/<host>/...` | The downloaded labels and inventories |
| `manifest.csv` | One row per collection: URLs, `url_base`, local paths, MD5s from the registry and from the download, record counts, status |
| `harvest_config_snippet.xml` | The `<load><directories>` paths and the `<fileInfo><fileRef replacePrefix=... with=... />` entries to merge into your Harvest configuration |

The manifest columns `md5_changed_since_harvest` and `records_match` flag collections to look at before re-harvesting:

- `md5_changed_since_harvest` is `True` when a downloaded file's MD5 differs from the checksum the registry holds, meaning the data provider changed the file after the collection was harvested. A re-harvest picks up the new content.
- `records_match` is `False` when the downloaded label's `pds:Inventory/pds:records` differs from the number of rows in the downloaded inventory. That is a problem in the provider's data that re-harvesting does not fix.

A collection whose registered label `file_ref` is not a URL (for example a local filesystem path) cannot be downloaded and is listed in the summary.

---

### Index Mapping Audit

Compare the OpenSearch index mappings of every node and report the differences.

**Script:** `audit_index_mappings.py` (helpers in `unprocessed_audit/mapping_audit.py`).

#### Purpose

Each node has its own `<node>-registry` index, created at a different time, so their mappings drift. A field missing from a mapping is returned in `_source` but cannot be searched (for example `ops:Provenance/ops:superseded_by` on the ATM index, issue #611). A field mapped with different types on different nodes behaves differently under the same query. The audit reads `GET /<index>/_mapping` for every node, and with `--include-refs` the `<node>-registry-refs` indices, flattens each mapping to `field -> type`, and compares the indices of a group with each other. A field's expected type is the most common type among the indices that define it; a field defined on at least `--presence-threshold` (default 0.8) of the indices is expected on all of them.

| Discrepancy | Meaning |
|---|---|
| `missing_field` | Defined on most indices of the group, absent on this one |
| `type_mismatch` | Defined with a different type than on most indices |
| `dynamic_mismatch` | The index's `dynamic` setting differs from most indices |
| `index_missing` | A `registry-refs` index that does not exist |

A missing `ops:` field or core top-level field (`lid`, `lidvid`, `vid`, `title`, `description`, `product_class`, `alternate_ids`, `_package_id`) and every type mismatch is an **error**; any other missing field (`pds:...`, `ref_lid_*`) is a **warning**. Fields defined on fewer indices than the threshold are node-specific and not reported as missing. The audit is read-only.

#### Usage

Credentials come from the shell environment, as for the other audits.

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"

# Every node's registry index
python scripts/audit_index_mappings.py --output-dir ./audit_mappings/

# Include the registry-refs indices; exit code 2 when an error-level discrepancy is found
python scripts/audit_index_mappings.py --output-dir ./audit_mappings/ --include-refs --check
```

The ATM products index is `temp-atm-registry` behind the alias `atm-registry`, while its refs index is `atm-registry-refs`. Node discovery returns the concrete name `temp-atm`, and the refs index is looked up under the tenant name `atm`.

#### Output

| File | Content |
|---|---|
| `mapping_summary.md` | The report (also printed): per-index counts, fields missing from some indices, one row per field with conflicting types showing which nodes use which type, missing indices |
| `mapping_discrepancies.csv` | One row per discrepancy: group, index, field, kind, severity, expected and actual type, how many indices have the expected type, and for a type mismatch the nodes that use each type (`types_by_index`) |
| `mapping_matrix.csv` | One row per field, one column per index, with the mapped type or `(absent)` |
| `mapping_possibly_stale.csv` | Written only when such indices exist: one row per index that is not named after a tenant node, with its document count, mapped-field count and whether a refs index exists |

#### Possibly stale indices

Only tenant nodes are compared: `atm`, `en`, `geo`, `img`, `naif`, `ppi`, `psa`, `rms`, `sbnpsi` and `sbnumd` (`--known-node`, repeatable, replaces the list). When nodes are discovered, an index named `<prefix>-registry` whose prefix is not one of them (a personal, temporary or test copy) is left out of the comparison and listed under "Possibly stale or test indices" in the report with its document count, mapped-field count and refs-index presence. These are candidates for cleanup: confirm with the owner before deleting, since the audit never deletes anything. `audit_unprocessed_products.py` applies the same rule to discovered nodes and names the skipped indices in its report headline. Nodes named with `--node` are always audited as given.

Exit codes: 0 on success (and, with `--check`, no error-level discrepancy), 1 on an error, 2 when `--check` finds an error-level discrepancy. A mapping type cannot be changed in place, so fixing a type mismatch means reindexing into a corrected index.


### Registry Report Card

Grade every node green, yellow or red from the status reports and the fidelity audits.

**Scripts:** `generate_report_card.py` (reads local files only) and `collect_node_totals.py` (read-only `_count` queries). The rubric and the node list are in `conf/status/report_card.json`.

Each node gets Loading, File paths and Fidelity scores (the node's) and a Registry Health score (EN's). A score is green with no issues, yellow with issues below 5% of the node's items, and red from 5%. The index mapping counts only for the fields the API relies on (`lid`, `lidvid`, `archive_status`, `superseded_by`, `ancestor_refs`): one missing from a node's mapping or mapped with a different type (`text` against `keyword` excepted) is red, and other mapping differences are ignored. The full rubric, the inputs and the refresh commands are in `docs/status/fidelity/README.md`.

```bash
PYTHON="<path-to-python-with-the-registry-client>"
"${PYTHON}" scripts/generate_report_card.py          # writes docs/status/report_card.{html,md,json}
```

`collect_node_totals.py` counts each node's API-visible products, the denominator of the product-based scores, and needs registry credentials like the audits.
