# Unprocessed Product Audit: Output Reference and Verification Guide

Companion to the [design](audit-unprocessed-products-design.md) and the usage notes in
[`scripts/README.md`](../../scripts/README.md). This page explains what each output means in
technical terms and how to confirm any row by hand.

## Reviewing the output

Every run writes to the directory given as `--output-dir`. Review in this order:

| Order | File | Use it to |
|---|---|---|
| 1 | `summary.md` | See totals, anomalies grouped by rule and node, the worst collections and what each rule means |
| 2 | `collections.csv` | See every collection's state, bundle, and refs coverage |
| 3 | `unprocessed_products.csv` | See one row per product with its rule, severity and a one-line rationale |
| 4 | `anomalous_collections.txt` | Feed `audit_collection.py --from-file` to dig into each collection |

`unprocessed_products.csv` can reach hundreds of MB. Slice it with a spreadsheet, or with the Python
standard library:

```bash
CSV="./audit_unprocessed/unprocessed_products.csv"
RULE="reloaded_after_collection"
SAMPLE_SIZE=3
python - "${CSV}" "${RULE}" "${SAMPLE_SIZE}" <<'EOF'
import csv, random, sys
path, rule, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
with open(path, newline="", encoding="utf-8") as f:
    rows = [r for r in csv.DictReader(f) if r["rule"] == rule]
print(f"{len(rows)} rows with rule {rule}")
for row in random.sample(rows, min(size, len(rows))):
    print(row["node"], row["lidvid"], "|", row["rationale"])
EOF
```

Test results are not written to a file. Run them with:

```bash
./.venv/bin/python -m pytest tests/scripts -v
```

Add `--junitxml=test-results.xml` for a report file.

## Column reference: `unprocessed_products.csv`

| Column | Meaning |
|---|---|
| `node` | Index prefix the product lives in (`geo` for `geo-registry`) |
| `lidvid`, `product_class` | Identity and `product_class` of the product |
| `population` | `A` no ancestry stamp; `B` stamped with the current version but `ancestor_refs` empty or absent; `C` stamped with any other version |
| `stamp_version` | Value of `ops:Provenance/ops:registry_sweepers_ancestry_version`; empty when absent |
| `has_ancestor_refs` | Whether `ops:Provenance/ops:ancestor_refs` is non-empty |
| `harvest_date_time`, `harvest_age_days` | `ops:Harvest_Info/ops:harvest_date_time` and its age at run time |
| `bundle_lid` | First four segments of the product LID |
| `collection_lidvid` | Parent collection. From `registry-refs` when a refs document lists the product, otherwise the collection matched by the product LID's first five segments. Empty when no collection was found |
| `collection_state` | State of that collection (see below) |
| `collection_harvest_date_time` | Harvest time of that collection |
| `in_refs` | `true`/`false` when `registry-refs` was consulted for this product, empty when it was not needed |
| `rule`, `severity`, `rationale` | The verdict. `severity` is `expected` (should resolve on its own) or `anomalous` |

## Terms: orphaned, not processed, and who fixes what

`summary.md` opens with "What needs to happen", a table in plain language. It uses these terms.

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection shown for it
  is a **best guess**, derived from the product's identifier (`bundle:collection:product`) and the collection
  versions that are registered. The product may really belong to a collection version that is not loaded.
  Rules: `collection_not_loaded_overdue`, `inventory_version_mismatch`, `not_in_collection_inventory`,
  `bare_lid_in_inventory`, `refs_missing`.
- **Not processed**: the `registry-refs` documents list the product, so its collection is confirmed, but the
  sweepers never gave it ancestry. Rules: `reloaded_after_collection`, `stale_stamp`, `collection_overdue`,
  `sweeper_miss`, and a collection stamped with empty refs that has a bundle.
- **Waiting**: loaded recently, expected to resolve by itself (the `*_pending` rules and `no_parent_by_design`).

Harvest writes the refs from a collection's inventory when the collection is harvested, and the ancestry sweeper
reaches a non-aggregate product only through them. It does not revisit a collection once it is stamped (on `main`, which production runs). That is
why the owner follows from the rule:

| Owner | Rules |
|---|---|
| Node | `collection_not_loaded_overdue`, `inventory_version_mismatch`, `not_in_collection_inventory`; and, by re-harvesting the collection (EN then runs the sweepers), `refs_missing` where the inventory lists the exact product, `reloaded_after_collection`, `stale_stamp` |
| EN (runs the sweepers) | `collection_overdue`, a collection stamped with empty refs that has a bundle (sweepers bug, fixed in PR #286) |
| Sweepers team | `sweeper_miss`, `bare_lid_in_inventory` |
| Needs a closer look | `refs_missing` that was reached without the collection inventory |
| No action | `*_pending`, `no_parent_by_design` |

`refs_missing` is therefore not a verdict on its own. With the inventory read, a product that no refs document
lists is classified by what the inventory says: another version (`inventory_version_mismatch`, node), no
listing (`not_in_collection_inventory`, node), a LID without a version (`bare_lid_in_inventory`), or the exact
product (`refs_missing`: stale or never-written refs, the node re-harvests). Without the inventory (`--no-inventory`,
or a provider file that cannot be downloaded) it stays `refs_missing` and is reported as needing a closer look.

## Background: what "processed" means

The ancestry sweeper marks a product processed by writing two fields:

- `ops:Provenance/ops:registry_sweepers_ancestry_version`: the version stamp (currently `7`).
- `ops:Provenance/ops:ancestor_refs`: the ancestors' LIDs and LIDVIDs.

Facts that drive the rules:

- Collections are selected by the sweeper directly. A collection is pending when its stamp is missing
  or not the current version.
- A non-aggregate product is selected only when it appears in `product_lidvid` of a
  `<node>-registry-refs` document whose `collection_lidvid` is a pending collection. A product with no
  refs document is never touched.
- A stamped collection is never revisited. A product re-harvested afterwards loses its ancestry and
  nothing restores it. Refs added to a stamped collection later are never swept. This describes registry-sweepers `main`, which production runs (registry-sweepers #298). `develop`, which is not deployed because it uses structured metadata, adds a deferral (PR #256) that processes products that were not yet loaded when their collection was swept. It does not cover products overwritten afterwards or refs added afterwards (#270), or a bundle loaded after its collection (#301); the completeness flag verified by count (#243) and Harvest preserving `ops:` metadata on overwrite (harvest#349) are the planned fixes. Until production moves to `develop`, the workaround is for the node to re-harvest the collection and for EN to run the sweepers.
- `exists` queries treat an empty array as absent, so population B is found with
  `must_not exists ancestor_refs`.
- The stamp is a `keyword` field. The audit compares it for equality, never with a range.
- There is no timestamp for when ancestry ran. `harvest_date_time` is the only time signal, so rules that
  compare "collection processed before product" actually compare harvest times.

### Collection states

| State | Condition |
|---|---|
| `processed` | Stamp is current and `ancestor_refs` non-empty |
| `stamped_empty_refs` | Stamp is current and `ancestor_refs` empty or absent. If a bundle references the collection, that bundle's `/members` is empty |
| `unprocessed_pending` | Stamp missing or stale, harvested within `--collection-grace-days` |
| `unprocessed_overdue` | Stamp missing or stale, harvested longer ago than that, or harvest time unknown |

A `stamped_empty_refs` collection counts as stamped, so its products are judged by the
processed-collection rules.

## Verification toolkit

Set up once per shell. Use a virtualenv that has the registry client but not this repository's editable
install (see Troubleshooting in `scripts/README.md`).

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
source "${ENV_FILE}"
REGISTRY_CLIENT="<path-to-registry-client-venv>/bin/pds-registry-client"
API_BASE="<pds-search-api-base-url>"
NODE="<node column of the CSV row>"
LIDVID="<lidvid column of the CSV row>"
COLLECTION_LIDVID="<collection_lidvid column of the CSV row>"

registry_query() {
  # Usage: registry_query <index path and endpoint> <JSON body>
  local query_file
  query_file="$(mktemp)"
  printf '%s' "$2" > "${query_file}"
  "${REGISTRY_CLIENT}" -d "@${query_file}" "$1"
  rm -f "${query_file}"
}

show_doc() {
  # Usage: show_doc <lidvid>  - ancestry fields of one registry document
  local body
  body="$(jq -n --arg id "$1" '{size: 1, query: {term: {lidvid: $id}}, _source: [
    "lidvid", "product_class",
    "ops:Provenance/ops:registry_sweepers_ancestry_version",
    "ops:Provenance/ops:ancestor_refs",
    "ops:Harvest_Info/ops:harvest_date_time",
    "ops:Tracking_Meta/ops:archive_status",
    "ops:Provenance/ops:superseded_by"]}')"
  registry_query "/${NODE}-registry/_search" "${body}" | jq '.hits.hits[0]._source'
}

show_refs() {
  # Usage: show_refs <product lidvid>  - registry-refs documents that list the product, across all nodes
  local body
  body="$(jq -n --arg id "$1" '{size: 5, query: {term: {product_lidvid: $id}}, _source: ["collection_lidvid", "batch_id"]}')"
  registry_query "/*-registry-refs/_search" "${body}" | jq '.hits'
}

api_member_hits() {
  # Usage: api_member_hits <collection lidvid> <member lidvid>  - 1 if the API lists the member, 0 if not
  local encoded
  encoded="$(jq -rn --arg id "$1" '$id | @uri')"
  curl -s -G "${API_BASE}/products/${encoded}/members" \
    --data-urlencode "q=lidvid eq \"$2\"" --data-urlencode "limit=1" | jq '.summary.hits'
}
```

Registry `_source` values can be scalars or arrays, and unprocessed documents simply lack the ancestry
fields. Compare harvest times as UTC timestamps.

## Rules: technical meaning and how to check each

In every case first confirm the product is a real candidate: `show_doc "${LIDVID}"` should show
`archive_status` of `archived` or `certified` and no `superseded_by`, and either no stamp, a stamp other
than the current version, or a current stamp with no `ancestor_refs`.

### `no_parent_by_design` (expected)

- **Meaning:** `product_class` is `Product_Service` or `Product_Context`. These never belong to a
  collection, so the sweeper never gives them ancestry.
- **Check:** `show_doc "${LIDVID}"` and read `product_class`.
- **Action:** none. If another class turns out to have no collection by design, add it to
  `NO_PARENT_CLASSES` in `scripts/unprocessed_audit/model.py`.

### `collection_not_loaded_pending` / `collection_not_loaded_overdue`

- **Meaning:** no API-visible collection matches the product. The collection is found by the first five
  segments of the product LID (`urn:<agency>:<archive>:<bundle>:<collection>`), or by the refs document's
  `collection_lidvid` when one lists the product. Pending when the product was harvested within
  `--product-grace-days`, overdue otherwise (or when its harvest time is unknown).
- **Check:** derive the collection LID from the rationale or the product LID, then look for it in any
  state:

  ```bash
  COLLECTION_LID="<first five segments of the product LID>"
  registry_query "/*-registry/_search" "$(jq -n --arg lid "${COLLECTION_LID}" '{size: 5, query: {term: {lid: $lid}},
    _source: ["lidvid", "ops:Tracking_Meta/ops:archive_status", "ops:Provenance/ops:superseded_by"]}')" | jq '.hits.hits'
  ```

  No hits: the collection is not loaded. Hits with a status other than `archived`/`certified`, or a
  `superseded_by`: the collection exists but the API hides it. A product whose LID does not follow the
  bundle:collection:product pattern also lands here.
- **Action:** pending resolves when the collection is loaded and swept. Overdue means load the
  collection, change its archive status, or fix the product LID.

### `collection_pending` / `collection_overdue`

- **Meaning:** the parent collection exists but is not stamped with the current version. Pending when
  harvested within `--collection-grace-days`, overdue otherwise. The collection is the root cause: the
  sweeper cannot reach the product until it processes the collection.
- **Check:** `show_doc "${COLLECTION_LIDVID}"`. Expect no stamp (or an old one) and no `ancestor_refs`.
  Compare its `harvest_date_time` with the run time.
- **Action:** pending resolves at the next sweeper run. Overdue: check that the ancestry sweeper has run
  against that node since the collection was harvested, and audit the collection with
  `audit_collection.py`.

### `reloaded_after_collection` (anomalous)

- **Meaning:** the collection is stamped with the current version and a refs document lists the product,
  but the collection's `harvest_date_time` is strictly earlier than the product's. The product was
  re-harvested (replaced) after the collection was swept, which wiped its ancestry. The sweeper does not
  revisit stamped collections, so nothing restores it. This is not a sweeper defect.
- **Check:**
  1. `show_doc "${LIDVID}"`: no stamp or refs fields (or no `ancestor_refs`), and note its harvest time.
  2. `show_doc "${COLLECTION_LIDVID}"`: stamp is the current version, `ancestor_refs` non-empty, and an
     earlier harvest time than the product.
  3. `show_refs "${LIDVID}"`: a hit whose `collection_lidvid` equals `COLLECTION_LIDVID`.
  4. `api_member_hits "${COLLECTION_LIDVID}" "${LIDVID}"` returns `0`: the API omits the product.
- **Action:** re-harvest the collection so it is no longer stamped, then let the sweeper run.

### `inventory_version_mismatch` (anomalous)

- **Meaning:** the collection is stamped and no `registry-refs` document lists the product's LIDVID, but a
  refs document lists the same product LID under a different version. Refs are written from the collection
  inventory when the collection is harvested, so the inventory names a version of the product (for example
  `::14.0`) other than the one the registry holds (`::13.1`). The sweeper selects only the listed LIDVIDs, so
  the registered version is never processed. This rule applies whatever the product's age.
- **Check:**
  1. `show_refs "${LIDVID}"` returns no hits.
  2. Search refs by LID, which should return a hit:

     ```bash
     PRODUCT_LID="${LIDVID%%::*}"
     body="$(jq -n --arg lid "${PRODUCT_LID}" '{size: 1, query: {term: {product_lid: $lid}}, _source: ["collection_lidvid", "batch_id"]}')"
     registry_query "/*-registry-refs/_search" "${body}" | jq '.hits'
     ```

  3. Run `audit_collection.py "${COLLECTION_LIDVID}" --diff`. The product's LIDVID is in
     `diff_registry_not_inventory.csv` and the version the inventory lists is in
     `diff_inventory_not_registry.csv`.
- **Action:** load the product version the inventory lists. The version the registry holds is then
  superseded and leaves the audit. Re-harvesting the collection does not help, because the refs already
  match the inventory.
- **Is the load still running?** Run `audit_collection.py "${COLLECTION_LIDVID}" --load-status`. It takes the
  newest harvest time among products that are in the inventory *and* in the registry. A recent time means the
  node is still loading the new version; an old time means the load stopped part-way and the node needs to
  continue or redo it. Registry products the inventory does not list are ignored, so the old versions cannot
  make a stalled load look active.

### `bare_lid_in_inventory` (anomalous)

The collection's inventory lists the product by LID, without a version. Harvest records that as `product_lid` in
the `registry-refs` document and leaves `product_lidvid` out, and the ancestry sweeper follows only
`product_lidvid`, so it never reaches the product. Re-harvesting writes the same refs. The inventory has to list
LIDVIDs, or the sweepers have to follow LID references; the audit assigns it to the sweepers team because the
sweepers are the part that does not follow a valid PDS4 inventory.

**Check.** Download the inventory (the collection's `ops:Data_File_Info/ops:file_ref`) and look at the row for the
product: a row such as `P,urn:nasa:pds:b:c:p` with no `::version`. Then `show_refs` for the collection shows a
document with `product_lid` and no `product_lidvid`.

### `sweeper_miss` (anomalous)

- **Meaning:** the collection is stamped and a refs document lists the product, and the collection was
  harvested at the same time as or after the product (or a harvest time is unknown), yet the product has
  no ancestry. Nothing in the registry data explains it; the ordering rules out a later overwrite.
- **Check:** the same four steps as `reloaded_after_collection`. Here step 2 shows a collection harvest
  time greater than or equal to the product's. Also check the refs hit's `batch_id`: if refs were added
  to the collection after the sweeper processed it, they were never swept (the sweeper marks the
  collection complete once).
- **Action:** inspect the sweeper run for the collection. Compare the collection's refs coverage in
  `collections.csv`. Report with the evidence from these queries.

### `refs_missing_pending` / `refs_missing`

- **Meaning:** the collection is stamped but no `registry-refs` document lists the product. The sweeper
  only selects products through refs, so it can never process this product. Pending when harvested
  within `--product-grace-days`.
- **Check:** `show_refs "${LIDVID}"` returns no hits across all nodes. If you ran the audit with
  `--node`, only that node's refs were searched, so confirm with `show_refs`, which searches every
  node's refs.
- **Meaning, continued:** no refs document lists the product's LID under any version either. Refs are written from
  the collection inventory when the collection is harvested, so they can be older than the inventory the
  data provider serves today. The audit reads the collection's current inventory (the URL on the
  collection's registry document) and reports `refs_missing` when the inventory **lists** the product, which
  means the refs are stale. When the inventory does not list it, the verdict is
  `not_in_collection_inventory`; when it lists another version, `inventory_version_mismatch`. With
  `--no-inventory`, or when the inventory cannot be downloaded, every such product is `refs_missing`.
- **Action:** re-harvest the collection from its current label and inventory so its refs are regenerated
  (`scripts/download_collection_files.py` fetches them). To confirm one product, run
  `audit_collection.py "${COLLECTION_LIDVID}" --diff`.

### `not_in_collection_inventory` (anomalous)

- **Meaning:** the product is registered under the collection's LID, but the collection's current inventory
  does not list it under any version (not by LIDVID, not as another version of the LID, not as a bare LID),
  and no refs document lists it. The sweeper selects non-aggregates only through the collection's refs, so
  it can never give this product that collection as an ancestor. Either the provider dropped the product from
  the inventory or it is a leftover, for example an earlier set of products registered under the same
  collection LID. It is anomalous after `--product-grace-days`.
- **Check:**
  1. `show_refs "${LIDVID}"` returns no hits, and the by-LID search from `inventory_version_mismatch` also
     returns none.
  2. Run `audit_collection.py "${COLLECTION_LIDVID}" --diff`. The product's LIDVID is in
     `diff_registry_not_inventory.csv` and no inventory entry has its LID.
- **Action:** the node decides whether the product belongs in the inventory (then update the inventory and
  re-harvest the collection) or should be removed from the registry. Re-harvesting alone and loading more
  products do not fix it.

### `stale_stamp` (anomalous)

- **Meaning:** the product has a stamp other than the current version, while its collection is already
  stamped with the current version. The collection will not be revisited, so the product is not
  reprocessed.
- **Check:** `show_doc "${LIDVID}"` shows an older stamp; `show_doc "${COLLECTION_LIDVID}"` shows the
  current stamp.
- **Action:** a re-sweep of the collection is needed.

## Collection-level outputs

`collections.csv` includes `coverage_note`, which compares three counts for each anomalous collection:

| Note | Technical meaning |
|---|---|
| `refs missing for N members (refs never written)` | The `registry-refs` documents for the collection list fewer `product_lidvid` values than there are API-visible members found by LID prefix |
| `refs complete but N members not stamped (sweeper skipped them)` | Refs list at least as many products as there are members, but some members have no current stamp and refs |
| `ok` | Every member is accounted for |
| (empty) | Coverage was not computed: it is queried only for the `--max-coverage-collections` anomalous collections with the most affected products |

Counts: `refs_count` is a `value_count` of `product_lidvid` over the collection's refs documents.
`member_count` is a `lid` wildcard `<collection LID>:*` over API-visible products, so it can include
members of other versions of the collection. `stamped_member_count` additionally requires the current
stamp and `ancestor_refs`.

For a `stamped_empty_refs` collection, confirm with `show_doc "${COLLECTION_LIDVID}"` (current stamp,
no `ancestor_refs`) and check the referencing bundle's `/members` through the API, which should be empty.

## Regression checks

`--check` evaluates invariants on the finished run and sets the exit code: 0 when all hold, 1 on an error
(registry, credentials, unreadable baseline or history file), 2 when an invariant is violated. A run always
writes `metrics.json`; `--check` adds the result to `summary.md` under "Regression check".

`metrics.json` fields: `schema_version`, `run_time`, `ancestry_version`, `nodes`, `examined`, `expected`,
`anomalous`, `rules` (anomalous product count for every rule, zero when unused), `anomalous_collections`,
`superseded_anomalous_collections`, `empty_refs_with_bundle`, and `unmapped_superseded` (`null` when the mapping
was not checked).

| Invariant | Without `--baseline` | With `--baseline` |
|---|---|---|
| `no_anomalous_products` | Fails when `anomalous` is above zero | Not evaluated |
| `no_new_anomalies` | Not evaluated | Fails for a collection in the current or superseded anomalous lists that the baseline lacks, and for any rule whose count is above its baseline count. The rule counts also cover products with no collection, such as orphans |
| `no_empty_refs_collection_with_bundle` | Fails for any collection in `empty_refs_with_bundle` | Fails for collections not in the baseline's list |
| `superseded_by_mapped` | Fails for any index in `unmapped_superseded` | Same; the baseline is not used |

How each invariant relates to a known failure:

- A collection stamped with empty refs that has a bundle is the sweeper collection-stamping failure: the bundle's
  `/members` is empty. Re-harvest the collection, then re-run the sweepers.
- A load that has stalled shows up as `inventory_version_mismatch`: the collection's inventory lists a product
  version that the node has not loaded. A growing count against the baseline fails `no_new_anomalies`.
- `superseded_by_mapped` reads `GET /<node>-registry/_mapping` and looks for `ops:Provenance/ops:superseded_by`. A
  field missing from the mapping is returned in `_source` but cannot be searched, so the API cannot leave
  superseded products out of a bare-LID lookup. The check does not request the API; it tests the cause.

A baseline run is comparable only when its `nodes` and `ancestry_version` equal this run's; otherwise the audit
stops before it scans any product. A rule count that rises because a node loaded more data that is also
anomalous is reported as a regression, which is the intended behaviour. To accept a new known backlog, keep the
run's `metrics.json` as the next baseline.

`--history-csv FILE` appends `run_time`, `ancestry_version`, `nodes`, `examined`, `expected`, `anomalous`, one
column per rule, `anomalous_collections` (count) and `empty_refs_with_bundle` (count). The audit stops before
scanning when the file exists with other columns.

## Verifying the audit itself

1. **Candidate count.** For a node, an independently phrased count must equal the audit's "Candidates
   examined" (run the audit without `--max-products`):

   ```bash
   registry_query "/${NODE}-registry/_count" '{"query": {"bool": {
     "filter": [{"terms": {"ops:Tracking_Meta/ops:archive_status": ["archived", "certified"]}}],
     "must_not": [
       {"exists": {"field": "ops:Provenance/ops:superseded_by"}},
       {"terms": {"product_class": ["Product_Bundle", "Product_Collection"]}},
       {"bool": {"filter": [
         {"term": {"ops:Provenance/ops:registry_sweepers_ancestry_version": "7"}},
         {"exists": {"field": "ops:Provenance/ops:ancestor_refs"}}]}}]}}}' | jq '.count'
   ```

2. **Spot-check every rule.** Sample a few rows per rule with the snippet in "Reviewing the output",
   then walk each through the matching "Check" steps above.
3. **Compare with known reports.** The orphan counts in registry-sweepers #273 (collections stamped with
   empty refs, products with no stamp) should be reproducible per node as `stamped_empty_refs`
   collections and population A and B products.
4. **Public API symptom.** For any anomalous row, `api_member_hits` returning `0` for the product in its
   collection confirms the user-visible effect.

## Limitations

- The collection named for an orphaned product is a best guess. Compare the collection's inventory with the
  registry (`audit_collection.py --diff`) before acting on it.
- A refs listing counts as an inventory version mismatch only when it comes from the product's own collection
  version. Refs of an older collection version that name an older product version say nothing about the current
  one.
- `inventory_version_mismatch` can point either way: the registry may hold an older or a newer version than the
  inventory lists. The rationale says which.
- A product that already has ancestry naming an older collection version than the inventory's current one is not
  a candidate and is not examined (on IMG, the `mars2020_navcam_ops_mosaic` collection has about 35,000 of
  these). `audit_collection.py --diff` shows them.

- Only API-visible products are examined: not superseded, `archived` or `certified`.
- On the ATM registry index, `ops:Provenance/ops:superseded_by` is returned in a document's `_source` but cannot be
  searched: `exists`, `term` and `wildcard` queries on it match nothing. A query cannot exclude superseded
  products there, so the audit reads the field from each hit and drops superseded products itself. Counts taken
  with a server-side `_count` query, such as the `coverage_note` member counts, still include superseded
  products on that index.
- Harvest time stands in for processing time. A collection harvested after a product is assumed to have
  been swept after it; the registry does not record when ancestry ran.
- Superseded collection versions are loaded too, because their products stay API-visible. When refs list a
  product, its collection is the one the refs name. Otherwise the collection is chosen from the versions
  registered under the product's collection LID: the one whose version number equals the product's (a
  product `...::2.1` belongs to collection `...::2.1`) if exactly one does, else a current version over a
  superseded one, taking the latest-harvested when all are processed and otherwise the worst unprocessed
  one. The version-number match is a heuristic. The rationale names the collection used and says when it
  is superseded.
- Superseded collection versions are listed in `collections.csv` (`superseded_by` column) and marked
  "(superseded)" in the summary, but are left out of `anomalous_collections.txt` and of the stamped-with-
  empty-refs section: a superseded version is not re-harvested, and its bundle refers to the newer version.
- Partially wrong but non-empty `ancestor_refs` (for example a missing bundle) is not detected.
- With `--node`, refs lookups cover only the named nodes' refs indices.
- `coverage_note` compares counts, not identities: a collection whose refs list as many products as it has
  members can still have members that no refs document lists (a different product of the same count).
  The per-product `refs_missing` verdict is identity-based and is authoritative; use `show_refs` on a
  product to settle a disagreement.
- `--node` accepts an alias such as `atm`, while the `node` column reports the underlying index prefix
  (`temp-atm`).
- A stamped collection with empty refs and no bundle is reported as expected only because no bundle in
  the registry references it by `ref_lid_collection`. Review the data collections among them, since a
  bundle that has not been loaded yet looks the same as a collection nobody references.
