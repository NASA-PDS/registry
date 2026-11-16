# Registry data fidelity audit reports, 2026-11-16

Output of the audits described in [the playbook](../../audit-registry-data-fidelity-playbook.md), run read-only against the production registry on 2026-11-16. They are a snapshot: re-run the scripts for current numbers.

## ATM unprocessed products (`atm-unprocessed-products/`)

`scripts/audit_unprocessed_products.py` on the ATM node with `--check`, ancestry version 7. Tracking issue: NASA-PDS/registry#610.

| File | Content |
|---|---|
| `summary.md` | The report: anomalies by rule, anomalous collections, expected-pending counts, orphans, breakdowns, and the regression check result |
| `metrics.json` | Totals, anomalous count per rule, and the anomalous collection lists; usable as the `--baseline` of a later `--check` run |
| `collections.csv` | One row per collection with state, bundles and refs coverage |
| `anomalous_collections.txt` | Collections to look at or re-harvest, for `audit_collection.py --from-file` |
| `history.csv` | The run's row for `--history-csv` trend files |

The per-product `unprocessed_products.csv.gz` (about 50 MB, 2.78 million rows) is not committed. Regenerate it with:

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
OUTPUT_DIR="./audit_unprocessed_atm/"
source "${ENV_FILE}"
python scripts/audit_unprocessed_products.py --output-dir "${OUTPUT_DIR}" --node atm --gzip --check
```

Result: 2,784,370 candidates, 2,782,645 anomalous (mostly `inventory_version_mismatch` and `not_in_collection_inventory`), no collection stamped with empty refs that has a bundle. The regression check fails on `no_anomalous_products` (no baseline was given) and on `superseded_by_mapped` (NASA-PDS/registry#611).

## Index mappings (`index-mappings/`)

`scripts/audit_index_mappings.py --include-refs` with node discovery. Tracking issue: NASA-PDS/registry#612.

| File | Content |
|---|---|
| `mapping_summary.md` | The report: per-index counts, fields missing from some indices, type mismatches, possibly stale indices |
| `mapping_discrepancies.csv` | One row per discrepancy |
| `mapping_matrix.csv` | One row per field, one column per index, with the mapped type |
| `mapping_possibly_stale.csv` | Index prefixes that are not tenant nodes, left out of the comparison |

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
OUTPUT_DIR="./audit_mappings/"
source "${ENV_FILE}"
python scripts/audit_index_mappings.py --output-dir "${OUTPUT_DIR}" --include-refs
```

Result: 20 indices compared (10 tenant registry indices and their 10 refs indices), 28 error-level and 154 warning-level discrepancies. The error-level ones are `ops:Provenance/ops:superseded_by` and `vid`, missing from the ATM index, plus the type mismatches. One index prefix that is not a tenant node was left out of the comparison and listed as possibly stale, with 5,239,034 documents and 2 mapped fields.
