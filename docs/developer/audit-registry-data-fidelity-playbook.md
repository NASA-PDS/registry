# Playbook: Registry Data Fidelity Audit for a Node

A runbook for auditing one PDS node's data in the registry, reading the results, turning them into
actions with an owner, and writing them up as a node issue. The same steps work for any node.

Companion documents:

- [Design](audit-unprocessed-products-design.md): why the audit works the way it does.
- [Reference](audit-unprocessed-products-reference.md): column meanings, the technical meaning of every
  rule, per-rule hand checks, limitations.
- [`scripts/README.md`](../../scripts/README.md): the sections "Collection Audit Script", "Unprocessed
  Product Audit" and "Collection Re-harvest Download".

## 1. What the audit answers and what it does not

The audit answers: which products that the public API could show are missing ancestry (and therefore
missing from `/members`, `/ancestors` and related results), why each one is missing, and who has to act.

- "API-visible" means `archive_status` of `archived` or `certified` and not superseded. Nothing else is
  examined.
- Every script is read-only. They issue `_search` and `_count` queries and download files; they never
  write to the registry.
- It does not detect partially wrong but non-empty `ancestor_refs` (for example a missing bundle ref).
- It does not validate PDS4 labels or the content of data files. File path and checksum checks are a
  separate option of `audit_collection.py` (`--check-files`).
- It does not say when ancestry ran. There is no such timestamp; harvest times stand in for it.

## 2. Prerequisites and setup

1. A Python virtualenv that has the registry client but not this repository's editable install. The
   editable install hides the client's `pds.aossrequestsigner` module and the scripts then fail with
   `ModuleNotFoundError: No module named 'pds.aossrequestsigner'`. The `registry-client` checkout's
   virtualenv works.
2. Registry credentials in the shell environment, not on the command line. Source your credentials file
   once per shell. The scripts accept `--env-file`, but shell-sourced variables take precedence and
   sourcing first is the supported routine.
3. Node names are the registry index prefixes (the part before `-registry`). `--node` also accepts an alias,
   but the `node` column in the CSV files reports the underlying index prefix. The audit skips the legacy
   mirror index (`en-legacy-registry`).
4. Run every command from the repository root so `scripts/...` paths resolve.

Setup used by every command below:

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
REGISTRY_CLIENT_VENV="<path-to-registry-client-venv>"
PYTHON="${REGISTRY_CLIENT_VENV}/bin/python"
NODE="<node-index-prefix>"
OUT_DIR="./audit_unprocessed/${NODE}"

source "${ENV_FILE}"
```

## 3. Runbook

### Step 1: bounded dry run on one node

A dry run proves credentials, the node name and the virtualenv before the long run. `--max-products`
stops after N candidate products, so the counts in a dry run are truncated; do not quote them.

```bash
DRY_DIR="./audit_unprocessed/${NODE}-dry"
"${PYTHON}" scripts/audit_unprocessed_products.py \
    --output-dir "${DRY_DIR}" --node "${NODE}" --max-products 5000
```

Check that `${DRY_DIR}/summary.md` exists and that the node appears in the headline and the run
parameters.

### Step 2: full node run

```bash
"${PYTHON}" scripts/audit_unprocessed_products.py \
    --output-dir "${OUT_DIR}" --node "${NODE}" --gzip
```

- `--gzip` writes `unprocessed_products.csv.gz`. The uncompressed CSV can reach hundreds of MB for a large
  node.
- When a product is in no `registry-refs` document, the audit downloads the current inventory of its
  collection from the data provider's server to tell stale refs from products the inventory does not list.
  These servers can be slow (tens of MB at tens of KB/s), so a full run can take hours. `--no-inventory`
  skips the downloads; those products are then reported as `refs_missing`, and the rules
  `inventory_version_mismatch` and `not_in_collection_inventory` cannot appear.
- For a re-run, pass the earlier products CSV so the summary reports what changed (see section 9):

```bash
PREVIOUS_CSV="<path-to-previous-unprocessed_products.csv.gz>"
RERUN_DIR="./audit_unprocessed/${NODE}-rerun"
"${PYTHON}" scripts/audit_unprocessed_products.py \
    --output-dir "${RERUN_DIR}" --node "${NODE}" --gzip --previous-csv "${PREVIOUS_CSV}"
```

Other options: `--collection-grace-days` (default 1), `--product-grace-days` (default 7),
`--ancestry-version` (default 7, the current sweeper stamp), `--max-coverage-collections` (default 200),
`--timeout` (default 60 seconds per request).

### Step 3: read the outputs

Read in this order.

| Order | File | What to take from it |
|---|---|---|
| 1 | `summary.md` | Totals, anomalies by rule and node, worst collections, stamped collections with empty refs, expected-pending counts, orphans, class and age breakdowns, the change since the previous run, and a note per rule |
| 2 | `collections.csv` | One row per collection: `state`, `stamp_version`, `harvest_date_time`, `bundle_lidvids`, `anomalous_product_count`, `refs_count`, `member_count`, `stamped_member_count`, `coverage_note`, `superseded_by` |
| 3 | `unprocessed_products.csv.gz` | One row per product: `lidvid`, `collection_lidvid`, `collection_state`, `in_refs`, `rule`, `severity`, `rationale` |
| 4 | `anomalous_collections.txt` | Collection LIDVIDs that root at least one anomaly; input for steps 4 and 5 |

How to read `summary.md`:

1. Headline: candidates examined, expected (will resolve on their own) and anomalous (need attention). Only
   the anomalous count needs an owner. Record the run parameters with the numbers.
2. "Anomalies by rule" and "By rule and node": the row counts that feed the decision table in section 5.
3. "Anomalous collections": worst first, with the collection state, harvest time, affected product count
   and refs coverage.
4. "Stamped collections with empty refs": collections that are stamped but have empty `ancestor_refs`; those
   with a bundle leave the bundle's `/members` empty.
5. "Expected pending": the number that should shrink on its own. Do not assign actions to it.
6. "Orphans": products whose collection LID has no API-visible collection.

To count rows per rule in the gzip CSV without opening it in a spreadsheet:

```bash
PRODUCTS_CSV="${OUT_DIR}/unprocessed_products.csv.gz"
"${PYTHON}" - "${PRODUCTS_CSV}" <<'EOF'
import collections, csv, gzip, sys
counts = collections.Counter()
with gzip.open(sys.argv[1], "rt", newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        counts[(row["severity"], row["rule"])] += 1
for (severity, rule), count in sorted(counts.items()):
    print(f"{severity:10} {rule:36} {count:>10,}")
EOF
```

Never trust the coverage note alone; see pitfall (b) in section 6.

### Step 4: classify each anomalous collection

Run the collection audit over the list the products audit wrote. `--diff` compares the inventory with the
registry LIDVID by LIDVID, and `--load-status` says whether loading is still going on (section 4).

```bash
COLLECTIONS_FILE="${OUT_DIR}/anomalous_collections.txt"
CLASSIFY_DIR="${OUT_DIR}/collection_audit"
ACTIVE_DAYS=3
"${PYTHON}" scripts/audit_collection.py \
    --from-file "${COLLECTIONS_FILE}" --diff --load-status \
    --active-days "${ACTIVE_DAYS}" --output-dir "${CLASSIFY_DIR}"
```

Outputs in `${CLASSIFY_DIR}`:

| File | Use |
|---|---|
| `summary.csv` | One row per collection. Columns include `label`, `inventory`, `api_members`, the `registry_*` counts, `diff_inventory_not_registry`, `diff_registry_not_inventory`, `inventory_loaded`, `inventory_not_loaded`, `latest_member_harvest`, `load_verdict` |
| `<slug>/diff_inventory_not_registry.csv` | LIDVIDs the inventory lists that the registry does not hold (not loaded, or loaded under a different version) |
| `<slug>/diff_registry_not_inventory.csv` | Non-superseded registry LIDVIDs the inventory does not list |

`<slug>` is derived from the last two segments of the collection LID. Add `--verbose-report` to one
collection when you need a plain-language explanation of every count and a comparison of the collection's
harvest time with its newest member's.

Sort each collection into one of these groups, then use the decision table:

- `load_verdict` of `stalled` or `not_started`, with product versions that differ between the registry and
  the inventory: a node loading problem.
- `complete` or `loading`: loading is not the problem; look at the product-level rules (stale refs, reload
  after the collection, stale stamp, sweeper timing).
- Large `diff_registry_not_inventory.csv`: the registry holds products the inventory does not list.

### Step 5: download re-harvest inputs

For collections that need re-harvesting, download the current label and inventory from the URLs the
registry holds. This needs the public API and the provider servers, not registry credentials.

```bash
REHARVEST_DIR="./reharvest/${NODE}"
AUDIT_CSV="${OUT_DIR}/unprocessed_products.csv.gz"

# List URLs and the Harvest fileRef prefixes; nothing is downloaded
"${PYTHON}" scripts/download_collection_files.py --list-only \
    --output-dir "${REHARVEST_DIR}" --from-audit-csv "${AUDIT_CSV}"

# Download the label and inventory of each collection
"${PYTHON}" scripts/download_collection_files.py \
    --output-dir "${REHARVEST_DIR}" --from-audit-csv "${AUDIT_CSV}"
```

- With `--from-audit-csv` the default rules are `refs_missing`, `reloaded_after_collection`,
  `sweeper_miss` and `stale_stamp`. Change them with `--rules`. The rules `inventory_version_mismatch` and
  `not_in_collection_inventory` are not re-harvest cases and are not in the default list.
- `--from-file` accepts a list of collection LIDVIDs instead, for example `anomalous_collections.txt` or a
  hand-edited subset. `--skip-existing` resumes an interrupted run.
- A LIDVID can be registered under several nodes, each with its own copy of the files. For those the
  script requires `--node-name`, the `ops:Harvest_Info/ops:node_name` value of the copy to use:

```bash
NODE_NAME="<harvest-node-name-such-as-PDS_ATM>"
"${PYTHON}" scripts/download_collection_files.py \
    --output-dir "${REHARVEST_DIR}" --from-audit-csv "${AUDIT_CSV}" --node-name "${NODE_NAME}"
```

Outputs in `${REHARVEST_DIR}`: `files/<host>/<url path>`, `manifest.csv` and
`harvest_config_snippet.xml` (the `<load><directories>` and `<fileInfo><fileRef .../>` entries for the
Harvest configuration). In `manifest.csv`, check two columns before anyone re-harvests:

- `md5_changed_since_harvest` is `True`: the provider changed the file after harvest. A re-harvest picks up
  the new content.
- `records_match` is `False`: the provider's label and inventory disagree. Re-harvesting cannot fix this;
  the node must.

Collections whose registered label `file_ref` is not a URL cannot be downloaded and are listed in the
script's summary. The scripts never re-harvest; registry operations does that with the downloaded files.

## 4. Is the node still loading?

Before asking a node to "finish loading", find out whether it already is. `--load-status` answers this per
collection.

The signal is the newest `ops:Harvest_Info/ops:harvest_date_time` among products that are in BOTH the
collection's inventory and the registry. Registry products the inventory does not list (typically older
versions) are ignored, so old versions cannot make a stalled load look active. The report also prints the
newest harvest time among those other products for context.

| Verdict | Meaning | Reading |
|---|---|---|
| `complete` | Every inventory product is loaded | Loading is finished |
| `not_started` | No inventory product is in the registry | Nothing of the listed versions has been loaded |
| `loading` | Partially loaded; newest loaded member harvested within `--active-days` (default 3) | Loading looks active; recheck later |
| `stalled` | Partially loaded; nothing in the inventory harvested within `--active-days` | The load stopped part-way |

- Widen `--active-days` for nodes that load in occasional batches (for example `--active-days 14`); the
  verdict depends entirely on that window. State the window next to the verdict in any report.
- A long-stalled load usually means the node does not know about the gap. Confirm with the node whether a
  load is running before asking for one.
- Also compare the Harvest version recorded in `ops:Harvest_Info/ops:harvest_version` on the newest loaded
  members with the current Harvest release. If recent loads were written by an old release, ask the node to
  upgrade. The scripts do not report this field; read it with the `show_doc` helper from the reference
  document's verification toolkit after adding the field to its `_source` list.

## 5. Decision table: finding, meaning, action, owner

Owners: **node** (the data provider's PDS node), **registry operations** (the team that re-harvests and runs
sweepers on demand), **sweepers** (the registry-sweepers team).

| Finding | What it means | Action | Owner |
|---|---|---|---|
| Collection `load_verdict` of `stalled` or `not_started`, and rule `inventory_version_mismatch` | The inventory lists a different version of the product than the registry holds; refs follow the inventory, so the registered version is never swept | Finish or start loading the product versions the inventory lists. First confirm whether a load is actually running; a long-stalled load usually means the node does not know about the gap. Older registered versions should then be superseded. Re-harvesting the collection does not help | node |
| `refs_missing` where the inventory lists the product | Stale refs: the refs documents were written from an older inventory than the one served now | Re-harvest the collection from its current label and inventory (use step 5), then run the ancestry sweeper | registry operations, with the node |
| `not_in_collection_inventory` | The product is registered under the collection but the current inventory lists it under no version, and no refs document lists it | Decide whether the product belongs in the inventory (update the inventory and re-harvest the collection) or should be removed from the registry. Re-harvesting alone does not help | node |
| `reloaded_after_collection` | The collection was swept, then the product was re-harvested and lost its ancestry. Not a sweeper defect | Re-harvest the collection (step 5), then let the sweeper run | registry operations |
| `stale_stamp` (non-superseded products only) | The product carries an older ancestry stamp than its already-stamped collection, which is not revisited | Re-sweep the collection | sweepers / registry operations |
| `collection_overdue` / `collection_pending` | The parent collection has no current stamp; the collection is the root cause. Pending is within the grace period, overdue is beyond it | Confirm the ancestry sweeper ran for the node since the collection was harvested | sweepers |
| `collection_not_loaded_overdue` | No API-visible collection exists for the product's collection LID well after the product was harvested | Load the parent collection, change its archive status, or fix the product LID | node |
| Stamped collection with empty `ancestor_refs` that has a bundle | The collection counts as swept, so its products are not revisited, and the bundle's `/members` is empty | File or comment on a registry-sweepers issue (see NASA-PDS/registry-sweepers#284 and PR #286). Repair by running ancestry in overwrite mode for the node, or by re-harvesting the collection and running the sweepers with the PR #286 fix. On ATM, that repaired 44 of 45 such collections | sweepers |
| Superseded collection version whose products are unprocessed | A superseded version is not re-harvested; its bundle refers to the newer version | No re-harvest. Report the products against the real (current) collection version | - (reporting only) |
| Old Harvest version on recent loads | The node loads with an outdated Harvest release | Informational. Ask the node to upgrade | node |

Rules that need no owner:

- `no_parent_by_design`: `Product_Service` and `Product_Context` never belong to a collection.
- `*_pending` rules (`collection_not_loaded_pending`, `collection_pending`, `refs_missing_pending`): within
  the grace periods, expected to resolve on their own. Recheck on the next run.
- `sweeper_miss`: nothing in the registry data explains the gap. Gather the evidence from the reference
  document's checks (including the refs `batch_id`) and report it to the sweepers team.

## 6. Known pitfalls

| | Pitfall | How to recognize it |
|---|---|---|
| a | On the ATM registry index, `ops:Provenance/ops:superseded_by` is returned in `_source` but cannot be searched. `exists`, `term` and `wildcard` queries on it match nothing, so a server-side "not superseded" filter matches everything. Superseded products must be filtered client-side. The audit does this | A manual `_count` with a `must_not exists` on `superseded_by` returns more than the audit's candidate count. `_count`-based numbers, such as `registry_superseded` (reported as 0) and `registry_api_visible` in `audit_collection.py` and the member counts behind `coverage_note`, still include superseded products on that index. `--diff` and `--load-status` filter client-side and are not affected |
| b | `coverage_note` compares counts, not identities | A collection reports `ok` or "refs complete" while a specific product is in no refs document. The per-product verdict (`refs_missing`) is identity-based and authoritative. Settle disagreements with `show_refs` |
| c | Harvest time stands in for processing time | A rule such as `reloaded_after_collection` says "collection harvested before product". The registry does not record when ancestry ran, so the ordering is an inference |
| d | A LIDVID can be registered under several nodes, each with its own files | `download_collection_files.py` refuses to pick a copy and asks for `--node-name`. The `node` column of the CSV shows which index each row came from |
| e | Inventory servers can be slow | The full run sits for long stretches on inventory downloads (tens of MB at tens of KB/s). Use `--timeout` to tune and `--no-inventory` for a quick pass |
| f | `--max-products` truncates per-collection counts | Counts from a dry run are lower than the real ones and collection tallies are partial. Never quote a dry-run number |
| g | A surprising number may be a query artifact | Before trusting any count, sample the population and read the `_source` of a few documents. Confirm fields exist, are searchable and hold the values the query assumes |

## 7. Verifying a finding by hand, and cross-checks

For any row, the reference document gives a toolkit and a "Check" procedure per rule. Set up the helpers
once (`registry_query`, `show_doc`, `show_refs`, `api_member_hits`) from
[the verification toolkit](audit-unprocessed-products-reference.md#verification-toolkit), then follow the
steps under the rule you are checking in
[Rules: technical meaning and how to check each](audit-unprocessed-products-reference.md#rules-technical-meaning-and-how-to-check-each).
The public symptom check is `api_member_hits` returning `0` for the product in its collection.

Cross-checks that add confidence before you publish numbers:

1. **Independent count.** Run the `_count` query in the reference document's "Verifying the audit itself"
   (candidate count) and compare it to "Candidates examined" for the same node, run without
   `--max-products`. On an index where `superseded_by` is not searchable (pitfall a), expect the
   server-side count to exceed the audit's by the number of superseded products, and explain the
   difference rather than hiding it.
2. **Sample each rule.** Draw a few rows per rule from the CSV and walk each through its "Check" steps.
3. **Reconcile with earlier reports.** The orphan counts in registry-sweepers#273 (collections stamped with
   empty refs, products with no stamp) should be reproducible per node as `stamped_empty_refs` collections
   and population A and B products. Explain any difference (for example superseded versions, or products
   loaded since).
4. **Per-collection spot check.** Run `audit_collection.py` with `--diff --load-status` on the two or three
   worst collections and confirm the load verdict and diff files match the product rules.

## 8. Turning findings into a node issue

Convention: one tracking issue per node, filed in NASA-PDS/registry under the theme issue
NASA-PDS/registry#609. The ATM example is NASA-PDS/registry#610. Reference the theme in the issue body.

Public-repo rule: the issue may contain only public PDS identifiers and counts (LIDs, LIDVIDs, collection
and bundle names, node names, numbers, dates). No credentials, account or endpoint values, internal
hostnames, user names or email addresses, and no URLs that point at internal servers. Attach nothing from
the output directories that contains such values.

Recommended structure:

1. **Summary**: node, run date, audit parameters (ancestry version, grace periods, `--active-days`), API
   visible products examined, and the headline anomalous count. State that superseded versions are excluded.
2. **Findings**: one short paragraph or bullet per finding with its count, in the order of the decision
   table. Say how the number was obtained (the audit rule).
3. **Per-collection remaining work**: a table of the collections that still need work.

   | Collection | Rule | Products affected | Registered / inventory versions | Load verdict | Newest loaded member (days old) |
   |---|---|---|---|---|---|

4. **Actions for the node**: loading, inventory and LID problems, each with the collections involved and
   what "done" looks like (the next audit run does not list them).
5. **Items for registry operations and sweepers**, kept in a separate section so the node is not asked to
   do work that belongs to others: re-harvests, sweeper runs, the empty-refs collections and the
   registry-sweepers issue link.
6. **Evidence**: audit run date, the commands (with variable names, not values), and which
   cross-checks from section 7 were done. Name the output files; do not attach files that contain
   anything beyond public identifiers.

Draft the body in a file, then create the issue with one `gh` command:

```bash
ISSUE_REPO="NASA-PDS/registry"
ISSUE_TITLE="Registry data fidelity audit: <node> node"
BODY_FILE="<path-to-issue-body.md>"
gh issue create --repo "${ISSUE_REPO}" --title "${ISSUE_TITLE}" --body-file "${BODY_FILE}"
```

Follow the NASA-PDS issue templates and labels, and add the new issue to the theme's task list.

## 9. When and how to re-run

Re-run the full node audit:

- after the node reports a load finished, to confirm the version mismatches clear;
- after registry operations re-harvests collections and the ancestry sweeper has run;
- after a sweepers fix is deployed, to confirm empty-refs collections are repaired;
- on a regular schedule while a node is loading (the pending counts should fall).

Always pass the previous products CSV (`.csv` or `.csv.gz`) as `--previous-csv`, and keep the same
`--node`, grace periods and `--ancestry-version` so the runs are comparable. The summary then ends with a
section "Change since previous run":

| Line | Meaning |
|---|---|
| New | Products (keyed on LIDVID and rule) in this run but not in the previous one. Investigate: newly loaded, newly re-harvested, or a rule change |
| Resolved | Products in the previous run but not in this one. The fixes worked, or the product left the API-visible set (for example it was superseded) |
| Persisting | In both runs. These need the actions in section 5 |

A large "New" count right after a re-harvest is common: re-harvested products are overwritten and can
appear under a different rule (for example `collection_pending`) until the sweeper runs.

## 10. The audit suite and the regression plan

The data fidelity audits are read-only scripts under `scripts/`. Each answers one question and can run on its
own; `--check` on the first two turns them into regression tests with an exit code.

| Audit | Script | Question | Regression mode |
|---|---|---|---|
| Unprocessed products | `audit_unprocessed_products.py` | Which API-visible products lack current ancestry, and why? | `--check`, optionally `--baseline` (a previous `metrics.json`) |
| Index mappings | `audit_index_mappings.py` | Do the node indices map the same fields with the same types? A field missing from a mapping cannot be searched | `--check` (any error-level discrepancy) |
| One collection | `audit_collection.py` | Is this collection's inventory loaded, with correct file paths and checksums? | Exit code per collection |

The mapping audit is the root-cause check for failures the product audit can only see as symptoms: a field
absent from a node's mapping (for example `ops:Provenance/ops:superseded_by`) breaks every query that depends on
it, and the effect appears in the product audit only as miscounted or misclassified products. Run the mapping
audit before a full product audit and read its error-level discrepancies first.

A regression schedule has three parts:

1. **Fast checks, frequently.** The mapping audit (it reads one mapping per index) and the product audit with
   `--check --no-inventory --baseline <last accepted metrics.json>`.
2. **Full audit, weekly.** The product audit with inventories (`--inventory-cache-dir`), against its own
   baseline, with `--history-csv` appending to a trend file.
3. **After every load or fix.** Re-run the full audit for the affected node and promote its `metrics.json` to
   the baseline once the owners have accepted the remaining findings.

Candidate audits not yet written, each reusing the same client and output conventions:

- Superseded chains: every LID's versions form one chain, each superseded product names the next version, and
  the newest version has no `superseded_by`.
- File references: every `file_ref` starts with `https://` (the status report already lists these per node).
- Registry-refs coverage: every member of a processed collection inventory has a refs document.
- API symptom canaries: a bare-LID request returns the newest version; `/members` of a bundle is non-empty.

## 11. Worked example: ATM node

The tracking issue is NASA-PDS/registry#610. Correction: the first ATM numbers included superseded
product versions and were corrected after the audit began filtering them client-side (pitfall a). All
numbers below exclude superseded versions.

| Finding | Number | Reading | Action and owner |
|---|---|---|---|
| API-visible products without ancestry | about 2.78 million | Scale of the gap; most is explained by the collection-level findings below | See rows below |
| Collections partially loaded or not started | 22 collections, none currently loading (newest loaded member 130 to 535 days old) | `--load-status` verdicts of `stalled` and `not_started` | Node: check whether a load is running; finish or start loading |
| maven.iuvs collections | Registry holds product versions 13.1; the inventory lists 14.0; only 4 to 8 percent loaded | Rule `inventory_version_mismatch`; refs follow the inventory, so the registered versions are never swept | Node: load the 14.0 versions; the 13.1 versions are then superseded. Re-harvesting does not help |
| juno_mwr 3.0 | Collection registered, none of its products loaded | Verdict `not_started` | Node: start loading the products the inventory lists |
| Harvest version | Newest loaded members written by Harvest 4.0.7 while 5.1.3 was current | Informational | Node: upgrade Harvest |
| Re-harvested collections | 45 collections re-harvested on 2026-11-14 were stamped with empty `ancestor_refs` although their bundle was already stamped | Sweepers defect (NASA-PDS/registry-sweepers#284, fixed by PR #286); the bundle's `/members` stays empty until repaired | Registry operations: re-harvest and run the sweepers with the fix. Done on 2026-11-15: 44 of the 45 now have the bundle in `ancestor_refs`; `juno_mwr:document::3.0` is still empty and needs a closer look |

How the analysis ran: dry run on the node, full run with `--gzip`, `audit_collection.py --diff
--load-status` over `anomalous_collections.txt` to produce the load verdicts, `download_collection_files.py`
for the collections that needed re-harvesting, the cross-checks from section 7, and one tracking issue
structured as in section 8 with node actions and registry or sweepers items in separate sections.
