# Fidelity inputs and the report card

`report_card.html` and `report_card.md` in the parent directory grade every node. This directory holds the latest
fidelity audit output the card reads. The dated audit reports stay under `docs/developer/audit-reports/`.

## How a node is graded

| Score | Owner | Counted as an issue | Out of |
|---|---|---|---|
| Loading | Node | Current bundles and collections not yet in the registry | All current bundles and collections |
| File paths | Node | Products, collections and bundles with an invalid `file_ref` | The node's API-visible products |
| Fidelity | Node | API-visible products without ancestry that the node must fix, or that need a closer look | The node's API-visible products |
| Registry Health | EN | Products without ancestry that EN or the sweepers team fix; collections stamped without a link to their bundle; index mapping errors | Products, collections; mapping is graded by kind |

- **Green:** no issues. **Yellow:** issues below 5% of the items. **Red:** 5% or more.
- Registry Health grades a mapping error on a core or `ops:` field red, and a type conflict on any other field yellow. Its worst sub-score is its grade.
- A node's status is the worst of Loading, File paths and Fidelity. Registry Health is shown beside it, not folded in.
- Products still within the grace period ("waiting") are not issues.
- Data older than 14 days is shown as stale; a stale green is no longer green.
- The limit (5%), the stale limit and the node list are in `conf/status/report_card.json`.
- `sbnpsi` and `sbnumd` share one status node, `PDS_SBN`, in the status reports, so their Loading and File paths scores count both.

## Files

| Path | Written by |
|---|---|
| `<node>/metrics.json`, `<node>/summary.md` | `audit_unprocessed_products.py --node <node> --output-dir docs/status/fidelity/<node>` |
| `index-mappings/` | `audit_index_mappings.py --output-dir docs/status/fidelity/index-mappings` |
| `node_totals.json` | `collect_node_totals.py --output docs/status/fidelity/node_totals.json` |

## Refresh

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
PYTHON="<path-to-python-with-the-registry-client>"
FIDELITY_DIR="docs/status/fidelity"
source "${ENV_FILE}"

for NODE in atm en geo img naif ppi psa rms sbnpsi sbnumd; do
  "${PYTHON}" scripts/audit_unprocessed_products.py --node "${NODE}" --output-dir "${FIDELITY_DIR}/${NODE}"
done
"${PYTHON}" scripts/audit_index_mappings.py --output-dir "${FIDELITY_DIR}/index-mappings"
"${PYTHON}" scripts/collect_node_totals.py --output "${FIDELITY_DIR}/node_totals.json"
"${PYTHON}" scripts/generate_report_card.py
```
