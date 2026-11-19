# Unprocessed product audit

Run time: 2026-11-19T04:02:42+00:00
Nodes: img

- Candidates examined: **516**
- Expected (should resolve on their own): **0**
- Anomalous (need attention): **516**
- Not API-visible (staged etc.) without ancestry, not counted above: 1,645 (staged 1,645)

## What needs to happen

**Needs attention: 516 products for the node.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 516 | 1 | Load the version the inventory lists, or correct the inventory |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory), or the collection has to be re-harvested by the node so that the registry's refs are rewritten from its inventory; EN then runs the sweepers.

## Anomalies by rule

| Rule | Products |
|---|---|
| inventory_version_mismatch | 516 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| inventory_version_mismatch | img | 516 |

## Anomalous collections

1 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| img | urn:nasa:pds:mars2020_navcam_ops_mosaic::13.0, urn:nasa:pds:mars2020_navcam_ops_mosaic::1.1, urn:nasa:pds:mars2020_navcam_ops_mosaic::1.0 (+2 more) | urn:nasa:pds:mars2020_navcam_ops_mosaic:data::16.0 | processed | 2026-08-14T01:19:19+00:00 | 516 | refs complete but 516 members not stamped (sweeper skipped them) |

## Stamped collections with empty refs

30 collections are stamped with the current version but have no ancestor refs. 0 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 30 have no bundle and are expected.

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_File_Text | 0 | 516 | 516 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| >30d | 0 | 516 | 516 |

## How this maps to the orphan repair report

The ancestry orphan repair dry run prints products examined, repairable (a refs document lists the product under a collection in the registry) and unresolved (no refs document lists it, or only under a collection that is not in the registry).

- The repair examines the 516 audit candidates plus the 1,645 products that are not API-visible, because it does not filter on archive status.
- The repair has no grace period, so waiting (`*_pending`) products are counted too.
- The audit counts any stamp other than the current version, the repair only a stamp below it.

| Audit rule | Products | Repair bucket |
|---|---|---|
| inventory_version_mismatch | 516 | unresolved |
| not API-visible (not audited) | 1,645 | repairable if a refs document lists it, else unresolved |
| **all (the repair's products examined)** | **2,161** |  |

## What each rule means

- **inventory_version_mismatch** (516 products): The collection's inventory (as recorded in registry-refs) lists this product at a different version than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the collection will not help: load the product version the inventory lists, after which the registered version is superseded. Confirm with audit_collection.py --diff.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: img
- Node filter: img
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated against the baseline of 2026-11-16T22:23:49+00:00.

**PASS** - every invariant holds.
