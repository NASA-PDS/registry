# Registry data fidelity audits, 2026-11-16

Output of the audits described in [the playbook](../../audit-registry-data-fidelity-playbook.md), run read-only against the production registry on 2026-11-16. They are a snapshot: re-run the scripts for current numbers.

## How to read these reports

Every product that the public API could show but that has no ancestry (it is missing from its collection's and bundle's `/members`) is one of two kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection a report names for it is a best guess from its identifier; the product may belong to a collection version that is not loaded.
- **Not processed**: the registry's refs list the product, so its collection is confirmed, but the sweepers never gave it ancestry.

and each one has an owner, the party that can fix it:

| Owner | What they do |
|---|---|
| **Node** | Fix the node's data: load a collection or a product version, correct an inventory, or remove a product. Also re-harvest the collection when its refs are stale or missing, or the sweepers never reached the products |
| **EN** | Run the sweepers after the node's re-harvest, and fix the registry itself (index mappings). No product is waiting on EN alone in this run |
| **Sweepers team** | Fix a software gap: the sweepers skipped a product that looks right, or do not follow an inventory that lists products without a version |
| **Needs a closer look** | The audit could not check the collection's inventory, so the cause is unknown |

## Roll-up by node

Products that need attention, by owner. "Bundles missing members" counts collections that are marked processed but have no link to their bundle, so the bundle does not list them (the node re-harvests the collection, then EN runs the sweepers).

| Node | Products examined | Needs attention: Node | Needs attention: EN | Needs attention: Sweepers team | Needs attention: Needs a closer look | Collections whose bundle shows no members | Waiting (no action) |
|---|--:|--:|--:|--:|--:|--:|--:|
| atm | 2,784,370 | 2,782,642 | 0 | 1 | 2 | 0 | 1,725 |
| en | 793 | 703 | 0 | 0 | 2 | 0 | 88 |
| geo | 1,373 | 1,324 | 0 | 49 | 0 | 2 | 0 |
| img | 36,839 | 36,839 | 0 | 0 | 0 | 6 | 0 |
| naif | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| ppi | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| psa | 1,561,792 | 262,042 | 0 | 0 | 57,525 | 0 | 1,242,225 |
| rms | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| sbnpsi | 98 | 69 | 0 | 0 | 0 | 0 | 29 |
| sbnumd | 25 | 25 | 0 | 0 | 0 | 58 | 0 |
| **Total** | **4,385,292** | **3,083,646** | **0** | **50** | **57,529** | **66** | **1,244,067** |

`scripts/audit_rollup.py` produces this table from the `metrics.json` files. "Needs a closer look" are products whose collection inventory could not be read (ATM: the `pds-ama` sample, whose files were loaded from a local path; PSA: see its report).

## Where the numbers are

Across the ten nodes, 4,385,292 API-visible products were examined: **3,141,225 need attention** (they have no ancestry and something has to be done) and 1,244,067 are only waiting (loaded within the last week). The products are not corrupted: each one is missing its link to a collection or its processing by the sweepers.

| What | Where |
|---|---|
| Totals by node and owner | The roll-up table above, and `scripts/audit_rollup.py` |
| Counts per rule and per owner, per node | `audit-output/<node>/metrics.json` (`rules` and `owners`) |
| Counts per collection | `audit-output/<node>/collections.csv` (`anomalous_product_count`) |
| **Example products of every problem group** | `audit-output/<node>/product_samples.csv`: for each group (one rule in one collection) the group's full size (`products_in_group`) and up to 10 products, with the owner and the reason |
| Every affected product | `unprocessed_products.csv.gz` in each audit run's output directory. Not committed (up to about 50 MB for ATM); regenerate with the commands below, or ask for the files |

`product_samples.csv` is written by `scripts/audit_product_samples.py` from the per-product CSVs; for every node the group sizes in it add up to that node's anomalous total.

## Per node

| Node | Report | Audit output |
|---|---|---|
| atm | [`nodes/atm.md`](nodes/atm.md) | [`audit-output/atm/`](audit-output/atm) |
| en | [`nodes/en.md`](nodes/en.md) | [`audit-output/en/`](audit-output/en) |
| geo | [`nodes/geo.md`](nodes/geo.md) | [`audit-output/geo/`](audit-output/geo) |
| img | [`nodes/img.md`](nodes/img.md) | [`audit-output/img/`](audit-output/img) |
| naif | [`nodes/naif.md`](nodes/naif.md) | [`audit-output/naif/`](audit-output/naif) |
| ppi | [`nodes/ppi.md`](nodes/ppi.md) | [`audit-output/ppi/`](audit-output/ppi) |
| psa | [`nodes/psa.md`](nodes/psa.md) | [`audit-output/psa/`](audit-output/psa) |
| rms | [`nodes/rms.md`](nodes/rms.md) | [`audit-output/rms/`](audit-output/rms) |
| sbnpsi | [`nodes/sbnpsi.md`](nodes/sbnpsi.md) | [`audit-output/sbnpsi/`](audit-output/sbnpsi) |
| sbnumd | [`nodes/sbnumd.md`](nodes/sbnumd.md) | [`audit-output/sbnumd/`](audit-output/sbnumd) |

Each `nodes/<node>.md` is a plain-language report: a verdict, a "What needs to happen" table by owner, the evidence checked by hand, and a short index-mapping section. Each `audit-output/<node>/` holds the script output: `summary.md` (opens with the same owner table), `metrics.json` (totals, counts per rule and per owner, usable as the `--baseline` of a later `--check` run), `collections.csv`, `anomalous_collections.txt` and `product_samples.csv` (example products of every problem group). The per-product CSVs (`unprocessed_products.csv.gz`, up to about 50 MB for ATM and 18 MB for PSA) are not committed; regenerate them with the commands below.

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
python scripts/audit_product_samples.py --audits-dir "${AUDITS_DIR}" --output-dir "${AUDITS_DIR}" --per-group 10
```

Without `--no-inventory` the audit reads each collection's inventory where it needs it, which can be slow for large collections; `--inventory-cache-dir` keeps the downloads.
