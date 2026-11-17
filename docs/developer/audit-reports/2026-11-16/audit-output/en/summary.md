# Unprocessed product audit

Run time: 2026-11-16T22:23:46+00:00
Nodes: en

- Candidates examined: **793**
- Expected (should resolve on their own): **88**
- Anomalous (need attention): **705**

## What needs to happen

**Needs attention: 703 for node; 2 for needs a closer look.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory does not list these products under any version | 360 | 3 | Add them to the inventory, or remove the products from the registry |
| Node | **Orphaned**: No collection with the identifier these products belong to is in the registry | 342 | 4 | Load the collection, or correct the product identifiers |
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 1 | 1 | Load the version the inventory lists, or correct the inventory |
| Needs a closer look | **Orphaned**: No refs record lists these products and the collection inventory could not be used to say why | 2 | 1 | Re-run the audit with the inventories (not --no-inventory), or check the collection's inventory by hand |
| No action | **Waiting**: Product classes that never belong to a collection | 88 | - | None |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Waiting**: loaded recently; expected to resolve by itself.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory); only the node can fix it.
- **Needs a closer look**: the cause cannot be told apart because the collection inventory could not be used.
- **No action**: loaded recently; expected to resolve by itself.

2 products were not checked against the collection inventory (it was skipped with `--no-inventory` or could not be read).

## Anomalies by rule

| Rule | Products |
|---|---|
| collection_not_loaded_overdue | 342 |
| inventory_version_mismatch | 1 |
| not_in_collection_inventory | 360 |
| refs_missing | 2 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| collection_not_loaded_overdue | en | 342 |
| inventory_version_mismatch | en | 1 |
| not_in_collection_inventory | en | 360 |
| refs_missing | en | 2 |

## Anomalous collections

5 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

3 of them are superseded collection versions. Their products are still API-visible, but a superseded version is not re-harvested, so it is left out of `anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| en | urn:nasa:pds:system_bundle, urn:nasa:pds:system_bundle::1.0 | urn:nasa:pds:system_bundle:product_sip_deep_archive::1.0 | processed (superseded) | 2025-07-16T14:57:26+00:00 | 180 | refs missing for 591 members (refs never written) |
| en | urn:nasa:pds:system_bundle, urn:nasa:pds:system_bundle::1.0 | urn:nasa:pds:system_bundle:product_aip::1.0 | processed (superseded) | 2025-07-16T14:57:25+00:00 | 179 | refs missing for 591 members (refs never written) |
| en | urn:nasa:pds:system_bundle | urn:nasa:pds:system_bundle:document_policy::1.0 | stamped_empty_refs | 2025-03-05T05:35:25+00:00 | 2 | refs complete but 2 members not stamped (sweeper skipped them) |
| en | urn:nasa:pds:context, urn:nasa:pds:context::1.6 | urn:nasa:pds:context:miscellaneous::1.1 | processed | 2026-07-07T19:15:01+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| en | urn:nasa:pds:system_bundle, urn:nasa:pds:system_bundle::1.0 | urn:nasa:pds:system_bundle:product_aip::2.0 | processed (superseded) | 2025-07-16T14:57:46+00:00 | 1 | refs missing for 612 members (refs never written) |

## Stamped collections with empty refs

2 collections are stamped with the current version but have no ancestor refs. 0 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 2 have no bundle and are expected.

## Orphans

342 products belong to 4 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:nasa:pds:system_bundle:xml_schema | en | 336 | 0 | 336 |
| urn:jaxa:darts:system_bundle:xml_schema | en | 3 | 0 | 3 |
| urn:kari:kpds:system_bundle:xml_schema | en | 2 | 0 | 2 |
| (unknown) | en | 1 | 0 | 1 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_XML_Schema | 0 | 342 | 342 |
| Product_AIP | 0 | 180 | 180 |
| Product_SIP_Deep_Archive | 0 | 180 | 180 |
| Product_Service | 87 | 0 | 87 |
| Product_Document | 0 | 2 | 2 |
| Product_Ancillary | 0 | 1 | 1 |
| Product_Context | 1 | 0 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| >30d | 88 | 705 | 793 |

## What each rule means

- **no_parent_by_design** (88 products): These product classes never belong to a collection, so they never receive ancestry. No action is needed.
- **collection_not_loaded_overdue** (342 products): The parent collection is still not in the registry (or is not API-visible) long after the product was harvested. Check whether the collection failed to load, is staged or superseded, or whether the product LID does not follow the bundle:collection:product pattern.
- **inventory_version_mismatch** (1 products): The collection's inventory (as recorded in registry-refs) lists this product at a different version than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the collection will not help: load the product version the inventory lists, after which the registered version is superseded. Confirm with audit_collection.py --diff.
- **not_in_collection_inventory** (360 products): The product is registered under this collection's LID, but the collection's current inventory does not list it under any version, so the sweeper can never give it this collection as an ancestor. The provider may have dropped it from the inventory or it may be a leftover. The node should decide whether it belongs in the inventory or should be removed from the registry; re-harvesting or loading more products will not fix it.
- **refs_missing** (2 products): The collection is processed and has refs, but no registry-refs document lists this product, so the sweeper never selects it. Harvest writes a collection's refs from its inventory when the collection is harvested, so the inventory read at that time did not list the product, or the inventory has changed since, or the refs were not written. Read the collection's current inventory. If it lists this exact product, the refs are stale: registry operations re-harvest the collection from its current label and inventory, then run the sweepers. If it lists another version of the product or does not list it, the node's data does not line up and the node fixes it (the audit reports those as inventory_version_mismatch and not_in_collection_inventory when it can read the inventory). The collection named for the product is a best guess from its identifier.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: en
- Node filter: en
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated with no baseline (any anomaly fails).

**FAIL** - 1 invariant(s) violated.

- `no_anomalous_products`: 705 products are anomalous
  - not_in_collection_inventory: 360
  - collection_not_loaded_overdue: 342
  - refs_missing: 2
  - inventory_version_mismatch: 1
