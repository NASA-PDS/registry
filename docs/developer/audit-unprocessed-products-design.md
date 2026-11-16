# Design: Unprocessed Product Audit

Script: `scripts/audit_unprocessed_products.py`

## Problem

The registry sweepers' ancestry sweeper writes `ops:Provenance/ops:ancestor_refs` and stamps
`ops:Provenance/ops:registry_sweepers_ancestry_version` on every product it processes. Products that
lack ancestry do not appear in `/members`, `/ancestors` and related API results, so the API looks
incomplete. Some of these products are simply waiting on the sweeper or on a parent collection that
is still loading. Others are genuinely broken. Today the only way to tell the difference is to
inspect products one at a time through OpenSearch (see registry-sweepers #273).

`audit_collection.py` answers "what is wrong with this one collection". This audit answers "which
products across the whole registry are missing ancestry, and why".

## Facts the design depends on

Taken from the ancestry sweeper source (`SWEEPERS_ANCESTRY_VERSION = 7`) and the #273 discussion.

- A processed product has `ops:Provenance/ops:registry_sweepers_ancestry_version` set and an
  `ops:Provenance/ops:ancestor_refs` key. The array can be empty, and `exists` treats an empty array
  as absent.
- Bundles and collections are selected for processing directly. A collection is pending when its
  stamp is missing or below the current version.
- **Non-aggregate products have no pending query of their own.** They are processed only when they
  appear in `product_lidvid` of a `<node>-registry-refs` document whose `collection_lidvid` is a
  pending collection. A product with no refs document is never touched.
- Once a collection is stamped it is never revisited. A product force-overwritten afterwards loses
  its ancestry and nothing repairs it. Refs added to a stamped collection later are never swept.
- A collection can be stamped with empty `ancestor_refs` (fixed going forward, but already-stamped
  collections are not reprocessed). Its bundle's `/members` then returns nothing.
- The version field is mapped as `keyword`, so range queries on it are lexicographic. Compare
  equality server-side and numerically client-side.
- The refs documents are read-only to the sweeper: `collection_lidvid`, `batch_id`,
  `product_lidvid` (array).
- Sweepers run per node, so `<node>-registry` joins with `<node>-registry-refs`.
- Ancestry has no timestamp. The only time signal is `ops:Harvest_Info/ops:harvest_date_time`.

## Scope

In scope: products that are **API-visible** (not superseded, `archive_status` of `archived` or
`certified`) and belong to one of three populations:

| Population | Meaning |
|---|---|
| A | No ancestry stamp |
| B | Stamped, but `ancestor_refs` empty or absent |
| C | Stamped with a version other than the current one (stale) |

Out of scope: superseded and staged products, and partially wrong but non-empty `ancestor_refs`
(for example a missing bundle ref), which needs a per-product comparison against refs.

## Approach

The audit works per parent collection, not per product. Collection state is loaded once into memory
(thousands of documents), and the millions of candidate products are streamed past it.

### Phase 1: collections

Fetch every API-visible `Product_Collection` with `lidvid`, `lid`, node, stamp, `ancestor_refs`
and harvest time. Classify each:

| State | Condition |
|---|---|
| `processed` | stamp is current and `ancestor_refs` non-empty |
| `stamped_empty_refs` | stamp is current and `ancestor_refs` empty |
| `unprocessed_pending` | stamp missing or stale, harvested within `--collection-grace-days` (default 1) |
| `unprocessed_overdue` | stamp missing or stale, harvested longer ago than that |

For `stamped_empty_refs`, look up bundles that reference the collection LID. A collection with a
bundle is an anomaly (the bundle's `/members` is empty). A collection with no bundle is expected.

### Phase 2: candidate products

Stream every API-visible non-aggregate product that is in population A, B or C, using `search_after`
(10,000 per page; the AOSS result window is capped at 10,000). For each product:

1. Derive the parent collection LID from the product LID. A product LID has the form
   `urn:<agency>:<archive>:<bundle>:<collection>:<product>`; the first five segments are the
   collection LID. Product classes that never belong to a collection (for example `Product_Service`,
   `Product_Context`) are marked `no_parent_by_design` and skipped from further analysis.
2. Look up the collection in the phase 1 map. All products that share a collection reuse the result,
   so once a collection is found to be missing, the products that follow it are classified without
   further lookups.
3. If the collection is stamped, confirm membership in `<node>-registry-refs` with batched `terms`
   queries on `product_lidvid` (about 1,000 per request). This is only needed for products whose
   collection was processed, which should be a small fraction of the candidates. Refs give the exact
   `collection_lidvid`; the derived LID is used only when no refs document exists.
4. Assign a rule (below).

### Rules

Each product gets exactly one rule, a severity (`expected` or `anomalous`) and a one-line rationale
that is written to the CSV.

| Rule | Condition | Severity |
|---|---|---|
| `no_parent_by_design` | Product class is never a collection member | expected |
| `collection_not_loaded_pending` | No API-visible collection for the derived LID; product harvested within `--product-grace-days` (default 7) | expected |
| `collection_not_loaded_overdue` | Same, but product harvested longer ago than that | anomalous |
| `collection_pending` | Collection unprocessed, within collection grace | expected |
| `collection_overdue` | Collection unprocessed beyond collection grace. Root cause is the collection, not the product | anomalous |
| `reloaded_after_collection` | Collection processed, product listed in refs, collection harvested **before** the product. The product was overwritten after the collection was swept | anomalous, fixable by re-harvesting the collection |
| `inventory_version_mismatch` | Collection processed, no refs document lists the product's LIDVID, but refs (found with a `terms` query on `product_lid`) or the collection's current inventory list the same product LID under another version. The inventory names a different version than the registry holds | anomalous, fixed by loading the listed version |
| `not_in_collection_inventory` | Collection processed, no refs document lists the product, and the collection's current inventory lists it under no version. The inventory is read from the URL on the collection's registry document, only for collections with such products, and only after the cheaper refs checks | anomalous after the product grace period; the node adds it to the inventory or removes it |
| `sweeper_miss` | Collection processed, product listed in refs, collection harvested at or after the product. Nothing explains the gap | anomalous |
| `refs_missing` | Collection exists but no refs document lists the product | anomalous after product grace, expected before |
| `stale_stamp` | Product stamp is below the current version and its collection is processed | anomalous |

`reloaded_after_collection` is flagged `anomalous` because the product is still missing ancestry and
will stay that way, but its rationale says no sweeper bug is implied.

## Extra diagnostics

- **Stamped collections with empty refs.** The collection list from phase 1 with bundle cross-check.
- **Refs coverage per anomalous collection.** For each collection that roots anomalies, compare three
  numbers: product LIDVIDs in refs (`value_count` of `product_lidvid`), API-visible members by LID
  prefix, and members that carry ancestry. Refs below members means the refs were never written;
  refs equal to members with members unstamped means the sweeper skipped them.
- **Orphans.** Products whose derived collection LID has no collection document, listed separately
  from sweeper bugs.
- **Diff against a previous run.** `--previous-csv` reports products that are new, resolved and
  persisting, keyed on `lidvid` and `rule`.

## Outputs

All written to `--output-dir`. None are meant to be committed.

| File | Content |
|---|---|
| `unprocessed_products.csv` | One row per product (see columns below) |
| `collections.csv` | One row per collection with state, counts and refs coverage |
| `summary.md` | The report, also printed to the terminal |
| `anomalous_collections.txt` | Collection LIDVIDs with anomalies, usable with `audit_collection.py --from-file` |

`unprocessed_products.csv` columns: `node`, `lidvid`, `product_class`, `population`, `stamp_version`,
`has_ancestor_refs`, `harvest_date_time`, `harvest_age_days`, `bundle_lid`, `collection_lidvid`,
`collection_state`, `collection_harvest_date_time`, `in_refs`, `rule`, `severity`, `rationale`.

`summary.md` sections, in order:

1. Headline: candidates examined, expected, anomalous, run parameters (thresholds, ancestry version, node filter).
2. Anomalies grouped by rule, then node, with counts.
3. Anomalous collections: node, bundle, collection LIDVID, state, harvest time, affected product count, refs coverage.
4. Stamped collections with empty refs and their bundles.
5. Expected-pending counts by node (the number that should shrink on its own).
6. Orphans.
7. Breakdown by product class and by age bucket.
8. Diff against the previous run, when supplied.
9. For each rule that appears, a short "what this means / what to do" note.

## CLI

```
audit_unprocessed_products.py --output-dir DIR
    [--node NODE ...]            limit to <node>-registry and <node>-registry-refs
    [--collection-grace-days N]  default 1
    [--product-grace-days N]     default 7
    [--ancestry-version N]       default 7
    [--previous-csv FILE]
    [--max-products N]           stop after N candidates (dry runs)
    [--timeout N] [--log-level LEVEL]
```

Credentials come from the shell environment, the same variables and loading as `audit_collection.py`.
The audit only issues read queries (`_search`, `_count`). It uses OpenSearch directly because the
public API does not expose `registry-refs`.

## Cost

About 3 million candidates at 10,000 per page is roughly 300 search requests, plus collection and
refs lookups. The CSV is expected to reach hundreds of MB, so rows are streamed to disk rather than
held in memory. Only collection state and per-collection counters stay in memory.

## Regression check

`--check` turns a run into a pass/fail test: it evaluates invariants on the run's `metrics.json` and exits 2
when one is violated (see the reference guide for the invariants). With `--baseline` (an earlier
`metrics.json`) it fails only for anomalies that are new, so a backlog the nodes are working through does not
fail every run while a new problem does. `--history-csv` appends one row per run for trend charts.

### Scheduled run (proposal)

Run the check on a schedule from a host that has the registry credentials, which the repository's
GitHub-hosted runners do not have. Two cadences fit the cost of a run:

| Cadence | Command options | Why |
|---|---|---|
| Nightly | `--check --baseline <last accepted metrics.json> --no-inventory --history-csv <history.csv>` | Skips the slow inventory downloads; products in no refs document are reported as `refs_missing` instead of being split into version mismatches and unlisted products. Catches new unprocessed collections, empty-refs collections and the mapping canary |
| Weekly | `--check --baseline <last accepted metrics.json> --inventory-cache-dir <dir> --history-csv <history.csv>` | Full classification. A kept inventory is never refreshed, so clear the cache directory before the run |

Constraints that shape the job:

- A full run on the ATM node takes over an hour. Inventory downloads from the data providers are slow, which is
  why they are skippable and cacheable.
- The login credentials expire after about an hour; the audit renews them itself.
- A `--no-inventory` baseline and a full-run baseline classify the same products under different rules, so the
  two cadences need separate baseline files.
- Accepting a backlog means promoting that run's `metrics.json` to the baseline; the job does not do this by
  itself.
- A violated invariant should notify the owners of the failing collections (the nodes) rather than only fail
  the job; `summary.md` names the collections.

Open: where the job runs, who owns the credentials it uses, and how the exit code reaches the people who act on
it.

## Testing

- Unit tests for LID parsing, collection state, rule assignment (one case per rule, boundary cases on
  the grace periods and on equal harvest times), query builders and report rendering, with
  OpenSearch responses mocked.
- A read-only dry run against one node with `--node` and `--max-products` before any full run.

## Open questions

- **Multiple collection versions.** A derived collection LID can match several versions, including
  superseded ones, whose products stay API-visible. Refs decide when they list the product; otherwise
  the version whose number equals the product's is used if exactly one does (a heuristic), else a
  current version over a superseded one.
- **Classes with no parent.** The list of product classes treated as `no_parent_by_design` needs
  confirming against real data.

## Index handling

- `*-registry` also matches the legacy Solr mirror (`en-legacy-registry`), and AOSS rejects an
  exclusion in the index path. The script queries `*-registry` and skips the legacy index by name when
  discovering nodes and reading hits.
- Nodes are discovered with a size-0 terms aggregation on `_index`. AOSS reports each value as
  `<account>::<collection id>::SEARCH::<index name>:<n>`, so the script extracts the index name before
  deriving the node (the prefix before `-registry`).
- Products are scanned one node index at a time, which avoids `_id` ties across indices when paging with
  `search_after`.
