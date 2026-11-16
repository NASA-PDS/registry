# Unprocessed product audit

Run time: 2026-11-16T22:23:47+00:00
Nodes: geo

- Candidates examined: **1,373**
- Expected (should resolve on their own): **0**
- Anomalous (need attention): **1,373**

## What needs to happen

**Needs attention: 1,322 for node; 4 for registry operations; 49 for sweepers team.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 1,152 | 3 | Load the version the inventory lists, or correct the inventory |
| Node | **Orphaned**: The collection's inventory does not list these products under any version | 168 | 1 | Add them to the inventory, or remove the products from the registry |
| Node | **Orphaned**: No collection with the identifier these products belong to is in the registry | 2 | 2 | Load the collection, or correct the product identifiers |
| Registry operations | **Not processed**: Linked to their collection, but processed by an older sweepers version while the collection is on the current one, so the sweepers do not go back | 2 | 1 | Re-harvest the collection, then run the sweepers |
| Registry operations | **Not processed**: The collection is marked processed but has no link to its bundle, so the bundle does not list it as a member | - | 2 | Re-harvest the collection, then run the sweepers (the sweepers bug that caused this is fixed in registry-sweepers PR #286) |
| Sweepers team | **Orphaned**: The collection's inventory lists these products by LID without a version, which the sweepers do not follow | 49 | 11 | Re-harvesting does not help. The node lists LIDVIDs in the inventory, or the sweepers support LID references |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Not processed**: the registry's refs list the product, so its collection is confirmed, but the sweepers never gave it ancestry.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory); only the node can fix it.
- **Registry operations**: the node's data is fine and the registry's own processing missed it; fixed by re-harvesting the collection and running the sweepers.
- **Sweepers team**: everything looks right but the sweepers cannot or do not follow it; a software gap, possibly worked around by the node.

## Anomalies by rule

| Rule | Products |
|---|---|
| collection_not_loaded_overdue | 2 |
| inventory_version_mismatch | 1,152 |
| not_in_collection_inventory | 168 |
| bare_lid_in_inventory | 49 |
| stale_stamp | 2 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| collection_not_loaded_overdue | geo | 2 |
| inventory_version_mismatch | geo | 1,152 |
| not_in_collection_inventory | geo | 168 |
| bare_lid_in_inventory | geo | 49 |
| stale_stamp | geo | 2 |

## Anomalous collections

14 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| geo | urn:nasa:pds:mars2020_mission::3.0, urn:nasa:pds:mars2020_mission, urn:nasa:pds:mars2020_mission::1.0 (+2 more) | urn:nasa:pds:mars2020_mission:calibration_camera::1.1 | processed | 2026-09-03T19:25:12+00:00 | 1,295 | refs missing for 168 members (refs never written) |
| geo | urn:nasa:pds:mars2020_mission::3.0, urn:nasa:pds:mars2020_mission, urn:nasa:pds:mars2020_mission::1.0 (+2 more) | urn:nasa:pds:mars2020_mission:miscellaneous::1.1 | processed | 2026-09-03T19:25:17+00:00 | 23 | refs complete but 23 members not stamped (sweeper skipped them) |
| geo | urn:nasa:pds:mess_grs_derived, urn:nasa:pds:mess_grs_derived::1.0 | urn:nasa:pds:mess_grs_derived:document::1.0 | processed | 2024-11-26T04:08:33+00:00 | 8 | refs missing for 8 members (refs never written) |
| geo | urn:nasa:pds:mess_rs_derived::3.0, urn:nasa:pds:mess_rs_derived | urn:nasa:pds:mess_rs_derived:document::1.0 | processed | 2024-11-26T15:24:36+00:00 | 6 | refs missing for 6 members (refs never written) |
| geo | urn:nasa:pds:mess_mla_calibrated, urn:nasa:pds:mess_mla_calibrated::1.0 | urn:nasa:pds:mess_mla_calibrated:document::1.0 | processed | 2024-11-26T04:55:32+00:00 | 5 | refs missing for 5 members (refs never written) |
| geo | urn:nasa:pds:mess_mla_derived::1.0, urn:nasa:pds:mess_mla_derived | urn:nasa:pds:mess_mla_derived:document::1.0 | processed | 2024-11-11T21:39:42+00:00 | 5 | refs missing for 5 members (refs never written) |
| geo | urn:nasa:pds:mess_ns_derived::1.0, urn:nasa:pds:mess_ns_derived | urn:nasa:pds:mess_ns_derived:document::1.0 | processed | 2024-11-26T04:05:13+00:00 | 5 | refs missing for 5 members (refs never written) |
| geo | urn:nasa:pds:mess_xrs_derived::1.0, urn:nasa:pds:mess_xrs_derived | urn:nasa:pds:mess_xrs_derived:document::1.0 | processed | 2024-11-15T15:35:52+00:00 | 5 | refs missing for 5 members (refs never written) |
| geo | urn:nasa:pds:mars2020_mission::4.0 | urn:nasa:pds:mars2020_mission:document_camera::16.0 | stamped_empty_refs | 2026-11-06T21:46:03+00:00 | 4 | refs complete but 4 members not stamped (sweeper skipped them) |
| geo | urn:nasa:pds:mess_grs_raw::1.0, urn:nasa:pds:mess_grs_raw | urn:nasa:pds:mess_grs_raw:document::1.0 | processed | 2024-11-25T22:33:41+00:00 | 3 | refs missing for 3 members (refs never written) |
| geo | urn:nasa:pds:mess_mla_raw, urn:nasa:pds:mess_mla_raw::1.0 | urn:nasa:pds:mess_mla_raw:document::1.0 | processed | 2024-11-25T23:17:59+00:00 | 3 | refs missing for 3 members (refs never written) |
| geo | urn:nasa:pds:mess_ns_raw::1.0, urn:nasa:pds:mess_ns_raw | urn:nasa:pds:mess_ns_raw:document::1.0 | processed | 2024-11-26T04:04:30+00:00 | 3 | refs missing for 3 members (refs never written) |
| geo | urn:nasa:pds:mess_xrs_calibrated, urn:nasa:pds:mess_xrs_calibrated::1.0 | urn:nasa:pds:mess_xrs_calibrated:document::1.0 | processed | 2024-11-25T22:32:02+00:00 | 3 | refs missing for 3 members (refs never written) |
| geo | urn:nasa:pds:mess_xrs_raw, urn:nasa:pds:mess_xrs_raw::1.0 | urn:nasa:pds:mess_xrs_raw:document::1.0 | processed | 2024-11-25T22:32:31+00:00 | 3 | refs missing for 3 members (refs never written) |

## Stamped collections with empty refs

2 collections are stamped with the current version but have no ancestor refs. 2 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 0 have no bundle and are expected.

| Node | Bundle(s) | Collection | Harvested |
|---|---|---|---|
| geo | urn:nasa:pds:mars2020_mission::4.0 | urn:nasa:pds:mars2020_mission:document_camera::16.0 | 2026-11-06T21:46:03+00:00 |
| geo | urn:nasa:pds:mars2020_rimfax::1.0 | urn:nasa:pds:mars2020_rimfax:document::16.0 | 2026-11-06T21:47:16+00:00 |

## Orphans

2 products belong to 2 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:nasa:pds:messenger:document | geo | 1 | 0 | 1 |
| urn:nasa:pds:system_bundle:xml_schema | geo | 1 | 0 | 1 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Ancillary | 0 | 847 | 847 |
| Product_File_Text | 0 | 448 | 448 |
| Product_Document | 0 | 77 | 77 |
| Product_XML_Schema | 0 | 1 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| >30d | 0 | 1,373 | 1,373 |

## What each rule means

- **collection_not_loaded_overdue** (2 products): The parent collection is still not in the registry (or is not API-visible) long after the product was harvested. Check whether the collection failed to load, is staged or superseded, or whether the product LID does not follow the bundle:collection:product pattern.
- **inventory_version_mismatch** (1,152 products): The collection's inventory (as recorded in registry-refs) lists this product at a different version than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the collection will not help: load the product version the inventory lists, after which the registered version is superseded. Confirm with audit_collection.py --diff.
- **not_in_collection_inventory** (168 products): The product is registered under this collection's LID, but the collection's current inventory does not list it under any version, so the sweeper can never give it this collection as an ancestor. The provider may have dropped it from the inventory or it may be a leftover. The node should decide whether it belongs in the inventory or should be removed from the registry; re-harvesting or loading more products will not fix it.
- **bare_lid_in_inventory** (49 products): The collection's inventory lists the product by LID only, without a version. Harvest records that as a product_lid in the registry-refs document, but the ancestry sweeper follows only product_lidvid, so it never reaches the product. Re-harvesting the collection writes the same refs; the inventory must list LIDVIDs, or the sweepers must follow LID references.
- **stale_stamp** (2 products): The product carries an ancestry stamp from an older sweeper version although its collection is already on the current version. The collection will not be revisited, so a re-sweep of the collection may be needed.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: geo
- Node filter: geo
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated with no baseline (any anomaly fails).

**FAIL** - 2 invariant(s) violated.

- `no_anomalous_products`: 1,373 products are anomalous
  - inventory_version_mismatch: 1,152
  - not_in_collection_inventory: 168
  - bare_lid_in_inventory: 49
  - collection_not_loaded_overdue: 2
  - stale_stamp: 2
- `no_empty_refs_collection_with_bundle`: 2 collections with a bundle are stamped with empty refs
  - urn:nasa:pds:mars2020_mission:document_camera::16.0
  - urn:nasa:pds:mars2020_rimfax:document::16.0
