# Unprocessed product audit

Run time: 2026-11-19T04:03:41+00:00
Nodes: sbnpsi

- Candidates examined: **30**
- Expected (should resolve on their own): **29**
- Anomalous (need attention): **1**
- Not API-visible (staged etc.) without ancestry, not counted above: 268,696 (staged 268,696)

## What needs to happen

**Needs attention: 1 product for the node.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: No collection with the identifier these products belong to is in the registry | 1 | 1 | Load the collection, or correct the product identifiers |
| No action | **Waiting**: Product classes that never belong to a collection | 29 | - | None |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Waiting**: loaded recently; expected to resolve by itself.

Who fixes what:

- **Node**: the node's data does not line up (a collection is not loaded, a product is at the wrong version or not in the collection's inventory), or the inventory lists the product but the registry's refs do not, so the node re-harvests that collection to rewrite them.
- **No action**: loaded recently; expected to resolve by itself.

## Anomalies by rule

| Rule | Products |
|---|---|
| collection_not_loaded_overdue | 1 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| collection_not_loaded_overdue | sbnpsi | 1 |

## Orphans

1 products belong to 1 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:nasa:pds:system_bundle:xml_schema | sbnpsi | 1 | 0 | 1 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Context | 29 | 0 | 29 |
| Product_XML_Schema | 0 | 1 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| >30d | 29 | 1 | 30 |

## How this maps to the orphan repair report

The ancestry orphan repair dry run prints products examined, repairable (a refs document lists the product under a collection in the registry) and unresolved (no refs document lists it, or only under a collection that is not in the registry).

- The repair examines the 30 audit candidates plus the 268,696 products that are not API-visible, because it does not filter on archive status.
- The repair has no grace period, so waiting (`*_pending`) products are counted too.
- The audit counts any stamp other than the current version, the repair only a stamp below it.

| Audit rule | Products | Repair bucket |
|---|---|---|
| collection_not_loaded_overdue | 1 | unresolved unless a refs document lists it under a collection in the registry |
| no_parent_by_design | 29 | unresolved unless a refs document lists it under a collection in the registry |
| not API-visible (not audited) | 268,696 | repairable if a refs document lists it, else unresolved |
| **all (the repair's products examined)** | **268,726** |  |

## What each rule means

- **no_parent_by_design** (29 products): These product classes never belong to a collection, so they never receive ancestry. No action is needed.
- **collection_not_loaded_overdue** (1 products): The parent collection is still not in the registry (or is not API-visible) long after the product was harvested. Check whether the collection failed to load, is staged or superseded, or whether the product LID does not follow the bundle:collection:product pattern.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: sbnpsi
- Node filter: sbnpsi
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated against the baseline of 2026-11-16T22:23:53+00:00.

**PASS** - every invariant holds.
