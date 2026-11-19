# PDS Registry Status Reports

This directory contains automatically generated CSV reports that track the status of products in the PDS Registry.

## Report Card

[Registry Report Card](report_card.md) ([web page](https://nasa-pds.github.io/registry/status/report_card.html)): one row per node, graded green, yellow or red on loading, invalid file paths and data fidelity, with Index Health (EN's) beside them. Each score links to the details. How the scores work and how to refresh the inputs: [fidelity/README.md](fidelity/README.md).

## Metrics Summary

<!-- METRICS_START -->
*Last updated: 2026-11-19 04:06:04 UTC*

### Missing Products by Node

| Node | Latest Bundles | Superseded Bundles | Total Bundles | Latest Collections | Superseded Collections | Total Collections |
|------|---------------:|-------------------:|--------------:|-------------------:|-----------------------:|------------------:|
| KPDS | 1 | 0 | 1 | 3 | 0 | 3 |
| PDS_ATM | 11 | 9 | 20 | 37 | 83 | 120 |
| PDS_ENG | 1 | 6 | 7 | 5 | 89 | 94 |
| PDS_GEO | 0 | 24 | 24 | 0 | 350 | 350 |
| PDS_IMG | 48 | 49 | 97 | 1684 | 362 | 2046 |
| PDS_PPI | 3 | 198 | 201 | 9 | 1312 | 1321 |
| PDS_SBN | 1 | 24 | 25 | 7 | 86 | 93 |
| **Total** | **65** | **310** | **375** | **1745** | **2282** | **4027** |

### Staged Products by Node

| Node | Bundles | Collections |
|------|--------:|------------:|
| PDS_ATM | 3 | 29 |
| PDS_GEO | 0 | 7 |
| PDS_IMG | 0 | 61 |
| PDS_PPI | 3 | 46 |
| PDS_SBN | 22 | 102 |
| PSA | 902 | 4171 |
| **Total** | **930** | **4416** |

### Products with Invalid file_ref by Node

Products with a Label or Data `file_ref` that does not start with `https://`. Only `https://` is valid because the archive is served through CloudFront.

| Node | Bundles | Collections | Other Products |
|------|--------:|------------:|---------------:|
| PDS_ATM | 1 | 3 | 7 |
| PDS_ENG | 0 | 0 | 34 |
| PDS_GEO | 0 | 0 | 2 |
| PDS_IMG | 0 | 27 | 61937 |
| **Total** | **1** | **30** | **61980** |

### Loading Progress

[View Burnup Chart](burnup_chart.html) — cumulative products loaded over time vs. target

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
| **Invalid file_ref** | In the new registry, but a label or data `file_ref` does not start with `https://` |

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

### Invalid file_ref

Products in the new registry whose label (`ops:Label_File_Info/ops:file_ref`) or data file
(`ops:Data_File_Info/ops:file_ref`) reference does not start with `https://`, regardless of archive status.

Only `https://` references are valid, because the archive is served through CloudFront. Every other value is
reported: `s3://` URLs, local paths, relative paths and any other scheme. Empty values and the placeholder `null`
are ignored. Queried with pagination so counts are not capped at 10,000.

- **[`bad_file_ref_bundles_in_registry.csv`](bad_file_ref_bundles_in_registry.csv)** — One row per invalid value on a Product_Bundle
- **[`bad_file_ref_collections_in_registry.csv`](bad_file_ref_collections_in_registry.csv)** — One row per invalid value on a Product_Collection
- **[`bad_file_ref_products_in_registry.csv`](bad_file_ref_products_in_registry.csv)** — All other product classes, grouped (see below)

**Columns (bundles and collections):** `node, lidvid, product_class, archive_status, file_ref_field, file_ref`

`file_ref_field` is `Label_File_Info` or `Data_File_Info`.

**Columns (other products):** `node, bundle_lid, collection_lid, archive_status, products, values, value_kinds, file_ref_fields, example_lidvid, example_file_ref`

There are too many other products to list one by one, so each row summarizes one node, bundle, collection and
archive status. `products` is the number of distinct products affected, `values` the number of invalid values,
`value_kinds` the kinds of value found (`s3://`, `http://`, `local path`, `relative path`, ...), and
`file_ref_fields` which fields are affected. `example_lidvid` and `example_file_ref` give one affected product.
Rows are ordered by `products`, largest first.

The directory part of an invalid value is a path on the machine the product was harvested from, so every
`file_ref` in these reports is masked to its scheme and file name (for example `.../label.xml` or
`s3://.../label.xml`).

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
- **Loaded products** and **invalid `file_ref` products** are queried from the `/*-registry/_search` endpoint and paginated

Both queries return up to 2000 results per product type.

## Field Descriptions

- **NODE_ID** - The PDS node responsible for the product (e.g., PDS_SBN, PDS_ENG, PDS_GEO)
- **LIDVID** - Logical Identifier with Version ID in the format `urn:nasa:pds:bundle_name::version`
- **PRODUCT_CLASS** - Type of product (Product_Bundle or Product_Collection)
- **HARVEST_DATE_TIME** - Timestamp when the product was harvested into the registry (ISO 8601 format, UTC)
- **ARCHIVE_STATUS** - The product's `ops:Tracking_Meta/ops:archive_status` (e.g., `staged`, `archived`)
- **FILE_REF** - A label or data file reference, masked to its scheme and file name; valid only if it started with `https://`

## Questions or Issues

For questions about:
- **Report contents or data**: Contact the PDS Engineering Node
- **Script errors or enhancements**: Create an issue at [NASA-PDS/registry](https://github.com/NASA-PDS/registry/issues)
- **Registry access**: Contact PDS operations team

## Related Documentation

- [Registry User Documentation](https://nasa-pds.github.io/registry/)
- [Script Documentation](../../scripts/README.md)
- [Main Repository README](../../README.md)
