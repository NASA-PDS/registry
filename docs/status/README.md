# PDS Registry Status Reports

This directory contains automatically generated CSV reports that track the status of products in the PDS Registry.

## Metrics Summary

<!-- METRICS_START -->
*Last updated: 2026-03-18 19:07:21 UTC*

### Missing Products by Node

| Node | Bundles | Collections |
|------|---------|-------------|
| KPDS | 1 | 2 |
| PDS_ATM | 23 | 97 |
| PDS_ENG | 7 | 43 |
| PDS_GEO | 37 | 258 |
| PDS_IMG | 58 | 799 |
| PDS_PPI | 215 | 703 |
| PDS_SBN | 45 | 98 |
| **Total** | **386** | **2000** |

### Staged Products by Node

| Node | Bundles | Collections |
|------|---------|-------------|
| PDS_ATM | 3 | 9 |
| PDS_GEO | 0 | 1 |
| PDS_IMG | 5 | 38 |
| PDS_NAIF | 0 | 93 |
| PDS_PPI | 6 | 116 |
| PDS_RMS | 0 | 1 |
| PDS_SBN | 26 | 42 |
| PSA | 902 | 1700 |
| **Total** | **942** | **2000** |

<!-- METRICS_END -->

## How These Reports Work

### Source of Truth: PDS Keyword Search

The baseline for what bundles and collections *should* exist in the registry is the
**[PDS Keyword Search](https://pds.nasa.gov/datasearch/keyword-search/)**, which is populated by the
Engineering Node (EN) each time a formal data release occurs. This is the authoritative, agreed-upon
inventory of PDS archive data.

The reports compare that baseline against what is actually available through the
**[PDS Registry API](https://pds.mcp.nasa.gov/api/search/1/products/)** to identify gaps.

A product is considered **missing** when it appears in the PDS Keyword Search (i.e., EN has released it)
but is not yet present in the new OpenSearch-based registry.

### Report Categories

| Category | What it means |
|----------|---------------|
| **Missing** | In PDS Keyword Search (released by EN) but not yet in the new registry |
| **Staged** | In the new registry but `archive_status = staged` — loaded but not yet transitioned to `archived` |
| **Loaded** | All products currently in the new registry, regardless of archive status |

> **Note:** Loaded counts will exceed missing-products baseline counts because the new registry also
> contains products harvested directly from non-EN sources (e.g., PSA/ESA ~900 bundles, ~4,000
> collections). Do not compare loaded totals directly to the Keyword Search totals.

---

## Reports

### Missing Products

Products present in the PDS Keyword Search but **not yet loaded** into the new OpenSearch registry.

- **[`missing_bundles_in_registry.csv`](missing_bundles_in_registry.csv)** — Missing Product_Bundle records
- **[`missing_collections_in_registry.csv`](missing_collections_in_registry.csv)** — Missing Product_Collection records

**Columns:** `node, lidvid, product_class, superseded`

The `superseded` flag is `true` when a newer version of the same LID exists elsewhere in the dataset,
meaning this particular version has been superseded by a later release.

### Staged Products

Products in the new registry with `archive_status = staged` (loaded but not yet archived).
These require operator action to advance their status.

- **[`staged_bundles_in_registry.csv`](staged_bundles_in_registry.csv)** — Staged Product_Bundle records
- **[`staged_collections_in_registry.csv`](staged_collections_in_registry.csv)** — Staged Product_Collection records

**Columns:** `node, lidvid, product_class, harvest_date`

### Loaded Products

All products currently in the new OpenSearch registry, regardless of archive status.
Queried with pagination so counts are not capped at 10,000.

- **[`loaded_bundles_in_registry.csv`](loaded_bundles_in_registry.csv)** — All Product_Bundle records in new OpenSearch
- **[`loaded_collections_in_registry.csv`](loaded_collections_in_registry.csv)** — All Product_Collection records in new OpenSearch

**Columns:** `node, lidvid, product_class, harvest_date`

---

## Frequently Asked Questions

**Q: How can I find the bundles or collections that are applicable to my node?**

Filter the relevant CSV file on the `node` column (e.g., `PDS_SBN`, `PDS_GEO`, `PDS_IMG`).
For example, to find all missing bundles for the Small Bodies Node:

```bash
grep "^PDS_SBN," missing_bundles_in_registry.csv
```

Or in a spreadsheet application, use the filter/sort feature on column A.

---

**Q: A bundle or collection appears in the missing CSVs and `superseded = true`. What does that mean?**

It means a newer version of that LID has already been released. The older version shown is no longer
the latest — however, *both* versions are absent from the registry.
If the newest version also needs to be loaded, verify it appears in the missing CSV as well.

---

**Q: A bundle or collection appears in the loaded CSVs but `superseded = true`. Why is it showing there?**

The newer version was likely never formally released through EN. All version updates of bundles or
collections must be delivered to EN in order to maintain the Keyword Search as the source of truth
for the archive. Submit a ticket to the EN Operations team to request a data release for the new version:

[Submit a Data Release Request](https://github.com/NASA-PDS/operations/issues/new?template=-data-release.yml)

---

**Q: Why are there products in the loaded CSV that have no corresponding entry in the missing CSV?**

The new registry contains products harvested from non-EN sources (e.g., PSA/ESA data). These were
never in the PDS Keyword Search baseline, so they don't appear as "missing" — they simply arrived
through a different pipeline.

---

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
for file in missing_bundles_in_registry.csv missing_collections_in_registry.csv \
            staged_bundles_in_registry.csv staged_collections_in_registry.csv; do
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

## Data Source

- **Missing products** are queried from the `/en-legacy-registry/_search` endpoint
- **Staged products** are queried from the `/*-registry/_search` endpoint (all registry indices)

Both queries return up to 2000 results per product type.

## Field Descriptions

- **NODE_ID** - The PDS node responsible for the product (e.g., PDS_SBN, PDS_ENG, PDS_GEO)
- **LIDVID** - Logical Identifier with Version ID in the format `urn:nasa:pds:bundle_name::version`
- **PRODUCT_CLASS** - Type of product (Product_Bundle or Product_Collection)
- **HARVEST_DATE_TIME** - Timestamp when the product was harvested into the registry (ISO 8601 format, UTC)

## Questions or Issues

For questions about:
- **Report contents or data**: Contact the PDS Engineering Node
- **Script errors or enhancements**: Create an issue at [NASA-PDS/registry](https://github.com/NASA-PDS/registry/issues)
- **Registry access**: Contact PDS operations team

## Related Documentation

- [Registry User Documentation](https://nasa-pds.github.io/registry/)
- [Script Documentation](../../scripts/README.md)
- [Main Repository README](../../README.md)
