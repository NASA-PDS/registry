# Unprocessed product audit

Run time: 2026-11-19T04:03:42+00:00
Nodes: sbnumd

- Candidates examined: **1**
- Expected (should resolve on their own): **0**
- Anomalous (need attention): **1**
- Not API-visible (staged etc.) without ancestry, not counted above: 0

## What needs to happen

**Needs attention: 1 product for the node.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory does not list these products under any version | 1 | 1 | Add them to the inventory, or remove the products from the registry |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.

Who fixes what:

- **Node**: the node's data does not line up (a collection is not loaded, a product is at the wrong version or not in the collection's inventory), or the inventory lists the product but the registry's refs do not, so the node re-harvests that collection to rewrite them.

## Anomalies by rule

| Rule | Products |
|---|---|
| not_in_collection_inventory | 1 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| not_in_collection_inventory | sbnumd | 1 |

## Anomalous collections

1 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| sbnumd | urn:nasa:pds:lucy.rss::2.0, urn:nasa:pds:lucy.rss::1.0, urn:nasa:pds:lucy.rss | urn:nasa:pds:lucy.rss:data_dinkinesh_trk234::1.0 | processed | 2026-10-27T16:16:07+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Document | 0 | 1 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| >30d | 0 | 1 | 1 |

## How this maps to the orphan repair report

The ancestry orphan repair dry run prints products examined, repairable (a refs document lists the product under a collection in the registry) and unresolved (no refs document lists it, or only under a collection that is not in the registry).

- The repair examines the 1 audit candidates plus the 0 products that are not API-visible, because it does not filter on archive status.
- The repair has no grace period, so waiting (`*_pending`) products are counted too.
- The audit counts any stamp other than the current version, the repair only a stamp below it.

| Audit rule | Products | Repair bucket |
|---|---|---|
| not_in_collection_inventory | 1 | unresolved |
| **all (the repair's products examined)** | **1** |  |

## What each rule means

- **not_in_collection_inventory** (1 products): The product is registered under this collection's LID, but the collection's current inventory does not list it under any version, so the sweeper can never give it this collection as an ancestor. The provider may have dropped it from the inventory or it may be a leftover. The node should decide whether it belongs in the inventory or should be removed from the registry; re-harvesting or loading more products will not fix it.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: sbnumd
- Node filter: sbnumd
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated against the baseline of 2026-11-16T22:23:53+00:00.

**PASS** - every invariant holds.
