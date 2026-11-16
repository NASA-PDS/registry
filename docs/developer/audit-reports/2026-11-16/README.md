# Registry data fidelity audits, 2026-11-16

Output of the audits described in [the playbook](../../audit-registry-data-fidelity-playbook.md), run read-only against the production registry on 2026-11-16. They are a snapshot: re-run the scripts for current numbers.

## How to read these reports

Every product that the public API could show but that has no ancestry (it is missing from its collection's and bundle's `/members`) is one of two kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection a report names for it is a best guess from its identifier; the product may belong to a collection version that is not loaded.
- **Not processed**: the registry's refs list the product, so its collection is confirmed, but the sweepers never gave it ancestry.

and each one has an owner, the party that can fix it:

| Owner | What they do |
|---|---|
| **Node** | Fix the node's data: load a collection or a product version, correct an inventory, or remove a product |
| **Registry operations** | Re-harvest the collection, then run the sweepers. No change to the node's data |
| **Sweepers team** | Fix a software gap: the sweepers skipped a product that looks right, or do not follow an inventory that lists products without a version |
| **Needs a closer look** | The audit could not check the collection's inventory, so the cause is unknown |

## Roll-up by node

Products that need attention, by owner. "Bundles missing members" counts collections that are marked processed but have no link to their bundle, so the bundle does not list them (fixed by registry operations).

| Node | Products examined | Node | Registry operations | Sweepers team | Needs a closer look | Bundles missing members | Waiting (no action) |
|---|--:|--:|--:|--:|--:|--:|--:|
| atm (earlier run, see below) | 2,784,370 | 2,782,642 | 0 | 0 | 3 | 0 | 1,725 |
| en | 793 | 703 | 0 | 0 | 2 | 0 | 88 |
| geo | 1,373 | 1,322 | 2 | 49 | 0 | 2 | 0 |
| img | 36,839 | 516 | 36,323 | 0 | 0 | 6 | 0 |
| naif | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| ppi | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rms | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| sbnpsi | 98 | 2 | 67 | 0 | 0 | 0 | 29 |
| sbnumd | 25 | 1 | 24 | 0 | 0 | 58 | 0 |
| **Total** | **2,823,500** | **2,785,186** | **36,418** | **49** | **5** | **66** | **1,842** |

PSA is not in the table yet. `scripts/audit_rollup.py` produces this table from the `metrics.json` files.

The ATM row comes from the ATM audit run earlier on 2026-11-16, before the owner-first reporting existed: its counts are mapped to owners by rule, and its 3 `refs_missing` products are shown as needing a closer look because that run did not record whether the inventory was used for them. A final ATM run (and a PSA run) with the same code as the other nodes replaces this row and adds PSA when they finish.

## Per node

| Node | Report | Audit output |
|---|---|---|
| atm | [`atm-unprocessed-products/summary.md`](atm-unprocessed-products/summary.md) (earlier run) | [`atm-unprocessed-products/`](atm-unprocessed-products) |
| en | [`nodes/en.md`](nodes/en.md) | [`audit-output/en/`](audit-output/en) |
| geo | [`nodes/geo.md`](nodes/geo.md) | [`audit-output/geo/`](audit-output/geo) |
| img | [`nodes/img.md`](nodes/img.md) | [`audit-output/img/`](audit-output/img) |
| naif | [`nodes/naif.md`](nodes/naif.md) | [`audit-output/naif/`](audit-output/naif) |
| ppi | [`nodes/ppi.md`](nodes/ppi.md) | [`audit-output/ppi/`](audit-output/ppi) |
| rms | [`nodes/rms.md`](nodes/rms.md) | [`audit-output/rms/`](audit-output/rms) |
| sbnpsi | [`nodes/sbnpsi.md`](nodes/sbnpsi.md) | [`audit-output/sbnpsi/`](audit-output/sbnpsi) |
| sbnumd | [`nodes/sbnumd.md`](nodes/sbnumd.md) | [`audit-output/sbnumd/`](audit-output/sbnumd) |

Each `nodes/<node>.md` is a plain-language report: a verdict, a "What needs to happen" table by owner, the evidence checked by hand, and a short index-mapping section. Each `audit-output/<node>/` holds the script output: `summary.md` (opens with the same owner table), `metrics.json` (totals, counts per rule and per owner, usable as the `--baseline` of a later `--check` run), `collections.csv` and `anomalous_collections.txt`. The per-product CSVs (`unprocessed_products.csv.gz`, up to about 50 MB for ATM) are not committed; regenerate them with the commands below.

## ATM unprocessed products (`atm-unprocessed-products/`)

`scripts/audit_unprocessed_products.py` on the ATM node with `--check`, ancestry version 7. Tracking issue: NASA-PDS/registry#610.

| File | Content |
|---|---|
| `summary.md` | The report: anomalies by rule, anomalous collections, expected-pending counts, orphans, breakdowns, and the regression check result |
| `metrics.json` | Totals, anomalous count per rule, and the anomalous collection lists |
| `collections.csv` | One row per collection with state, bundles and refs coverage |
| `anomalous_collections.txt` | Collections to look at or re-harvest, for `audit_collection.py --from-file` |
| `history.csv` | The run's row for `--history-csv` trend files |

Result: 2,784,370 candidates, 2,782,645 anomalous (mostly `inventory_version_mismatch` and `not_in_collection_inventory`, both the node's), no collection stamped with empty refs that has a bundle. The regression check fails on `no_anomalous_products` (no baseline was given) and on `superseded_by_mapped` (NASA-PDS/registry#611).

## Index mappings (`index-mappings/`)

`scripts/audit_index_mappings.py --include-refs` with node discovery. Tracking issue: NASA-PDS/registry#612.

| File | Content |
|---|---|
| `mapping_summary.md` | The report: per-index counts, fields missing from some indices, one row per field with conflicting types showing which nodes use which type, possibly stale indices |
| `mapping_discrepancies.csv` | One row per discrepancy |
| `mapping_matrix.csv` | One row per field, one column per index, with the mapped type |
| `mapping_possibly_stale.csv` | Index prefixes that are not tenant nodes, left out of the comparison |

Result: 20 indices compared (10 tenant registry indices and their 10 refs indices), 28 error-level and 154 warning-level discrepancies. The error-level ones are `ops:Provenance/ops:superseded_by` and `vid`, missing from the ATM index, plus 25 fields with conflicting types. One index prefix that is not a tenant node was left out of the comparison and listed as possibly stale.

## Regenerating

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
NODE="<node-name>"
OUTPUT_DIR="./audit_${NODE}/"
source "${ENV_FILE}"
python scripts/audit_unprocessed_products.py --output-dir "${OUTPUT_DIR}" --node "${NODE}" --gzip --check
python scripts/audit_index_mappings.py --output-dir "./audit_mappings/" --include-refs
AUDITS_DIR="<directory containing one sub-directory per node>"
python scripts/audit_rollup.py --audits-dir "${AUDITS_DIR}"
```

Without `--no-inventory` the audit reads each collection's inventory where it needs it, which can be slow for large collections; `--inventory-cache-dir` keeps the downloads.
