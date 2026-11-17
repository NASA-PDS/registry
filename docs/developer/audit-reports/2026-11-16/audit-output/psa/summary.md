# Unprocessed product audit

Run time: 2026-11-16T22:53:59+00:00
Nodes: psa

- Candidates examined: **1,561,792**
- Expected (should resolve on their own): **1,242,225**
- Anomalous (need attention): **319,567**

## What needs to happen

**Needs attention: 262,042 for the node; 57,525 that need a closer look.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Not processed**: Linked to their collection, but loaded after the sweepers processed it, so the sweepers never went back | 233,104 | 10 | Re-harvest the collection; EN then runs the sweepers |
| Node | **Orphaned**: No collection with the identifier these products belong to is in the registry | 20,941 | 17 | Load the collection, or correct the product identifiers |
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 7,997 | 10 | Load the version the inventory lists, or correct the inventory |
| Needs a closer look | **Orphaned**: No refs record lists these products and the collection inventory could not be used to say why | 57,525 | 29 | Re-run the audit with the inventories (not --no-inventory), or check the collection's inventory by hand |
| No action | **Waiting**: Not in the registry's refs yet | 1,241,560 | - | None; re-check later |
| No action | **Waiting**: Waiting for the collection to be loaded | 663 | - | None; re-check later |
| No action | **Waiting**: Product classes that never belong to a collection | 2 | - | None |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Not processed**: the registry's refs list the product, so its collection is confirmed, but the sweepers never gave it ancestry.
- **Waiting**: loaded recently; expected to resolve by itself.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory), or the collection has to be re-harvested by the node so that the registry's refs are rewritten from its inventory; EN then runs the sweepers.
- **Needs a closer look**: the cause cannot be told apart because the collection inventory could not be used.
- **No action**: loaded recently; expected to resolve by itself.

57,525 products were not checked against the collection inventory (it was skipped with `--no-inventory` or could not be read).

## Anomalies by rule

| Rule | Products |
|---|---|
| collection_not_loaded_overdue | 20,941 |
| reloaded_after_collection | 233,104 |
| inventory_version_mismatch | 7,997 |
| refs_missing | 57,525 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| collection_not_loaded_overdue | psa | 20,941 |
| reloaded_after_collection | psa | 233,104 |
| inventory_version_mismatch | psa | 7,997 |
| refs_missing | psa | 57,525 |

## Anomalous collections

41 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

28 of them are superseded collection versions. Their products are still API-visible, but a superseded version is not re-harvested, so it is left out of `anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| psa | urn:esa:psa:em16_tgo_cas::1.0, urn:esa:psa:em16_tgo_cas | urn:esa:psa:em16_tgo_cas:data_raw::1.0 | processed (superseded) | 2026-10-22T07:45:06+00:00 | 113,135 | refs complete but 145687 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_cas::1.0, urn:esa:psa:em16_tgo_cas | urn:esa:psa:em16_tgo_cas:browse_raw::1.0 | processed (superseded) | 2026-10-22T06:19:45+00:00 | 111,867 | refs complete but 144363 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_cas, urn:esa:psa:em16_tgo_cas::1.0, urn:esa:psa:em16_tgo_cas::107.1 | urn:esa:psa:em16_tgo_cas:browse_raw::2.0 | processed | 2025-03-22T07:09:22+00:00 | 13,912 | refs complete but 144363 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_cas::81.36, urn:esa:psa:em16_tgo_cas::64.4, urn:esa:psa:em16_tgo_cas::14.8 (+411 more) | urn:esa:psa:em16_tgo_cas:data_raw::105.1 | processed | 2025-03-22T08:20:51+00:00 | 13,912 | refs complete but 145687 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_nmd, urn:esa:psa:em16_tgo_nmd::108.0, urn:esa:psa:em16_tgo_nmd::99.3 (+24 more) | urn:esa:psa:em16_tgo_nmd:data_calibrated::4.0 | processed (superseded) | 2023-09-27T06:48:58+00:00 | 8,606 | refs missing for 177439 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_cas, urn:esa:psa:em16_tgo_cas::1.0, urn:esa:psa:em16_tgo_cas::107.1 | urn:esa:psa:em16_tgo_cas:browse_calibrated::2.0 | processed | 2025-03-22T06:46:46+00:00 | 5,856 | refs missing for 1775351 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_cas::105.3, urn:esa:psa:em16_tgo_cas, urn:esa:psa:em16_tgo_cas::98.1 (+27 more) | urn:esa:psa:em16_tgo_cas:data_calibrated::4.0 | processed (superseded) | 2023-10-27T06:38:26+00:00 | 5,856 | refs missing for 7589497 members (refs never written) |
| psa | urn:esa:psa:em16::117.4, urn:esa:psa:em16::120.1, urn:esa:psa:em16::67.47 (+612 more) | urn:esa:psa:em16:miscellaneous_ancillary::125.3 | processed | 2025-03-22T06:01:31+00:00 | 5,374 | refs complete but 7105 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::2.0 | processed (superseded) | 2023-09-06T15:21:19+00:00 | 3,674 | refs missing for 5195 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::2.0 | processed (superseded) | 2023-09-06T15:41:19+00:00 | 3,674 | refs missing for 5194 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_nmd, urn:esa:psa:em16_tgo_nmd::1.0 | urn:esa:psa:em16_tgo_nmd:data_raw::1.0 | processed (superseded) | 2026-10-22T08:48:03+00:00 | 2,813 | refs complete but 2813 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.0 | processed (superseded) | 2023-09-06T15:20:57+00:00 | 1,869 | refs missing for 5243 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.0 | processed (superseded) | 2023-09-06T15:39:10+00:00 | 1,869 | refs missing for 5242 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_acs::1.0, urn:esa:psa:em16_tgo_acs | urn:esa:psa:em16_tgo_acs:data_raw::1.0 | processed (superseded) | 2026-10-22T05:26:41+00:00 | 1,860 | refs complete but 1860 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_nmd, urn:esa:psa:em16_tgo_nmd::1.0 | urn:esa:psa:em16_tgo_nmd:data_partially_processed::1.0 | processed (superseded) | 2026-10-22T08:47:15+00:00 | 1,840 | refs complete but 1840 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_cas::1.0, urn:esa:psa:em16_tgo_cas | urn:esa:psa:em16_tgo_cas:data_partially_processed::1.0 | processed (superseded) | 2026-10-22T07:44:42+00:00 | 976 | refs complete but 976 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:bc, urn:esa:psa:bc::1.0 | urn:esa:psa:bc:miscellaneous::1.0 | processed (superseded) | 2026-10-22T05:01:25+00:00 | 429 | refs complete but 525 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_frd::1.0, urn:esa:psa:em16_tgo_frd | urn:esa:psa:em16_tgo_frd:data_partially_processed::1.0 | processed (superseded) | 2026-10-22T08:44:44+00:00 | 122 | refs complete but 146 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_cas::81.36, urn:esa:psa:em16_tgo_cas::64.4, urn:esa:psa:em16_tgo_cas::14.8 (+398 more) | urn:esa:psa:em16_tgo_cas:miscellaneous_ancillary::4.0 | processed (superseded) | 2023-11-15T07:44:56+00:00 | 121 | refs missing for 2523 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_nmd::52.0, urn:esa:psa:em16_tgo_nmd::84.9, urn:esa:psa:em16_tgo_nmd::45.58 (+397 more) | urn:esa:psa:em16_tgo_nmd:miscellaneous_ancillary::4.0 | processed (superseded) | 2023-09-25T18:01:42+00:00 | 119 | refs missing for 2571 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_acs::102.1, urn:esa:psa:em16_tgo_acs::78.1, urn:esa:psa:em16_tgo_acs::41.7 (+410 more) | urn:esa:psa:em16_tgo_acs:miscellaneous_ancillary::4.0 | processed (superseded) | 2023-09-25T01:48:16+00:00 | 118 | refs missing for 2578 members (refs never written) |
| psa | urn:esa:psa:bc_spice::3.0, urn:esa:psa:bc_spice::1.0, urn:esa:psa:bc_spice::2.0 (+2 more) | urn:esa:psa:bc_spice:spice_kernels::4.0 | processed | 2024-03-20T06:06:07+00:00 | 92 | refs missing for 88 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.1 | processed (superseded) | 2023-09-06T15:20:59+00:00 | 90 | refs missing for 5238 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.1 | processed (superseded) | 2023-09-06T15:39:13+00:00 | 90 | refs missing for 5237 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_frd::1.0, urn:esa:psa:em16_tgo_frd | urn:esa:psa:em16_tgo_frd:data_raw::1.0 | processed (superseded) | 2026-10-22T08:44:50+00:00 | 61 | refs complete but 61 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_spice, urn:esa:psa:em16_spice::3.0, urn:esa:psa:em16_spice::2.0 (+8 more) | urn:esa:psa:em16_spice:spice_kernels::10.0 | processed | 2024-02-21T08:22:21+00:00 | 58 | refs missing for 53 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.3 | processed (superseded) | 2023-09-06T15:21:15+00:00 | 27 | refs missing for 5207 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.3 | processed (superseded) | 2023-09-06T15:40:14+00:00 | 27 | refs missing for 5206 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.2 | processed (superseded) | 2023-09-06T15:21:13+00:00 | 24 | refs missing for 5223 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.2 | processed (superseded) | 2023-09-06T15:39:17+00:00 | 24 | refs missing for 5222 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_frd::76.2, urn:esa:psa:em16_tgo_frd, urn:esa:psa:em16_tgo_frd::1.0 (+1 more) | urn:esa:psa:em16_tgo_frd:data_partially_processed::59.3 | processed | 2025-03-22T09:09:34+00:00 | 24 | refs complete but 146 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::13.1 | processed | 2023-09-06T16:03:45+00:00 | 23 | refs missing for 909 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::13.1 | processed | 2023-09-06T16:03:48+00:00 | 23 | refs missing for 910 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_nmd, urn:esa:psa:em16_tgo_nmd::1.0 | urn:esa:psa:em16_tgo_nmd:calibration_files::1.1 | processed | 2026-10-22T08:46:28+00:00 | 16 | refs missing for 16 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.4 | processed (superseded) | 2023-09-06T15:21:17+00:00 | 12 | refs missing for 5197 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.4 | processed (superseded) | 2023-09-06T15:40:28+00:00 | 12 | refs missing for 5196 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_frd::1.0, urn:esa:psa:em16_tgo_frd | urn:esa:psa:em16_tgo_frd:data_calibrated::1.0 | processed (superseded) | 2026-10-22T08:44:42+00:00 | 12 | refs complete but 12 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_spice, urn:esa:psa:em16_spice::3.0, urn:esa:psa:em16_spice::2.0 (+8 more) | urn:esa:psa:em16_spice:miscellaneous::10.0 | processed | 2024-02-21T08:22:23+00:00 | 6 | refs complete but 7 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:bc, urn:esa:psa:bc::1.0 | urn:esa:psa:bc:xml_schema::1.0 | processed (superseded) | 2026-10-22T05:01:32+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:bc_spice::3.0, urn:esa:psa:bc_spice::1.0, urn:esa:psa:bc_spice::2.0 (+2 more) | urn:esa:psa:bc_spice:miscellaneous::4.0 | processed | 2024-03-20T06:06:10+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:psa_master, urn:esa:psa:psa_master::8.0 | urn:esa:psa:psa_master:xml_schema::7.0 | processed | 2026-10-22T05:00:43+00:00 | 1 | refs missing for 1 members (refs never written) |

## Stamped collections with empty refs

2 collections are stamped with the current version but have no ancestor refs. 0 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 2 have no bundle and are expected.

## Expected pending, by node

1,242,223 products are waiting on the sweeper or a loading collection. This is the number that should shrink on its own.

| Node | collection_not_loaded_pending | collection_pending | refs_missing_pending | Total |
|---|---|---|---|---|
| psa | 663 | 0 | 1,241,560 | 1,242,223 |

## Orphans

21,604 products belong to 18 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:esa:psa:juice:miscellaneous | psa | 11,372 | 283 | 11,655 |
| urn:esa:psa:juice_radem:browse_raw | psa | 2,218 | 30 | 2,248 |
| urn:esa:psa:juice_radem:data_raw | psa | 2,218 | 30 | 2,248 |
| urn:esa:psa:juice_jmc:data_raw | psa | 1,676 | 104 | 1,780 |
| urn:esa:psa:juice_jmc:browse_partially_processed | psa | 1,493 | 102 | 1,595 |
| urn:esa:psa:juice_jmc:data_partially_processed | psa | 1,488 | 102 | 1,590 |
| urn:esa:psa:bc_mpo_mag:data_derived | psa | 264 | 0 | 264 |
| urn:esa:psa:juice_jmc:data_calibrated | psa | 186 | 6 | 192 |
| urn:esa:psa:bc_mpo_more:document | psa | 10 | 0 | 10 |
| urn:esa:psa:bc_mpo_mertis:document | psa | 0 | 6 | 6 |
| urn:esa:psa:bc_mpo_serena:document | psa | 6 | 0 | 6 |
| urn:esa:psa:bc_mpo_berm:document | psa | 3 | 0 | 3 |
| urn:esa:psa:juice_radem:miscellaneous | psa | 2 | 0 | 2 |
| urn:esa:psa:bc_mpo_isa:document | psa | 1 | 0 | 1 |
| urn:esa:psa:bc_mpo_mgns:document | psa | 1 | 0 | 1 |
| urn:esa:psa:bc_mpo_mixs:document | psa | 1 | 0 | 1 |
| urn:esa:psa:bc_mpo_sixs:document | psa | 1 | 0 | 1 |
| urn:esa:psa:juice_radem:document | psa | 1 | 0 | 1 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Observational | 622,125 | 177,958 | 800,083 |
| Product_Browse | 619,991 | 141,065 | 761,056 |
| Product_Ancillary | 96 | 368 | 464 |
| Product_SPICE_Kernel | 5 | 150 | 155 |
| Product_Document | 6 | 24 | 30 |
| Product_Context | 2 | 0 | 2 |
| Product_XML_Schema | 0 | 2 | 2 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| 1-7d | 1,242,224 | 65,869 | 1,308,093 |
| 7-30d | 1 | 190,547 | 190,548 |
| >30d | 0 | 63,151 | 63,151 |

## What each rule means

- **no_parent_by_design** (2 products): These product classes never belong to a collection, so they never receive ancestry. No action is needed.
- **collection_not_loaded_pending** (663 products): The parent collection is not in the registry yet and the product was harvested recently. This is expected to resolve once the collection is loaded and swept.
- **collection_not_loaded_overdue** (20,941 products): The parent collection is still not in the registry (or is not API-visible) long after the product was harvested. Check whether the collection failed to load, is staged or superseded, or whether the product LID does not follow the bundle:collection:product pattern.
- **reloaded_after_collection** (233,104 products): The product was re-harvested after its collection was processed, so the sweeper has no reason to revisit it. Candidate fix: re-harvest the collection so the sweeper reprocesses it.
- **inventory_version_mismatch** (7,997 products): The collection's inventory (as recorded in registry-refs) lists this product at a different version than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the collection will not help: load the product version the inventory lists, after which the registered version is superseded. Confirm with audit_collection.py --diff.
- **refs_missing_pending** (1,241,560 products): The collection is processed but no registry-refs document lists the product, and the product was harvested within the grace period, so a load may still be running. Re-check after the grace period; if the product is still missing, it is classified like refs_missing.
- **refs_missing** (57,525 products): The collection is processed and has refs, but no registry-refs document lists this product, so the sweeper never selects it. Harvest writes a collection's refs from its inventory when the collection is harvested, so the inventory read at that time did not list the product, or the inventory has changed since, or the refs were not written. Read the collection's current inventory. If it lists this exact product, the refs are stale: the node re-harvests the collection from its current label and inventory, then EN runs the sweepers. If it lists another version of the product or does not list it, the node's data does not line up and the node fixes it (the audit reports those as inventory_version_mismatch and not_in_collection_inventory when it can read the inventory). The collection named for the product is a best guess from its identifier.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: psa
- Node filter: psa
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated with no baseline (any anomaly fails).

**FAIL** - 1 invariant(s) violated.

- `no_anomalous_products`: 319,567 products are anomalous
  - reloaded_after_collection: 233,104
  - refs_missing: 57,525
  - collection_not_loaded_overdue: 20,941
  - inventory_version_mismatch: 7,997
