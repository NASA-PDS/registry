# Unprocessed product audit

Run time: 2026-11-19T04:02:40+00:00
Nodes: atm

- Candidates examined: **2,804,917**
- Expected (should resolve on their own): **8,064**
- Anomalous (need attention): **2,796,853**
- Not API-visible (staged etc.) without ancestry, not counted above: 7,770 (staged 7,770)

## What needs to happen

**Needs attention: 2,796,850 products for the node; 21 collections for EN; 1 product for the sweepers team; 2 products that need a closer look.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 2,765,640 | 16 | Load the version the inventory lists, or correct the inventory |
| Node | **Orphaned**: The collection's inventory does not list these products under any version | 16,960 | 8 | Add them to the inventory, or remove the products from the registry |
| Node | **Not processed**: Linked to their collection, but loaded after the sweepers processed it, so the sweepers never went back | 14,208 | 2 | Re-harvest the collection; EN then runs the sweepers |
| Node | **Orphaned**: No collection with the identifier these products belong to is in the registry | 42 | 1 | Load the collection, or correct the product identifiers |
| EN | **Not processed**: The collection is marked processed but has no link to its bundle, so the bundle does not list it as a member (a sweepers bug, fixed in registry-sweepers PR #286) | - | 21 | EN re-harvests the collection and runs the sweepers that include the fix |
| Sweepers team | **Orphaned**: The collection's inventory lists these products by LID without a version, which the sweepers do not follow | 1 | 1 | Re-harvesting does not help. The node lists LIDVIDs in the inventory, or the sweepers support LID references |
| Needs a closer look | **Orphaned**: No refs record lists these products and the collection inventory could not be used to say why | 2 | 1 | Re-run the audit with the inventories (not --no-inventory), or check the collection's inventory by hand |
| No action | **Waiting**: Waiting for the collection to be loaded | 6,339 | - | None; re-check later |
| No action | **Waiting**: Not in the registry's refs yet | 1,725 | - | None; re-check later |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Not processed**: the registry's refs list the product, so its collection is confirmed, but the sweepers never gave it ancestry.
- **Waiting**: loaded recently; expected to resolve by itself.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory), or the collection has to be re-harvested by the node so that the registry's refs are rewritten from its inventory; EN then runs the sweepers.
- **EN**: EN fixes the registry itself: runs the sweepers, repairs collections the sweepers bug left without a bundle link, and fixes index mappings.
- **Sweepers team**: everything looks right but the sweepers cannot or do not follow it; a software gap, possibly worked around by the node.
- **Needs a closer look**: the cause cannot be told apart because the collection inventory could not be used.
- **No action**: loaded recently; expected to resolve by itself.

2 products were not checked against the collection inventory (it was skipped with `--no-inventory` or could not be read).

## Anomalies by rule

| Rule | Products |
|---|---|
| collection_not_loaded_overdue | 42 |
| reloaded_after_collection | 14,208 |
| inventory_version_mismatch | 2,765,640 |
| not_in_collection_inventory | 16,960 |
| bare_lid_in_inventory | 1 |
| refs_missing | 2 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| collection_not_loaded_overdue | temp-atm | 42 |
| reloaded_after_collection | temp-atm | 14,208 |
| inventory_version_mismatch | temp-atm | 2,765,640 |
| not_in_collection_inventory | temp-atm | 16,960 |
| bare_lid_in_inventory | temp-atm | 1 |
| refs_missing | temp-atm | 2 |

## Anomalous collections

25 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

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
| temp-atm | urn:nasa:pds:juno_jiram, urn:nasa:pds:juno_jiram::1.1 | urn:nasa:pds:juno_jiram:data_raw::1.0 | processed | 2026-11-15T21:44:46+00:00 | 7,188 | refs missing for 136733 members (refs never written) |
| temp-atm | urn:nasa:pds:juno_jiram, urn:nasa:pds:juno_jiram::1.1 | urn:nasa:pds:juno_jiram:data_calibrated::1.0 | processed | 2026-11-15T21:43:59+00:00 | 7,020 | refs missing for 85206 members (refs never written) |
| temp-atm | urn:nasa:pds:juno_mwr, urn:nasa:pds:juno_mwr::1.0 | urn:nasa:pds:juno_mwr:data_calibrated::2.1 | processed (superseded) | 2024-10-25T23:50:35+00:00 | 6,130 | refs missing for 171780 members (refs never written) |
| temp-atm | urn:nasa:pds:maven_ngims::1.1, urn:nasa:pds:maven_ngims::1.0, urn:nasa:pds:maven_ngims | urn:nasa:pds:maven_ngims:l1b::1.0 | processed | 2026-11-15T21:54:47+00:00 | 4,622 | refs missing for 4506 members (refs never written) |
| temp-atm | urn:nasa:pds:juno_mwr, urn:nasa:pds:juno_mwr::1.0 | urn:nasa:pds:juno_mwr:data_raw::2.0 | processed (superseded) | 2024-10-25T19:57:09+00:00 | 3,065 | refs missing for 85894 members (refs never written) |
| temp-atm | urn:nasa:pds:maven.iuvs.calibrated::13.0, urn:nasa:pds:maven.iuvs.calibrated | urn:nasa:pds:maven.iuvs.calibrated:transition::13.0 | processed | 2026-11-15T21:49:47+00:00 | 485 | refs complete but 485 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.derived::13.0, urn:nasa:pds:maven.iuvs.derived | urn:nasa:pds:maven.iuvs.derived:limb::13.0 | processed | 2026-11-15T21:49:48+00:00 | 319 | refs complete but 319 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.processed | urn:nasa:pds:maven.iuvs.processed:occultation::13.0 | stamped_empty_refs | 2026-11-17T19:27:04+00:00 | 86 | refs missing for 1691 members (refs never written) |
| temp-atm | urn:nasa:pds:maven.iuvs.raw, urn:nasa:pds:maven.iuvs.raw::13.0 | urn:nasa:pds:maven.iuvs.raw:transition::13.0 | processed | 2026-11-15T21:54:10+00:00 | 51 | refs complete but 51 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven.iuvs.derived::13.0, urn:nasa:pds:maven.iuvs.derived | urn:nasa:pds:maven.iuvs.derived:occultation::13.0 | processed | 2026-11-15T21:49:49+00:00 | 19 | refs missing for 19 members (refs never written) |
| temp-atm | urn:nasa:pds-ama:sample_bundle, urn:nasa:pds-ama:sample_bundle::1.0 | urn:nasa:pds-ama:sample_bundle:simulation02::1.0 | processed | 2026-06-05T15:42:21+00:00 | 2 | refs complete but 2 members not stamped (sweeper skipped them) |
| temp-atm | urn:nasa:pds:maven_ngims::1.1, urn:nasa:pds:maven_ngims::1.0, urn:nasa:pds:maven_ngims | urn:nasa:pds:maven_ngims:calibration::1.0 | processed | 2026-11-15T21:54:11+00:00 | 2 | refs missing for 2 members (refs never written) |
| temp-atm | urn:nasa:pds:maven.iuvs.kp, urn:nasa:pds:maven.iuvs.kp::13.0 | urn:nasa:pds:maven.iuvs.kp:document::13.0 | processed | 2026-11-15T21:49:50+00:00 | 1 | refs missing for 1 members (refs never written) |

## Stamped collections with empty refs

84 collections are stamped with the current version but have no ancestor refs. 21 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 63 have no bundle and are expected.

| Node | Bundle(s) | Collection | Harvested |
|---|---|---|---|
| temp-atm | urn:nasa:pds:cassini_saturn_radar_maps::1.0 | urn:nasa:pds:cassini_saturn_radar_maps:context::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:cassini_saturn_radar_maps::1.0 | urn:nasa:pds:cassini_saturn_radar_maps:document::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:cocirs_c2h4abund::1.0 | urn:nasa:pds:cocirs_c2h4abund:context::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:corss_occul_el_dens::1.0 | urn:nasa:pds:corss_occul_el_dens:context::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:corss_saturn_ionosphere::1.0 | urn:nasa:pds:corss_saturn_ionosphere:context::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:corss_saturn_ionosphere::1.0 | urn:nasa:pds:corss_saturn_ionosphere:data_derived::1.1 | 2026-11-17T23:35:43+00:00 |
| temp-atm | urn:nasa:pds:corss_saturn_ionosphere::1.0 | urn:nasa:pds:corss_saturn_ionosphere:document::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:corss_titan_ionosphere::1.0 | urn:nasa:pds:corss_titan_ionosphere:data_derived::1.1 | 2026-11-17T23:35:42+00:00 |
| temp-atm | urn:nasa:pds:irtf_io_photometry::1.0 | urn:nasa:pds:irtf_io_photometry:data_derived::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:juno_mwr::1.0 | urn:nasa:pds:juno_mwr:data_calibrated::3.0 | 2026-11-17T19:24:01+00:00 |
| temp-atm | urn:nasa:pds:juno_mwr::1.0 | urn:nasa:pds:juno_mwr:data_raw::3.0 | 2026-11-17T19:23:45+00:00 |
| temp-atm | urn:nasa:pds:juno_mwr::1.0 | urn:nasa:pds:juno_mwr:document::3.0 | 2026-11-17T19:23:06+00:00 |
| temp-atm | urn:nasa:pds:mars2020_meda::6.0 | urn:nasa:pds:mars2020_meda:data_calibrated_env::16.0 | 2026-11-17T19:29:50+00:00 |
| temp-atm | urn:nasa:pds:mars2020_meda::6.0 | urn:nasa:pds:mars2020_meda:data_derived_env::16.0 | 2026-11-17T19:33:48+00:00 |
| temp-atm | urn:nasa:pds:mars2020_meda::6.0 | urn:nasa:pds:mars2020_meda:data_partially_processed_env::16.0 | 2026-11-17T19:41:19+00:00 |
| temp-atm | urn:nasa:pds:mars2020_meda::6.0 | urn:nasa:pds:mars2020_meda:data_raw_env::16.0 | 2026-11-17T19:26:12+00:00 |
| temp-atm | urn:nasa:pds:mer_imu::1.1 | urn:nasa:pds:mer_imu:context::1.2 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:msledl::1.1 | urn:nasa:pds:msledl:data::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:msledl::1.1 | urn:nasa:pds:msledl:document::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:msledl::1.1 | urn:nasa:pds:msledl:schema::1.1 | 2026-11-17T23:35:35+00:00 |
| temp-atm | urn:nasa:pds:saturn_thermosphere_h2_density_temp::1.0 | urn:nasa:pds:saturn_thermosphere_h2_density_temp:context::1.1 | 2026-11-17T23:35:35+00:00 |

## Expected pending, by node

8,064 products are waiting on the sweeper or a loading collection. This is the number that should shrink on its own.

| Node | collection_not_loaded_pending | collection_pending | refs_missing_pending | Total |
|---|---|---|---|---|
| temp-atm | 6,339 | 0 | 1,725 | 8,064 |

## Orphans

6,381 products belong to 2 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:nasa:pds:maven.iuvs.processed:echelle | temp-atm | 0 | 6,294 | 6,294 |
| urn:nasa:pds:juno_uvs:data_raw | temp-atm | 42 | 45 | 87 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Observational | 8,064 | 2,796,850 | 2,804,914 |
| Product_External | 0 | 2 | 2 |
| Product_Document | 0 | 1 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| <=1d | 6,294 | 14,208 | 20,502 |
| 1-7d | 1,770 | 86 | 1,856 |
| >30d | 0 | 2,782,559 | 2,782,559 |

## How this maps to the orphan repair report

The ancestry orphan repair dry run prints products examined, repairable (a refs document lists the product under a collection in the registry) and unresolved (no refs document lists it, or only under a collection that is not in the registry).

- The repair examines the 2,804,917 audit candidates plus the 7,770 products that are not API-visible, because it does not filter on archive status.
- The repair has no grace period, so waiting (`*_pending`) products are counted too.
- The audit counts any stamp other than the current version, the repair only a stamp below it.

| Audit rule | Products | Repair bucket |
|---|---|---|
| reloaded_after_collection | 14,208 | repairable |
| refs_missing | 2 | unresolved |
| refs_missing_pending | 1,725 | unresolved |
| inventory_version_mismatch | 2,765,640 | unresolved |
| not_in_collection_inventory | 16,960 | unresolved |
| bare_lid_in_inventory | 1 | unresolved |
| collection_not_loaded_overdue | 42 | unresolved unless a refs document lists it under a collection in the registry |
| collection_not_loaded_pending | 6,339 | unresolved unless a refs document lists it under a collection in the registry |
| not API-visible (not audited) | 7,770 | repairable if a refs document lists it, else unresolved |
| **all (the repair's products examined)** | **2,812,687** |  |

## What each rule means

- **collection_not_loaded_pending** (6,339 products): The parent collection is not in the registry yet and the product was harvested recently. This is expected to resolve once the collection is loaded and swept.
- **collection_not_loaded_overdue** (42 products): The parent collection is still not in the registry (or is not API-visible) long after the product was harvested. Check whether the collection failed to load, is staged or superseded, or whether the product LID does not follow the bundle:collection:product pattern.
- **reloaded_after_collection** (14,208 products): The product was re-harvested after its collection was processed, so the sweeper has no reason to revisit it. Candidate fix: re-harvest the collection so the sweeper reprocesses it.
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

Evaluated against the baseline of 2026-11-16T22:23:46+00:00.

**FAIL** - 2 invariant(s) violated.

- `no_new_anomalies`: 2 collections newly root anomalous products; 1 rules have more anomalous products than the baseline of 2026-11-16T22:23:46+00:00
  - urn:nasa:pds:juno_jiram:data_calibrated::1.0
  - urn:nasa:pds:juno_jiram:data_raw::1.0
  - reloaded_after_collection: 0 -> 14,208
- `no_empty_refs_collection_with_bundle`: 21 collections with a bundle are newly stamped with empty refs
  - urn:nasa:pds:cassini_saturn_radar_maps:context::1.1
  - urn:nasa:pds:cassini_saturn_radar_maps:document::1.1
  - urn:nasa:pds:cocirs_c2h4abund:context::1.1
  - urn:nasa:pds:corss_occul_el_dens:context::1.1
  - urn:nasa:pds:corss_saturn_ionosphere:context::1.1
  - urn:nasa:pds:corss_saturn_ionosphere:data_derived::1.1
  - urn:nasa:pds:corss_saturn_ionosphere:document::1.1
  - urn:nasa:pds:corss_titan_ionosphere:data_derived::1.1
  - urn:nasa:pds:irtf_io_photometry:data_derived::1.1
  - urn:nasa:pds:juno_mwr:data_calibrated::3.0
  - urn:nasa:pds:juno_mwr:data_raw::3.0
  - urn:nasa:pds:juno_mwr:document::3.0
  - urn:nasa:pds:mars2020_meda:data_calibrated_env::16.0
  - urn:nasa:pds:mars2020_meda:data_derived_env::16.0
  - urn:nasa:pds:mars2020_meda:data_partially_processed_env::16.0
  - urn:nasa:pds:mars2020_meda:data_raw_env::16.0
  - urn:nasa:pds:mer_imu:context::1.2
  - urn:nasa:pds:msledl:data::1.1
  - urn:nasa:pds:msledl:document::1.1
  - urn:nasa:pds:msledl:schema::1.1
  - ... and 1 more
