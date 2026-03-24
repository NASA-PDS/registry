# PDS Registry Status Reports

This directory contains automatically generated CSV reports that track the status of products in the PDS Registry.

## Metrics Summary

<!-- METRICS_START -->
*Last updated: 2026-03-24 01:30:07 UTC*

### Missing Products by Node

| Node | Latest Bundles | Superseded Bundles | Total Bundles | Latest Collections | Superseded Collections | Total Collections |
|------|---------------:|-------------------:|--------------:|-------------------:|-----------------------:|------------------:|
| KPDS | 1 | 0 | 1 | 3 | 0 | 3 |
| PDS_ATM | 22 | 4 | 26 | 156 | 59 | 215 |
| PDS_ENG | 2 | 6 | 8 | 18 | 75 | 93 |
| PDS_GEO | 27 | 9 | 36 | 306 | 224 | 530 |
| PDS_IMG | 40 | 27 | 67 | 1642 | 205 | 1847 |
| PDS_PPI | 38 | 174 | 212 | 222 | 1207 | 1429 |
| PDS_SBN | 23 | 21 | 44 | 116 | 63 | 179 |
| **Total** | **153** | **241** | **394** | **2463** | **1833** | **4296** |

### Staged Products by Node

| Node | Bundles | Collections |
|------|--------:|------------:|
| PDS_ATM | 3 | 30 |
| PDS_GEO | 0 | 16 |
| PDS_IMG | 0 | 64 |
| PDS_NAIF | 0 | 183 |
| PDS_PPI | 1 | 4 |
| PDS_RMS | 0 | 1 |
| PDS_SBN | 25 | 136 |
| PSA | 902 | 4171 |
| **Total** | **931** | **4605** |

<!-- METRICS_END -->

## Reports

### Missing Products

These reports identify products that are marked as missing in the registry (`found_in_registry: false`).
Version status is determined by comparing version numbers numerically within each LID; the `superseded` column indicates whether a LIDVID is the latest version (`false`) or an older version that has been superseded by a newer one (`true`).

| File | Description |
|------|-------------|
| `missing_bundles_in_registry.csv` | All missing Product_Bundle records, with a `superseded` column |
| `missing_collections_in_registry.csv` | All missing Product_Collection records, with a `superseded` column |

**CSV Format:** `NODE_ID, LIDVID, PRODUCT_CLASS, SUPERSEDED`

**Example:**
```
"PDS_PPI","urn:nasa:pds:maven.rose.raw::1.21","Product_Bundle","false"
"PDS_ENG","urn:nasa:pds:context::1.2","Product_Bundle","true"
```

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

These reports identify products that have an archive status of "staged" in the registry:

- **`staged_bundles_in_registry.csv`** - Staged Product_Bundle records
- **`staged_collections_in_registry.csv`** - Staged Product_Collection records

**CSV Format:** `NODE_ID, LIDVID, PRODUCT_CLASS, HARVEST_DATE_TIME`

**Example:**
```
"PDS_SBN","urn:nasa:pds:bopps2014::1.0","Product_Bundle","2025-07-22T22:48:09.852492089Z"
"PDS_ATM","urn:nasa:pds:insight_rad::1.0","Product_Bundle","2024-03-15T10:30:00Z"
```

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
            missing_collections_in_registry.csv \
            staged_bundles_in_registry.csv \
            staged_collections_in_registry.csv \
            counts_history.csv; do
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
        node, lidvid, product_class, superseded = row
        print(f"{node}: {lidvid} (superseded={superseded})")

# Or use pandas for analysis
import pandas as pd
df = pd.read_csv('missing_bundles_in_registry.csv', names=['node', 'lidvid', 'product_class', 'superseded'])
# Count only latest (non-superseded) missing bundles per node
print(df[df['superseded'] == 'false'].groupby('node').size())
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
- **SUPERSEDED** - (`true`/`false`) Whether this LIDVID has been superseded by a higher-versioned LIDVID for the same LID. `false` means it is the latest version; `true` means a newer version exists. Present only in missing-product CSVs.
- **HARVEST_DATE_TIME** - Timestamp when the product was harvested into the registry (ISO 8601 format, UTC). Present only in staged-product CSVs.

## Questions or Issues

For questions about:
- **Report contents or data**: Contact the PDS Engineering Node
- **Script errors or enhancements**: Create an issue at [NASA-PDS/registry](https://github.com/NASA-PDS/registry/issues)
- **Registry access**: Contact PDS operations team

## Related Documentation

- [Registry User Documentation](https://nasa-pds.github.io/registry/)
- [Script Documentation](../../scripts/README.md)
- [Main Repository README](../../README.md)
