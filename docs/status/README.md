# PDS Registry Status Reports

This directory contains automatically generated CSV reports that track the status of products in the PDS Registry.

## Metrics Summary

<!-- METRICS_START -->
*Last updated: 2026-05-13 20:00:31 UTC*

### Missing Products by Node

| Node | Latest Bundles | Superseded Bundles | Total Bundles | Latest Collections | Superseded Collections | Total Collections |
|------|---------------:|-------------------:|--------------:|-------------------:|-----------------------:|------------------:|
| KPDS | 1 | 0 | 1 | 3 | 0 | 3 |
| PDS_ATM | 18 | 8 | 26 | 138 | 81 | 219 |
| PDS_ENG | 2 | 6 | 8 | 5 | 88 | 93 |
| PDS_GEO | 11 | 24 | 35 | 166 | 364 | 530 |
| PDS_IMG | 36 | 35 | 71 | 1592 | 294 | 1886 |
| PDS_PPI | 14 | 199 | 213 | 84 | 1347 | 1431 |
| PDS_RMS | 8 | 0 | 8 | 23 | 0 | 23 |
| PDS_SBN | 16 | 30 | 46 | 89 | 93 | 182 |
| **Total** | **106** | **302** | **408** | **2100** | **2267** | **4367** |

### Staged Products by Node

| Node | Bundles | Collections |
|------|--------:|------------:|
| PDS_ATM | 3 | 30 |
| PDS_GEO | 0 | 7 |
| PDS_IMG | 0 | 64 |
| PDS_PPI | 2 | 30 |
| PDS_RMS | 0 | 1 |
| PDS_SBN | 26 | 137 |
| PSA | 902 | 4171 |
| **Total** | **933** | **4440** |

### Loading Progress

[View Burnup Chart](burnup_chart.html) — cumulative products loaded over time vs. target

<!-- METRICS_END -->

## Reports

### Missing Products

These reports identify products that are in the legacy Solr registry but have **not yet been loaded** into the new OpenSearch registry (`found_in_registry: false` in `en-legacy-registry`).
Three variants are generated per product type by comparing version numbers numerically within each LID:

| File | Description |
|------|-------------|
| `missing_bundles_in_registry.csv` | All missing Product_Bundle records (all versions) |
| `missing_bundles_latest_in_registry.csv` | Only the highest-versioned missing bundle per LID |
| `missing_bundles_superseded_in_registry.csv` | Older versions of missing bundles (superseded by a newer version) |
| `missing_collections_in_registry.csv` | All missing Product_Collection records (all versions) |
| `missing_collections_latest_in_registry.csv` | Only the highest-versioned missing collection per LID |
| `missing_collections_superseded_in_registry.csv` | Older versions of missing collections (superseded by a newer version) |

**CSV Format:** `NODE_ID, LIDVID, PRODUCT_CLASS, SUPERSEDED`

**Example:**
```
"PDS_PPI","urn:nasa:pds:maven.rose.raw::1.21","Product_Bundle","false"
"PDS_ENG","urn:nasa:pds:context::1.2","Product_Bundle","true"
```

### Loaded Products

These reports identify all products currently present in the new OpenSearch registry, regardless of `archive_status`.

- **`loaded_bundles_in_registry.csv`** - All Product_Bundle records in new OpenSearch
- **`loaded_collections_in_registry.csv`** - All Product_Collection records in new OpenSearch

**Important:** The loaded population is larger than the legacy Solr population because the new registry also contains products that were directly harvested (e.g., PSA/ESA products) and were never in the legacy Solr. See [How Numbers Are Calculated](#how-numbers-are-calculated) for details.

**CSV Format:** `NODE_ID, LIDVID, PRODUCT_CLASS, HARVEST_DATE_TIME`

### Historical Counts (Burndown Tracking)

**`counts_history.csv`** — one row is appended per run; the file is **never overwritten** so data accumulates over time. Use this to plot a burndown of missing/staged products.

**CSV Format (header included):**
```
date,
missing_bundles_total,missing_bundles_latest,missing_bundles_superseded,
missing_collections_total,missing_collections_latest,missing_collections_superseded,
staged_bundles_total,staged_collections_total
```

**Example:**
```
date,missing_bundles_total,missing_bundles_latest,missing_bundles_superseded,missing_collections_total,missing_collections_latest,missing_collections_superseded,staged_bundles_total,staged_collections_total
2026-03-20,386,250,136,4233,2100,2133,942,4877
2026-03-21,380,245,135,4190,2080,2110,938,4850
```

**Analyzing with Python/pandas:**
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('counts_history.csv', parse_dates=['date'])
df.plot(x='date', y=['missing_bundles_latest', 'missing_collections_latest'], title='Missing Products Burndown')
plt.show()
```

### Staged Products

These reports identify products in the new OpenSearch registry whose `ops:Tracking_Meta/ops:archive_status` is `staged`. This is an **operator concern** — the products are loaded but in the wrong state and need to be transitioned to `archived`.

- **`staged_bundles_in_registry.csv`** - Staged Product_Bundle records
- **`staged_collections_in_registry.csv`** - Staged Product_Collection records

**CSV Format:** `NODE_ID, LIDVID, PRODUCT_CLASS, HARVEST_DATE_TIME`

**Example:**
```
"PDS_SBN","urn:nasa:pds:bopps2014::1.0","Product_Bundle","2025-07-22T22:48:09.852492089Z"
"PDS_ATM","urn:nasa:pds:insight_rad::1.0","Product_Bundle","2024-03-15T10:30:00Z"
```

### Burnup Charts

**`burnup_chart.html`** — interactive HTML page showing cumulative loading progress over time vs. targets. Includes overall and per-node breakdowns in both "all versions" and "latest versions only" views. Date range is filterable; defaults to the last 12 months.

Supporting CSVs (used to generate the chart):

| File | Description |
|------|-------------|
| `burnup_history.csv` | Overall cumulative loaded counts by date (all versions) |
| `burnup_by_node.csv` | Per-node cumulative loaded counts by date (all versions) |
| `burnup_history_latest.csv` | Overall cumulative loaded counts by date (latest version per LID only) |
| `burnup_by_node_latest.csv` | Per-node cumulative loaded counts by date (latest version per LID only) |

## How to Use These Files

### Viewing in GitHub

1. Navigate to this directory in GitHub: `docs/status/`
2. Click on any CSV file to view it
3. GitHub will render the CSV as a table for easy viewing

### Downloading Files

**Option 1: Download individual file from GitHub**
1. Click on the CSV file in GitHub
2. Click the "Raw" button
3. Right-click and select "Save As..."

**Option 2: Download via command line**
```bash
# Download a specific report
curl -O https://raw.githubusercontent.com/NASA-PDS/registry/main/docs/status/missing_bundles_in_registry.csv

# Download all reports
cd docs/status
for file in missing_bundles_in_registry.csv \
            missing_bundles_latest_in_registry.csv \
            missing_bundles_superseded_in_registry.csv \
            missing_collections_in_registry.csv \
            missing_collections_latest_in_registry.csv \
            missing_collections_superseded_in_registry.csv \
            staged_bundles_in_registry.csv \
            staged_collections_in_registry.csv \
            loaded_bundles_in_registry.csv \
            loaded_collections_in_registry.csv \
            counts_history.csv \
            burnup_history.csv \
            burnup_by_node.csv \
            burnup_history_latest.csv \
            burnup_by_node_latest.csv; do
  curl -O https://raw.githubusercontent.com/NASA-PDS/registry/main/docs/status/$file
done
```

**Option 3: Clone the repository**
```bash
git clone https://github.com/NASA-PDS/registry.git
cd registry/docs/status/
```

### Opening Files

**Spreadsheet Applications:**
- Microsoft Excel: File → Open → Select CSV file
- Google Sheets: File → Import → Upload CSV file
- LibreOffice Calc: File → Open → Select CSV file

**Text Editors:**
- Any text editor (VS Code, Sublime Text, nano, vim, etc.)
- CSV files are plain text and can be opened directly

**Command Line:**
```bash
# View entire file
cat missing_bundles_in_registry.csv

# View first 10 lines
head -10 missing_bundles_in_registry.csv

# Count records
wc -l missing_bundles_in_registry.csv

# Search for specific node
grep "PDS_SBN" staged_bundles_in_registry.csv

# Use column for formatted viewing
column -t -s',' missing_bundles_in_registry.csv | less
```

**Python:**
```python
import csv

# Read CSV file
with open('missing_bundles_in_registry.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        node, lidvid, product_class = row
        print(f"{node}: {lidvid}")

# Or use pandas for analysis
import pandas as pd
df = pd.read_csv('missing_bundles_in_registry.csv', names=['node', 'lidvid', 'product_class'])
print(df.groupby('node').size())
```

## Report Generation

These reports are automatically generated by the `generate_registry_status_reports.py` script located in the `scripts/` directory.

### Run Manually

```bash
# From repository root
./scripts/generate_registry_status_reports.py --no-commit
```

See the [scripts/README.md](../../scripts/README.md) for more details on running the report generator.

## How Numbers Are Calculated

Understanding the numbers requires knowing that there are two distinct data populations:

### Data Populations

**Legacy registry (`en-legacy-registry` OpenSearch index)**
- Populated by the `legacy_registry_sync` sweeper in [registry-sweepers](https://github.com/NASA-PDS/registry-sweepers)
- Sweeper queries `https://pds.nasa.gov/services/search/search?q=*` (the EN-operated legacy Solr) and upserts every document into `en-legacy-registry`
- Each document gets a `found_in_registry` field (`true`/`false`) set by checking whether that LIDVID already exists in the new OpenSearch registry
- **This is the source of truth for "what was in the legacy system"**

**New OpenSearch registry (`*-registry` indices)**
- Target system where legacy products are being migrated to
- Also contains products that were **directly harvested** (e.g., PSA/ESA products, JAXA, KPDS) and were never in the legacy Solr
- Harvest timestamp is stored in `ops:Harvest_Info/ops:harvest_date_time`

### Missing Products

Queried from `/en-legacy-registry/_search` with `product_class` filter.

The script fetches **all** products (both `found_in_registry=true` and `false`) so version ordering can be computed across the full set, then filters to missing-only (`found_in_registry=false`). Version status is then annotated:

- **Latest** (`superseded=false`): the highest-versioned LIDVID for a given LID across all rows
- **Superseded** (`superseded=true`): an older version where a higher version exists anywhere in the dataset

**Important:** These queries are currently limited to `size: 10000`. If the total legacy count for a product type exceeds that, the missing counts may be undercounted. Adding pagination to these queries is a known improvement item.

### Loaded Products

Queried from `/*-registry/_search` (all indices) with `product_class` filter and **no `archive_status` filter** — counts every product regardless of state.

These queries use **`search_after` pagination** (pages of 10,000, sorted by `_id`) to retrieve all records past the 10,000-hit window. The `ops:Harvest_Info/ops:harvest_date_time` field records when each product was harvested into the new registry.

**Note on count discrepancy:** The loaded count will be **larger** than the legacy Solr count because the new registry includes products from sources outside the legacy Solr (e.g., PSA has ~900 bundles and ~4,000 collections directly harvested). Comparing loaded counts directly to Solr `numFound` will show this inflation.

### Staged Products

Queried from `/*-registry/_search` with `archive_status=staged` filter. These are products that are loaded in the new registry but in the wrong state — they need operator action to transition to `archived`. **Staged products are not the same as "loaded" products** for progress-tracking purposes; they are a subset of loaded products.

### Burnup Chart Targets

The burnup chart computes:

```
target = loaded_count_per_node + missing_count_per_node
```

Because `loaded` includes non-Solr products (PSA, etc.) and `missing` is Solr-only, the target is not a pure legacy-Solr count. A future improvement would use `found_in_registry=true` counts from `en-legacy-registry` as the "loaded" numerator and total `en-legacy-registry` count as the target, which would exactly match the legacy Solr population.

### Superseded Flag Calculation

For a given set of LIDVIDs, version strings are compared numerically (e.g., `3.9 < 3.13`) within each LID. The highest-versioned LIDVID for each LID is marked `superseded=false`; all others are `superseded=true`. This comparison is done across the **full** result set (including `found_in_registry=true` records) so that a missing older version is correctly flagged as superseded if a newer version exists anywhere.

## Field Descriptions

- **NODE_ID** - The PDS node responsible for the product (e.g., PDS_SBN, PDS_ENG, PDS_GEO)
- **LIDVID** - Logical Identifier with Version ID in the format `urn:nasa:pds:bundle_name::version`
- **PRODUCT_CLASS** - Type of product (Product_Bundle or Product_Collection)
- **HARVEST_DATE_TIME** - Timestamp when the product was harvested into the new OpenSearch registry (ISO 8601 format, UTC)
- **SUPERSEDED** - `true` if a higher-versioned LIDVID exists for the same LID; `false` if this is the latest version

## Questions or Issues

For questions about:
- **Report contents or data**: Contact the PDS Engineering Node
- **Script errors or enhancements**: Create an issue at [NASA-PDS/registry](https://github.com/NASA-PDS/registry/issues)
- **Registry access**: Contact PDS operations team

## Related Documentation

- [Registry User Documentation](https://nasa-pds.github.io/registry/)
- [Script Documentation](../../scripts/README.md)
- [Main Repository README](../../README.md)
