# Unprocessed product audit

Run time: 2026-11-16T22:23:46+00:00
Nodes: atm

- Candidates examined: **2,784,370**
- Expected (should resolve on their own): **1,725**
- Anomalous (need attention): **2,782,645**

## What needs to happen

**Needs attention: 2,782,642 for the node; 1 for the sweepers team; 2 that need a closer look.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 2,765,640 | 16 | Load the version the inventory lists, or correct the inventory |
| Node | **Orphaned**: The collection's inventory does not list these products under any version | 16,960 | 8 | Add them to the inventory, or remove the products from the registry |
| Node | **Orphaned**: No collection with the identifier these products belong to is in the registry | 42 | 1 | Load the collection, or correct the product identifiers |
| Sweepers team | **Orphaned**: The collection's inventory lists these products by LID without a version, which the sweepers do not follow | 1 | 1 | Re-harvesting does not help. The node lists LIDVIDs in the inventory, or the sweepers support LID references |
| Needs a closer look | **Orphaned**: No refs record lists these products and the collection inventory could not be used to say why | 2 | 1 | Re-run the audit with the inventories (not --no-inventory), or check the collection's inventory by hand |
| No action | **Waiting**: Not in the registry's refs yet | 1,725 | - | None; re-check later |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Waiting**: loaded recently; expected to resolve by itself.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory), or the collection has to be re-harvested by the node so that the registry's refs are rewritten from its inventory; EN then runs the sweepers.
- **Sweepers team**: everything looks right but the sweepers cannot or do not follow it; a software gap, possibly worked around by the node.
- **Needs a closer look**: the cause cannot be told apart because the collection inventory could not be used.
- **No action**: loaded recently; expected to resolve by itself.

2 products were not checked against the collection inventory (it was skipped with `--no-inventory` or could not be read).

## Anomalies by rule

| Rule | Products |
|---|---|
| collection_not_loaded_overdue | 42 |
| inventory_version_mismatch | 2,765,640 |
| not_in_collection_inventory | 16,960 |
| bare_lid_in_inventory | 1 |
| refs_missing | 2 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| collection_not_loaded_overdue | temp-atm | 42 |
| inventory_version_mismatch | temp-atm | 2,765,640 |
| not_in_collection_inventory | temp-atm | 16,960 |
| bare_lid_in_inventory | temp-atm | 1 |
| refs_missing | temp-atm | 2 |

## Anomalous collections

23 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

2 of them are superseded collection versions. Their products are still API-visible, but a superseded version is not re-harvested, so it is left out of `anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| temp-atm | urn:nasa:pds:maven.iuvs.raw, urn:nasa:pds:maven.iuvs.raw::13.0 | urn:nasa:pds:maven.iuvs.raw:disk::13.0 | processed | 2026-11-15T21:50:06+00:00 | 662,080 | refs complete but 662080 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.raw, urn:nasa:pds:maven.iuvs.raw::13.0 | urn:nasa:pds:maven.iuvs.raw:limb::13.0 | processed | 2026-11-15T21:52:11+00:00 | 652,875 | refs complete but 652875 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.calibrated::13.0, urn:nasa:pds:maven.iuvs.calibrated | urn:nasa:pds:maven.iuvs.calibrated:disk::13.0 | processed | 2026-11-15T21:46:31+00:00 | 572,804 | refs complete but 572804 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.calibrated::13.0, urn:nasa:pds:maven.iuvs.calibrated | urn:nasa:pds:maven.iuvs.calibrated:limb::13.0 | processed | 2026-11-15T21:48:08+00:00 | 564,931 | refs complete but 564931 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.raw, urn:nasa:pds:maven.iuvs.raw::13.0 | urn:nasa:pds:maven.iuvs.raw:calibration::13.0 | processed | 2026-11-15T21:49:50+00:00 | 70,966 | refs complete but 70966 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.raw, urn:nasa:pds:maven.iuvs.raw::13.0 | urn:nasa:pds:maven.iuvs.raw:echelle::13.0 | processed | 2026-11-15T21:51:57+00:00 | 70,919 | refs missing for 1634 members (refs never written) |
| temp-atm | urn:nasa:pds:maven.iuvs.calibrated::13.0, urn:nasa:pds:maven.iuvs.calibrated | urn:nasa:pds:maven.iuvs.calibrated:calibration::13.0 | processed | 2026-11-15T21:46:18+00:00 | 62,437 | refs complete but 62437 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.calibrated::13.0, urn:nasa:pds:maven.iuvs.calibrated | urn:nasa:pds:maven.iuvs.calibrated:echelle::13.0 | processed | 2026-11-15T21:48:01+00:00 | 42,741 | refs complete but 42741 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.raw, urn:nasa:pds:maven.iuvs.raw::13.0 | urn:nasa:pds:maven.iuvs.raw:corona::13.0 | processed | 2026-11-15T21:50:01+00:00 | 28,542 | refs complete but 28542 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.calibrated::13.0, urn:nasa:pds:maven.iuvs.calibrated | urn:nasa:pds:maven.iuvs.calibrated:corona::13.0 | processed | 2026-11-15T21:46:28+00:00 | 17,617 | refs complete but 17617 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.raw, urn:nasa:pds:maven.iuvs.raw::13.0 | urn:nasa:pds:maven.iuvs.raw:occultation::13.0 | processed | 2026-11-15T21:54:08+00:00 | 14,607 | refs complete but 14607 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.calibrated::13.0, urn:nasa:pds:maven.iuvs.calibrated | urn:nasa:pds:maven.iuvs.calibrated:occultation::13.0 | processed | 2026-11-15T21:49:46+00:00 | 7,302 | refs complete but 7302 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:juno_mwr, urn:nasa:pds:juno_mwr::1.0 | urn:nasa:pds:juno_mwr:data_calibrated::2.1 | processed (superseded) | 2024-10-25T23:50:35+00:00 | 6,130 | refs missing for 6130 members (refs never written) |
| temp-atm | urn:nasa:pds:maven_ngims::1.1, urn:nasa:pds:maven_ngims::1.0, urn:nasa:pds:maven_ngims | urn:nasa:pds:maven_ngims:l1b::1.0 | processed | 2026-11-15T21:54:47+00:00 | 4,622 | refs missing for 4506 members (refs never written) |
| temp-atm | urn:nasa:pds:juno_mwr, urn:nasa:pds:juno_mwr::1.0 | urn:nasa:pds:juno_mwr:data_raw::2.0 | processed (superseded) | 2024-10-25T19:57:09+00:00 | 3,065 | refs missing for 3065 members (refs never written) |
| temp-atm | urn:nasa:pds:maven.iuvs.calibrated::13.0, urn:nasa:pds:maven.iuvs.calibrated | urn:nasa:pds:maven.iuvs.calibrated:transition::13.0 | processed | 2026-11-15T21:49:47+00:00 | 485 | refs complete but 485 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.derived::13.0, urn:nasa:pds:maven.iuvs.derived | urn:nasa:pds:maven.iuvs.derived:limb::13.0 | processed | 2026-11-15T21:49:48+00:00 | 319 | refs complete but 319 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.processed | urn:nasa:pds:maven.iuvs.processed:occultation::13.0 | stamped_empty_refs | 2026-11-13T07:04:35+00:00 | 86 | refs missing for 1691 members (refs never written) |
| temp-atm | urn:nasa:pds:maven.iuvs.raw, urn:nasa:pds:maven.iuvs.raw::13.0 | urn:nasa:pds:maven.iuvs.raw:transition::13.0 | processed | 2026-11-15T21:54:10+00:00 | 51 | refs complete but 51 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.derived::13.0, urn:nasa:pds:maven.iuvs.derived | urn:nasa:pds:maven.iuvs.derived:occultation::13.0 | processed | 2026-11-15T21:49:49+00:00 | 19 | refs missing for 19 members (refs never written) |
| temp-atm | urn:nasa:pds-ama:sample_bundle, urn:nasa:pds-ama:sample_bundle::1.0 | urn:nasa:pds-ama:sample_bundle:simulation02::1.0 | processed | 2026-06-05T15:42:21+00:00 | 2 | refs complete but 2 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven_ngims::1.1, urn:nasa:pds:maven_ngims::1.0, urn:nasa:pds:maven_ngims | urn:nasa:pds:maven_ngims:calibration::1.0 | processed | 2026-11-15T21:54:11+00:00 | 2 | refs missing for 2 members (refs never written) |
| temp-atm | urn:nasa:pds:maven.iuvs.kp, urn:nasa:pds:maven.iuvs.kp::13.0 | urn:nasa:pds:maven.iuvs.kp:document::13.0 | processed | 2026-11-15T21:49:50+00:00 | 1 | refs missing for 1 members (refs never written) |

## Stamped collections with empty refs

61 collections are stamped with the current version but have no ancestor refs. 0 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 61 have no bundle and are expected.

## Expected pending, by node

1,725 products are waiting on the sweeper or a loading collection. This is the number that should shrink on its own.

| Node | collection_not_loaded_pending | collection_pending | refs_missing_pending | Total |
|---|---|---|---|---|
| temp-atm | 0 | 0 | 1,725 | 1,725 |

## Orphans

42 products belong to 1 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:nasa:pds:juno_uvs:data_raw | temp-atm | 42 | 0 | 42 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Observational | 1,725 | 2,782,642 | 2,784,367 |
| Product_External | 0 | 2 | 2 |
| Product_Document | 0 | 1 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| 1-7d | 1,725 | 86 | 1,811 |
| >30d | 0 | 2,782,559 | 2,782,559 |

## What each rule means

- **collection_not_loaded_overdue** (42 products): The parent collection is still not in the registry (or is not API-visible) long after the product was harvested. Check whether the collection failed to load, is staged or superseded, or whether the product LID does not follow the bundle:collection:product pattern.
- **inventory_version_mismatch** (2,765,640 products): The collection's inventory (as recorded in registry-refs) lists this product at a different version than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the collection will not help: load the product version the inventory lists, after which the registered version is superseded. Confirm with audit_collection.py --diff.
- **not_in_collection_inventory** (16,960 products): The product is registered under this collection's LID, but the collection's current inventory does not list it under any version, so the sweeper can never give it this collection as an ancestor. The provider may have dropped it from the inventory or it may be a leftover. The node should decide whether it belongs in the inventory or should be removed from the registry; re-harvesting or loading more products will not fix it.
- **bare_lid_in_inventory** (1 products): The collection's inventory lists the product by LID only, without a version. Harvest records that as a product_lid in the registry-refs document, but the ancestry sweeper follows only product_lidvid, so it never reaches the product. Re-harvesting the collection writes the same refs; the inventory must list LIDVIDs, or the sweepers must follow LID references.
- **refs_missing_pending** (1,725 products): The collection is processed but no registry-refs document lists the product, and the product was harvested within the grace period, so a load may still be running. Re-check after the grace period; if the product is still missing, it is classified like refs_missing.
- **refs_missing** (2 products): The collection is processed and has refs, but no registry-refs document lists this product, so the sweeper never selects it. Harvest writes a collection's refs from its inventory when the collection is harvested, so the inventory read at that time did not list the product, or the inventory has changed since, or the refs were not written. Read the collection's current inventory. If it lists this exact product, the refs are stale: the node re-harvests the collection from its current label and inventory, then EN runs the sweepers. If it lists another version of the product or does not list it, the node's data does not line up and the node fixes it (the audit reports those as inventory_version_mismatch and not_in_collection_inventory when it can read the inventory). The collection named for the product is a best guess from its identifier.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: atm
- Node filter: atm
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated with no baseline (any anomaly fails).

**FAIL** - 2 invariant(s) violated.

- `no_anomalous_products`: 2,782,645 products are anomalous
  - inventory_version_mismatch: 2,765,640
  - not_in_collection_inventory: 16,960
  - collection_not_loaded_overdue: 42
  - refs_missing: 2
  - bare_lid_in_inventory: 1
- `superseded_by_mapped`: 1 registry indices do not map ops:Provenance/ops:superseded_by, so the API cannot exclude superseded products there
  - atm-registry
