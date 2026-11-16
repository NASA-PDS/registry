# rms node audit, 2026-11-16

## Verdict

Healthy for ancestry. Every API-visible product on the node has current ancestry, and none of its 356 collections is stamped without a link to its bundle. The one error-level problem is an index mapping type that differs from the other nodes.

## What needs to happen

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | Nothing | 0 | 0 | None |
| Registry operations | Nothing in the product data. One legacy field is mapped with a different type from the other nodes (see Index mapping) | 0 | 0 | Align the field type at the next reindex; no urgency |
| Sweepers team | Nothing | 0 | 0 | None |
| Needs a closer look | Nothing | 0 | 0 | None |
| No action | Nothing | 0 | 0 | None |

The audit was run with the collection inventories enabled; with no candidate products, none was read.

## Index mapping

`rms-registry` has 1 error-level problem and 12 warning-level missing fields.

- **Type conflict:** `ops:Provenance/ops:registry_sweepers_provenance_version` is `keyword` on RMS and `integer` on the other 9 tenant indices. This is the legacy provenance version field: the sweepers now select work on a separate field, `ops:Provenance/ops:registry_sweepers_provenance_hotfixed_version`, and clear this one, so the difference has no known effect on current sweeper runs. It is a leftover of the earlier keyword-versus-integer problem. A mapping type cannot be changed in place, so aligning it means reindexing RMS; owner: registry operations, with the index owners.
- **Missing fields (warnings):** 12 `pds:` fields that most nodes map, for example `pds:Array_3D_Image/pds:axes`, `pds:Person/pds:family_name` and `pds:Science_Facets/pds:domain`. A value in these fields is stored but cannot be searched on RMS.

## Reproduce

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
OUTPUT_DIR="./audit_rms/"
source "${ENV_FILE}"
python scripts/audit_unprocessed_products.py --output-dir "${OUTPUT_DIR}" --node rms --check
python scripts/audit_index_mappings.py --output-dir "./audit_mappings/" --include-refs
```

The unprocessed-product audit output (`summary.md`, `metrics.json`, `collections.csv`) is in `../audit-output/rms/`.
