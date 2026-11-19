# Unprocessed product audit

Run time: 2026-11-19T04:02:42+00:00
Nodes: en

- Candidates examined: **1,839**
- Expected (should resolve on their own): **1,834**
- Anomalous (need attention): **5**
- Not API-visible (staged etc.) without ancestry, not counted above: 31 (staged 31)

## What needs to happen

**Needs attention: 5 products for the node.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 3 | 3 | Load the version the inventory lists, or correct the inventory |
| Node | **Orphaned**: The collection's inventory does not list these products under any version | 2 | 1 | Add them to the inventory, or remove the products from the registry |
| No action | **Waiting**: Not in the registry's refs yet | 1,272 | - | None; re-check later |
| No action | **Waiting**: Waiting for the collection to be loaded | 561 | - | None; re-check later |
| No action | **Waiting**: Product classes that never belong to a collection | 1 | - | None |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Waiting**: loaded recently; expected to resolve by itself.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory), or the collection has to be re-harvested by the node so that the registry's refs are rewritten from its inventory; EN then runs the sweepers.
- **No action**: loaded recently; expected to resolve by itself.

## Anomalies by rule

| Rule | Products |
|---|---|
| inventory_version_mismatch | 3 |
| not_in_collection_inventory | 2 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| inventory_version_mismatch | en | 3 |
| not_in_collection_inventory | en | 2 |

## Anomalous collections

3 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| en | urn:nasa:pds:system_bundle | urn:nasa:pds:system_bundle:document_policy::1.0 | stamped_empty_refs | 2026-11-17T02:48:25+00:00 | 3 | refs complete but 3 members not stamped (sweeper skipped them) |
| en | urn:nasa:pds:context, urn:nasa:pds:context::1.6 | urn:nasa:pds:context:miscellaneous::1.1 | processed | 2026-07-07T19:15:01+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| en | urn:nasa:pds:misc, urn:nasa:pds:misc::1.0 | urn:nasa:pds:misc:document_cassini::1.0 | processed | 2026-11-17T02:48:24+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |

## Stamped collections with empty refs

2 collections are stamped with the current version but have no ancestor refs. 0 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 2 have no bundle and are expected.

## Expected pending, by node

1,833 products are waiting on the sweeper or a loading collection. This is the number that should shrink on its own.

| Node | collection_not_loaded_pending | collection_pending | refs_missing_pending | Total |
|---|---|---|---|---|
| en | 561 | 0 | 1,272 | 1,833 |

## Orphans

561 products belong to 4 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:nasa:pds:system_bundle:xml_schema | en | 0 | 554 | 554 |
| urn:jaxa:darts:system_bundle:xml_schema | en | 0 | 3 | 3 |
| urn:kari:kpds:system_bundle:xml_schema | en | 0 | 3 | 3 |
| (unknown) | en | 0 | 1 | 1 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_AIP | 636 | 0 | 636 |
| Product_SIP_Deep_Archive | 636 | 0 | 636 |
| Product_XML_Schema | 561 | 0 | 561 |
| Product_Document | 0 | 4 | 4 |
| Product_Ancillary | 0 | 1 | 1 |
| Product_Context | 1 | 0 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| 1-7d | 1,833 | 2 | 1,835 |
| >30d | 1 | 3 | 4 |

## How this maps to the orphan repair report

The ancestry orphan repair dry run prints products examined, repairable (a refs document lists the product under a collection in the registry) and unresolved (no refs document lists it, or only under a collection that is not in the registry).

- The repair examines the 1,839 audit candidates plus the 31 products that are not API-visible, because it does not filter on archive status.
- The repair has no grace period, so waiting (`*_pending`) products are counted too.
- The audit counts any stamp other than the current version, the repair only a stamp below it.

| Audit rule | Products | Repair bucket |
|---|---|---|
| refs_missing_pending | 1,272 | unresolved |
| inventory_version_mismatch | 3 | unresolved |
| not_in_collection_inventory | 2 | unresolved |
| collection_not_loaded_pending | 561 | unresolved unless a refs document lists it under a collection in the registry |
| no_parent_by_design | 1 | unresolved unless a refs document lists it under a collection in the registry |
| not API-visible (not audited) | 31 | repairable if a refs document lists it, else unresolved |
| **all (the repair's products examined)** | **1,870** |  |

## What each rule means

- **no_parent_by_design** (1 products): These product classes never belong to a collection, so they never receive ancestry. No action is needed.
- **collection_not_loaded_pending** (561 products): The parent collection is not in the registry yet and the product was harvested recently. This is expected to resolve once the collection is loaded and swept.
- **inventory_version_mismatch** (3 products): The collection's inventory (as recorded in registry-refs) lists this product at a different version than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the collection will not help: load the product version the inventory lists, after which the registered version is superseded. Confirm with audit_collection.py --diff.
- **not_in_collection_inventory** (2 products): The product is registered under this collection's LID, but the collection's current inventory does not list it under any version, so the sweeper can never give it this collection as an ancestor. The provider may have dropped it from the inventory or it may be a leftover. The node should decide whether it belongs in the inventory or should be removed from the registry; re-harvesting or loading more products will not fix it.
- **refs_missing_pending** (1,272 products): The collection is processed but no registry-refs document lists the product, and the product was harvested within the grace period, so a load may still be running. Re-check after the grace period; if the product is still missing, it is classified like refs_missing.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: en
- Node filter: en
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated against the baseline of 2026-11-16T22:23:46+00:00.

**FAIL** - 1 invariant(s) violated.

- `no_new_anomalies`: 1 collections newly root anomalous products; 1 rules have more anomalous products than the baseline of 2026-11-16T22:23:46+00:00
  - urn:nasa:pds:misc:document_cassini::1.0
  - inventory_version_mismatch: 1 -> 3
