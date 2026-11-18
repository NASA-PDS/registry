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
   the anomalous count needs an owner. The "Not API-visible" line counts products without ancestry that the audit
   does not examine (for example `staged`); the ancestry orphan repair examines them. Record the run parameters
   with the numbers.
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
script's summary. The scripts never re-harvest; the node does that with its own files.

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

### 5.1 Two kinds of problem

Harvest writes a `registry-refs` document for a collection from the collection's inventory when the collection
is harvested. The refs are the registry's record of which products belong to which collection. The ancestry
sweeper reaches a non-aggregate product only through those refs, and it does not revisit a collection once the
collection is stamped. That is the behaviour of registry-sweepers `main`, which production runs (registry-sweepers
#298). `develop` (not deployed, because it uses structured metadata) also processes products that were not yet
loaded when their collection was swept, but not products overwritten or listed in refs afterwards (#270); a bundle
loaded after its collection was stamped is not linked on either branch (#301). The planned fixes are a completeness
flag verified by count (#243) and Harvest preserving `ops:` metadata on overwrite (harvest#349). Until production
moves to `develop`, the workaround is the node re-harvesting the collection and EN running the sweepers. So a
product lacks ancestry in one of two ways:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection a report
  names for it is a **best guess** from its identifier (`bundle:collection:product`) and the collection versions
  that are registered. The product may really belong to a collection version that is not loaded; for example,
  products whose inventory is `::64.0` while the registry holds `::56.0` are orphans of a collection the registry
  does not have.
- **Not processed**: the refs do list the product, so its collection is confirmed, but the sweepers never gave
  it ancestry (it was loaded after its collection was processed, it carries an older stamp, or the sweepers have
  a bug).

A third group, **waiting**, is products loaded so recently that the sweepers have not had their chance.

### 5.2 Who fixes what

| Owner | Fixes | How |
|---|---|---|
| **Node** (the data provider's PDS node) | Orphans whose cause is the node's data: the collection is not loaded, the inventory lists a different version of the product, or the inventory does not list it. Also everything fixed by re-harvesting the collection: orphans whose inventory does list the product but whose refs are stale or missing; products that are linked but not processed | Load, correct or remove data; or re-harvest the collection (EN then runs the sweepers). Only the node can |
| **EN** (runs the sweepers, fixes the registry) | Collections stamped with empty refs by the sweepers bug (the bundle lists no members); collections the sweepers have not processed; index mapping fixes | Re-harvest the affected collections and run the sweepers with the fix; run the sweepers once the node has re-harvested; fix the mapping |
| **Sweepers team** | `sweeper_miss`: everything looks right and the sweepers skipped the product | Software fix |
| **Needs a closer look** | `refs_missing` products the audit could not check against the collection's inventory | Re-run with the inventories (not `--no-inventory`), or check the inventory by hand |

The audit's `summary.md` opens with a table in these terms ("What needs to happen"), and
`scripts/audit_rollup.py` puts every node side by side.

### 5.3 Is `refs_missing` a Harvest problem or a sweepers problem?

Neither, as a first guess; read the collection's inventory first. `refs_missing` means no refs document lists the
product while its collection exists. The inventory settles who is responsible:

- The inventory lists a **different version** of the product, or **does not list it**: the node's data does not
  line up (the audit then reports `inventory_version_mismatch` or `not_in_collection_inventory`). The node
  fixes it. Re-harvesting does not help, and neither do the sweepers.
- The inventory **lists this exact product**, but the refs do not: the refs were written from an older
  inventory, or never written. This is a Harvest-side gap, fixed by re-harvesting the collection so that its
  refs are regenerated, and then running the sweepers. It is not a sweepers defect, and the node's data is fine.
- The inventory could not be read (skipped with `--no-inventory`, or the provider's file could not be
  downloaded): the audit cannot tell; this is the "needs a closer look" group. In the first all-node run, every
  `refs_missing` product that was checked by hand turned out to be one of the first two cases, and the
  proportion of node problems was high (EN, GEO, SBNPSI and SBNUMD each had some).

A product that was overwritten (re-harvested) after its collection was processed, and whose collection was not
re-harvested, is a different case: it is `reloaded_after_collection`. Its refs still list it, so it is linked,
but the stamped collection is never revisited and so the product is never reprocessed. The fix is to re-harvest
the collection and run the sweepers. The naming is an inference from harvest times: on IMG the products of
four collections were stamped up to one point in time and not after it, which fits the sweepers having run
part-way through a sequential load.

### 5.4 Findings

| Finding (rule) | Kind | What it means | Action | Owner |
|---|---|---|---|---|
| `collection_not_loaded_overdue` | Orphaned | No collection with the product's collection identifier is registered in the audited node's index. Check first whether the collection is registered under another node (a LIDVID can be registered under several) | Load the parent collection, change its archive status, or fix the product identifier | node |
| `inventory_version_mismatch` | Orphaned | The collection's inventory lists a different version of the product than the registry holds. Usually the registry is older (the listed version is not loaded); it can also be newer (the registry holds a version the inventory does not list). `audit_collection.py --diff` shows the direction | Make them agree: load the listed version, or correct the inventory, or remove the unlisted version. First confirm whether a load is running; a long-stalled load usually means the node does not know about the gap. Re-harvesting the collection does not help | node |
| `not_in_collection_inventory` | Orphaned | The product is registered under the collection but the current inventory lists it under no version | Add it to the inventory, or remove it from the registry | node |
| `refs_missing` (inventory lists the exact product) | Orphaned | The refs were written from an older inventory, or never written | Node re-harvests the collection from its current label and inventory (step 5); EN then runs the sweepers | node |
| `refs_missing` (inventory not checked) | Orphaned, cause unknown | See 5.3 | Re-run with inventories | needs a closer look |
| `reloaded_after_collection` | Not processed | The collection was processed before the product was loaded, and the sweepers do not go back | Node re-harvests the collection (step 5); EN then runs the sweepers | node |
| `stale_stamp` (non-superseded products only) | Not processed | The product carries an older ancestry stamp than its already-stamped collection, which is not revisited. A plain sweeper run does not reach it | Re-harvest the collection and run the sweepers, or run ancestry in overwrite mode (registry-sweepers PR #291) | node (re-harvest); EN (sweepers) |
| `collection_overdue` / `collection_pending` | Not processed | The parent collection has no current stamp; the collection is the root cause. Pending is within the grace period, overdue is beyond it | Confirm the ancestry sweeper ran for the node since the collection was harvested | EN |
| `sweeper_miss` | Not processed | The collection is processed, the refs list the product, the product was loaded before the collection, and it still has no ancestry | Gather the evidence from the reference document's checks (including the refs `batch_id`) and report it | sweepers team |
| Stamped collection with empty `ancestor_refs` that has a bundle | Not processed | The collection counts as swept, so its products are not revisited, and the bundle does not list it as a member | Re-harvest the collection and run the sweepers with the fix from registry-sweepers PR #286 (NASA-PDS/registry-sweepers#284), or run ancestry in overwrite mode. On ATM, that repaired 44 of 45 such collections | EN (sweepers team if it recurs after the fix) |
| Superseded collection version whose products are unprocessed | - | A superseded version is not re-harvested; its bundle refers to the newer version | No re-harvest. Report the products against the real (current) collection version | reporting only |
| Old Harvest version on recent loads | - | The node loads with an outdated Harvest release | Informational. Ask the node to upgrade | node |

Rules that need no action: `no_parent_by_design` (`Product_Service` and `Product_Context` never belong to a
collection) and the `*_pending` rules (`collection_not_loaded_pending`, `collection_pending`,
`refs_missing_pending`), which are inside their grace periods. Recheck on the next run.

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
| h | The collection named for an orphan is a guess | A product of `...::64.0` is shown under the registered `...::56.0`. Compare the collection's inventory (`audit_collection.py --diff`) with the registry before acting; the product may belong to a version that is not loaded |
| i | Refs of another collection version are not evidence for this one | Refs of an older collection version that name an older product version say nothing about the current collection version. The audit counts a refs listing as a version mismatch only when it comes from the product's own collection |
| j | Products that are stamped but linked to an older collection version are not examined | A product that already has ancestry naming collection `::12.1` while the inventory of `::16.0` lists a different version is not a candidate. A node can have tens of thousands of these (on IMG, the `mars2020_navcam_ops_mosaic` collection); `audit_collection.py --diff` shows them and the `load_verdict` can read `stalled` for them even though nothing is waiting to load |
| k | A relative `file_ref` cannot be downloaded | A collection whose registered label location is a local path (not an `https://` URL) cannot have its inventory fetched by `audit_collection.py` or the audit; its products stay under "needs a closer look". See the invalid `file_ref` reports in NASA-PDS/registry#614 |

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
4. **Orphan repair dry run.** The repair's products examined equal "Candidates examined" plus the
   "Not API-visible" line; its repairable bucket is the products that refs list under a collection in the
   registry (`reloaded_after_collection`, `sweeper_miss`, and `stale_stamp` or `collection_*` products that refs
   list) and its unresolved bucket is the products no refs document lists (`refs_missing*`,
   `inventory_version_mismatch`, `not_in_collection_inventory`, `bare_lid_in_inventory`, and waiting products
   not in refs yet). The repair has no grace period and counts a stamp below the current version where the
   audit counts any other stamp. The full table is in
   [the reference](audit-unprocessed-products-reference.md#mapping-to-the-ancestry-orphan-repair-report).
5. **Per-collection spot check.** Run `audit_collection.py` with `--diff --load-status` on the two or three
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
5. **Items for EN and the sweepers team**, kept in a separate section so the node is not asked to
   do work that belongs to others: sweeper runs after the node's re-harvests, mapping fixes and the
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
- after the node re-harvests collections and EN has run the ancestry sweeper;
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
| Re-harvested collections | 45 collections re-harvested on 2026-11-14 were stamped with empty `ancestor_refs` although their bundle was already stamped | Sweepers defect (NASA-PDS/registry-sweepers#284, fixed by PR #286); the bundle's `/members` stays empty until repaired | Node re-harvests; EN runs the sweepers with the fix. Done on 2026-11-15: 44 of the 45 now have the bundle in `ancestor_refs`; `juno_mwr:document::3.0` is still empty and needs a closer look |

How the analysis ran: dry run on the node, full run with `--gzip`, `audit_collection.py --diff
--load-status` over `anomalous_collections.txt` to produce the load verdicts, `download_collection_files.py`
for the collections that needed re-harvesting, the cross-checks from section 7, and one tracking issue
structured as in section 8 with node actions and registry or sweepers items in separate sections.
