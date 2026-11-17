# ppi node audit, 2026-11-16

## Verdict

Healthy. Every API-visible product on the node has current ancestry, and none of its 1,546 collections is stamped without a link to its bundle. Nothing needs doing.

## What needs to happen

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | Nothing | 0 | 0 | None |
| Registry operations | Nothing | 0 | 0 | None |
| Sweepers team | Nothing | 0 | 0 | None |
| Needs a closer look | Nothing | 0 | 0 | None |
| No action | Nothing | 0 | 0 | None |

The audit was run with the collection inventories enabled; with no candidate products, none was read.

## Index mapping

`ppi-registry` has no error-level problems: no missing core field and no type conflict. It has 2 warning-level missing fields, `geom:SPICE_Kernel_Identification/geom:spice_kernel_file_name` and `pds:Element_Array/pds:value_offset`, which most other nodes map. A value in either field is stored but cannot be searched on PPI. Fixing it means adding the fields to the mapping and rewriting the documents (see NASA-PDS/registry#612); owner: registry operations with the index owners.

<!-- product-samples:start -->
## Example products

No product needs attention.

<!-- product-samples:end -->

## Reproduce

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
OUTPUT_DIR="./audit_ppi/"
source "${ENV_FILE}"
python scripts/audit_unprocessed_products.py --output-dir "${OUTPUT_DIR}" --node ppi --check
```

The unprocessed-product audit output (`summary.md`, `metrics.json`, `collections.csv`) is in `../audit-output/ppi/`.
