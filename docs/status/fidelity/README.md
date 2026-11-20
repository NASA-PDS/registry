# Fidelity inputs and the report card

`report_card.html` and `report_card.md` in the parent directory grade every node. This directory holds the latest
fidelity audit output the card reads. The dated audit reports stay under `docs/developer/audit-reports/`.

## How a node is graded

| Score | Owner | Counted as an issue | Out of |
|---|---|---|---|
| Loading | Node | Current bundles and collections not yet in the registry | All current bundles and collections |
| File paths | Node | Products, collections and bundles with an invalid `file_ref` | The node's API-visible products |
| Fidelity | Node | API-visible products without ancestry that the node must fix (a collection that is not loaded, an inventory that lists another version or omits the product, a collection whose inventory lists the product but whose refs do not), or that need a closer look | The node's API-visible products |
| Index Health | EN | EN's own problems: products without ancestry that the sweepers stamped and never revisited (loaded or overwritten after their collection was stamped, an older stamp, a loaded collection the sweepers never processed); products the sweepers team owns; collections stamped without a link to their bundle; index mapping problems on the fields the API relies on | Products and collections; the mapping check is pass or fail |

- **Green:** no issues. **Yellow:** issues below 5% of the items. **Red:** 5% or more.
- Index Health looks at the index mapping only for the fields the API relies on: `lid`, `lidvid`, `vid`, `ops:Tracking_Meta/ops:archive_status`, `ops:Provenance/ops:superseded_by` and `ops:Provenance/ops:ancestor_refs` (`api_mapping_fields` in the configuration). One of them missing from a node's mapping, or mapped with a type other than the other nodes', makes the mapping check red. `text` against `keyword` counts as the same type. Every other mapping difference, including fields a node has not loaded any data for, is ignored (the full list stays in the index mapping audit). Index Health's grade is its worst sub-score.
- Index Health is marked with an asterisk (*) because its issues are EN's or the sweepers team's, not the node's. EN's problems are collections the sweepers stamped before their products were loaded, products a node overwrote that the sweepers never revisited (EN runs the ancestry orphan repair), collections without a bundle link (EN runs the bundle-link pass), loaded collections the sweepers never processed, and index mappings. Loading, File paths and Fidelity are the node's. A node status marked * also has open Index Health issues, which are not counted in the node status.
- The owner of a product without ancestry is computed from the `rules` counts in `<node>/metrics.json` with the current ownership mapping (`scripts/unprocessed_audit/ownership.py`), not read from the stored `owners`, so every node is scored by the same rules.
- A node's status is the worst of Loading, File paths and Fidelity. Index Health is shown beside it, not folded in.
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

## Automated runs

`.github/workflows/registry-fidelity-audit.yml` runs the refresh above every Monday and on demand (Actions →
Registry Fidelity Audit → Run workflow). It:

1. audits each node with `audit_unprocessed_products.py --check --baseline <last committed metrics.json>`,
   three nodes at a time, reading collection inventories (cached between runs) and appending one row per run to
   `<node>/history.csv`;
2. runs `audit_index_mappings.py --check` and `collect_node_totals.py`;
3. runs `generate_registry_status_reports.py --no-commit`, because the Loading and File paths scores and the
   staleness date come from those reports;
4. rolls the nodes up into `rollup.md`, regenerates the report card, and opens or updates one pull request from
   the `automation/registry-fidelity-audit` branch. Merging it publishes the card and makes these results the
   baseline for the next run.

The run fails, after the pull request is updated, when a node has anomalies that are new since the last
committed run or the mapping audit finds an error-level discrepancy. A node whose audit cannot complete (exit
code 1) keeps its previous files, so its card turns stale rather than wrong. The per-product CSVs and the full
audit output are kept as run artifacts (`audit-output-<node>`) for 30 days; pass one as `--previous-csv` for a
new/resolved/persisting comparison by hand.

Manual runs can be limited to some nodes (`nodes: "atm geo"`), skip the inventories for a fast check, skip the
status reports, or skip the pull request.

### One-time setup

1. **Read-only service user.** Create a registry Cognito user for automation (not a person's account), in a
   group whose identity-pool role can only read: in the OpenSearch Serverless data access policy grant
   `aoss:DescribeCollectionItems` on the registry collection and only `aoss:ReadDocument` and
   `aoss:DescribeIndex` on the registry indices. The audits issue `_search`, `_count` and
   `GET /<index>/_mapping` only, so no write permission is needed. Do not reuse the harvest or sweepers users.
2. **GitHub environment.** Create the `registry-audit` environment (Settings → Environments), limit its
   deployment branches to `develop`, and add:

   | Kind | Name |
   |---|---|
   | Secret | `REQUEST_SIGNER_COGNITO_USER`, `REQUEST_SIGNER_COGNITO_PASSWORD` |
   | Variable | `REQUEST_SIGNER_AWS_REGION`, `REQUEST_SIGNER_AWS_ACCOUNT`, `REQUEST_SIGNER_CLIENT_ID`, `REQUEST_SIGNER_IDENTITY_POOL_ID`, `REQUEST_SIGNER_USER_POOL_ID`, `REQUEST_SIGNER_AOSS_ENDPOINT` |

   These are the same values as in a personal `~/.pds/.registry-client`, with the service user's name and
   password.
3. **Pull requests from Actions.** Enable "Allow GitHub Actions to create and approve pull requests" (Settings →
   Actions → General → Workflow permissions) so the workflow can open the results pull request.
4. **Retire manual schedules.** If `generate_registry_status_reports.py --commit` runs from someone's machine on
   a schedule, stop it once this workflow is merged, or the two will race on `docs/status/`.

### Limits

- GitHub-hosted runners stop a job after 6 hours. Each node job allows 345 minutes; if the full ATM audit with
  inventories needs longer, run ATM on a self-hosted runner or with `--no-inventory`.
- The runners reach the registry over the public internet, so the collection's network policy must allow the
  public endpoint. If personal runs only work from the JPL network or VPN, the jobs need a self-hosted runner.
- A baseline must come from the same nodes and ancestry version. After a change to `CURRENT_ANCESTRY_VERSION`,
  delete the affected `<node>/metrics.json` in a commit so the next run starts without a baseline.
