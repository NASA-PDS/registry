# PDS Registry Status Reports

This directory contains automatically generated CSV reports that track the status of products in the PDS Registry.

## Metrics Summary

<!-- METRICS_START -->
<<<<<<< Updated upstream
*Last updated: 2025-11-21 22:50:21 UTC*

### Missing Products by Node

| Node | Bundles | Collections |
|------|---------|-------------|
| KPDS | 1 | 2 |
| PDS_ATM | 22 | 93 |
| PDS_ENG | 7 | 7 |
| PDS_GEO | 36 | 252 |
| PDS_IMG | 60 | 876 |
| PDS_PPI | 199 | 653 |
| PDS_SBN | 72 | 117 |
| **Total** | **397** | **2000** |
=======
*Last updated: 2026-04-02 21:33:36 UTC*

### Missing Products by Node

| Node | Latest Bundles | Superseded Bundles | Total Bundles | Latest Collections | Superseded Collections | Total Collections |
|------|---------------:|-------------------:|--------------:|-------------------:|-----------------------:|------------------:|
| KPDS | 1 | 0 | 1 | 3 | 0 | 3 |
| PDS_ATM | 18 | 8 | 26 | 138 | 77 | 215 |
| PDS_ENG | 2 | 6 | 8 | 5 | 88 | 93 |
| PDS_GEO | 11 | 24 | 35 | 166 | 364 | 530 |
| PDS_IMG | 37 | 32 | 69 | 1585 | 272 | 1857 |
| PDS_PPI | 14 | 198 | 212 | 84 | 1345 | 1429 |
| PDS_SBN | 15 | 29 | 44 | 86 | 93 | 179 |
| **Total** | **98** | **297** | **395** | **2067** | **2239** | **4306** |
>>>>>>> Stashed changes

### Staged Products by Node

| Node | Bundles | Collections |
<<<<<<< Updated upstream
|------|---------|-------------|
| PDS_ATM | 3 | 6 |
| PDS_GEO | 0 | 11 |
| PDS_IMG | 13 | 38 |
| PDS_NAIF | 0 | 63 |
| PDS_PPI | 8 | 362 |
| PDS_SBN | 35 | 57 |
| PSA | 902 | 1463 |
| **Total** | **961** | **2000** |
=======
|------|--------:|------------:|
| PDS_ATM | 3 | 30 |
| PDS_GEO | 0 | 7 |
| PDS_IMG | 0 | 64 |
| PDS_PPI | 1 | 4 |
| PDS_RMS | 0 | 1 |
| PDS_SBN | 25 | 137 |
| PSA | 902 | 4171 |
| **Total** | **931** | **4414** |
>>>>>>> Stashed changes

<!-- METRICS_END -->

## Reports

### Missing Products

These reports identify products that are marked as missing in the registry (`found_in_registry: false`):

- **`missing_bundles_in_registry.csv`** - Missing Product_Bundle records
- **`missing_collections_in_registry.csv`** - Missing Product_Collection records

**CSV Format:** `NODE_ID, LIDVID, PRODUCT_CLASS`

**Example:**
```
"PDS_PPI","urn:nasa:pds:maven.rose.raw::1.21","Product_Bundle"
"PDS_ENG","urn:nasa:pds:context::1.2","Product_Bundle"
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
