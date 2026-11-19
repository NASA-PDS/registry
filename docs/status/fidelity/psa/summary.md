# Unprocessed product audit

Run time: 2026-11-19T04:03:08+00:00
Nodes: psa

- Candidates examined: **1,328,688**
- Expected (should resolve on their own): **1,073,027**
- Anomalous (need attention): **255,661**
- Not API-visible (staged etc.) without ancestry, not counted above: 0

## What needs to happen

**Needs attention: 29,463 products for the node; 226,198 products that need a closer look.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: No collection with the identifier these products belong to is in the registry | 21,466 | 17 | Load the collection, or correct the product identifiers |
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 7,997 | 10 | Load the version the inventory lists, or correct the inventory |
| Needs a closer look | **Orphaned**: No refs record lists these products and the collection inventory could not be used to say why | 226,198 | 30 | Re-run the audit with the inventories (not --no-inventory), or check the collection's inventory by hand |
| No action | **Waiting**: Not in the registry's refs yet | 1,072,887 | - | None; re-check later |
| No action | **Waiting**: Waiting for the collection to be loaded | 138 | - | None; re-check later |
| No action | **Waiting**: Product classes that never belong to a collection | 2 | - | None |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Waiting**: loaded recently; expected to resolve by itself.

Who fixes what:

- **Node**: the node's data does not line up (a collection is not loaded, a product is at the wrong version or not in the collection's inventory), or the inventory lists the product but the registry's refs do not, so the node re-harvests that collection to rewrite them.
- **Needs a closer look**: the cause cannot be told apart because the collection inventory could not be used.
- **No action**: loaded recently; expected to resolve by itself.

226,198 products were not checked against the collection inventory (it was skipped with `--no-inventory` or could not be read).

## Anomalies by rule

| Rule | Products |
|---|---|
| collection_not_loaded_overdue | 21,466 |
| inventory_version_mismatch | 7,997 |
| refs_missing | 226,198 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| collection_not_loaded_overdue | psa | 21,466 |
| inventory_version_mismatch | psa | 7,997 |
| refs_missing | psa | 226,198 |

## Anomalous collections

32 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

18 of them are superseded collection versions. Their products are still API-visible, but a superseded version is not re-harvested, so it is left out of `anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| psa | urn:esa:psa:em16_tgo_cas::105.3, urn:esa:psa:em16_tgo_cas, urn:esa:psa:em16_tgo_cas::98.1 (+27 more) | urn:esa:psa:em16_tgo_cas:data_calibrated::4.0 | processed (superseded) | 2023-10-27T06:38:26+00:00 | 172,702 | refs missing for 7589497 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_cas, urn:esa:psa:em16_tgo_cas::1.0, urn:esa:psa:em16_tgo_cas::107.1 | urn:esa:psa:em16_tgo_cas:browse_raw::2.0 | processed | 2025-03-22T07:09:22+00:00 | 13,912 | refs complete but 32496 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_cas::81.36, urn:esa:psa:em16_tgo_cas::64.4, urn:esa:psa:em16_tgo_cas::14.8 (+411 more) | urn:esa:psa:em16_tgo_cas:data_raw::105.1 | processed | 2025-03-22T08:20:51+00:00 | 13,912 | refs complete but 32552 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_nmd, urn:esa:psa:em16_tgo_nmd::108.0, urn:esa:psa:em16_tgo_nmd::99.3 (+24 more) | urn:esa:psa:em16_tgo_nmd:data_calibrated::4.0 | processed (superseded) | 2023-09-27T06:48:58+00:00 | 8,606 | refs missing for 177439 members (refs never written) |
| psa | urn:esa:psa:em16::117.4, urn:esa:psa:em16::120.1, urn:esa:psa:em16::67.47 (+612 more) | urn:esa:psa:em16:miscellaneous_ancillary::125.3 | processed | 2025-03-22T06:01:31+00:00 | 7,105 | refs complete but 7105 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_tgo_cas, urn:esa:psa:em16_tgo_cas::1.0, urn:esa:psa:em16_tgo_cas::107.1 | urn:esa:psa:em16_tgo_cas:browse_calibrated::2.0 | processed | 2025-03-22T06:46:46+00:00 | 5,856 | refs missing for 1775351 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::2.0 | processed (superseded) | 2023-09-06T15:21:19+00:00 | 3,674 | refs missing for 5195 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::2.0 | processed (superseded) | 2023-09-06T15:41:19+00:00 | 3,674 | refs missing for 5194 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.0 | processed (superseded) | 2023-09-06T15:20:57+00:00 | 1,869 | refs missing for 5243 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.0 | processed (superseded) | 2023-09-06T15:39:10+00:00 | 1,869 | refs missing for 5242 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_cas::81.36, urn:esa:psa:em16_tgo_cas::64.4, urn:esa:psa:em16_tgo_cas::14.8 (+398 more) | urn:esa:psa:em16_tgo_cas:miscellaneous_ancillary::4.0 | processed (superseded) | 2023-11-15T07:44:56+00:00 | 121 | refs missing for 2523 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_nmd::52.0, urn:esa:psa:em16_tgo_nmd::84.9, urn:esa:psa:em16_tgo_nmd::45.58 (+397 more) | urn:esa:psa:em16_tgo_nmd:miscellaneous_ancillary::4.0 | processed (superseded) | 2023-09-25T18:01:42+00:00 | 119 | refs missing for 2571 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_acs::102.1, urn:esa:psa:em16_tgo_acs::78.1, urn:esa:psa:em16_tgo_acs::41.7 (+410 more) | urn:esa:psa:em16_tgo_acs:miscellaneous_ancillary::4.0 | processed (superseded) | 2023-09-25T01:48:16+00:00 | 118 | refs missing for 2578 members (refs never written) |
| psa | urn:esa:psa:bc::14.2, urn:esa:psa:bc::25.2, urn:esa:psa:bc::14.3 (+100 more) | urn:esa:psa:bc:miscellaneous::12.1 | processed | 2025-02-20T06:04:29+00:00 | 96 | refs missing for 3814 members (refs never written) |
| psa | urn:esa:psa:bc_spice::3.0, urn:esa:psa:bc_spice::1.0, urn:esa:psa:bc_spice::2.0 (+2 more) | urn:esa:psa:bc_spice:spice_kernels::4.0 | processed | 2024-03-20T06:06:07+00:00 | 92 | refs missing for 88 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.1 | processed (superseded) | 2023-09-06T15:20:59+00:00 | 90 | refs missing for 5238 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.1 | processed (superseded) | 2023-09-06T15:39:13+00:00 | 90 | refs missing for 5237 members (refs never written) |
| psa | urn:esa:psa:em16_spice, urn:esa:psa:em16_spice::3.0, urn:esa:psa:em16_spice::2.0 (+8 more) | urn:esa:psa:em16_spice:spice_kernels::10.0 | processed | 2024-02-21T08:22:21+00:00 | 58 | refs missing for 53 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.3 | processed (superseded) | 2023-09-06T15:21:15+00:00 | 27 | refs missing for 5207 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.3 | processed (superseded) | 2023-09-06T15:40:14+00:00 | 27 | refs missing for 5206 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.2 | processed (superseded) | 2023-09-06T15:21:13+00:00 | 24 | refs missing for 5223 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.2 | processed (superseded) | 2023-09-06T15:39:17+00:00 | 24 | refs missing for 5222 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_frd::76.2, urn:esa:psa:em16_tgo_frd, urn:esa:psa:em16_tgo_frd::1.0 (+1 more) | urn:esa:psa:em16_tgo_frd:data_partially_processed::59.3 | processed | 2025-03-22T09:09:34+00:00 | 24 | refs complete but 24 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::13.1 | processed | 2023-09-06T16:03:45+00:00 | 23 | refs missing for 909 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::13.1 | processed | 2023-09-06T16:03:48+00:00 | 23 | refs missing for 910 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_nmd, urn:esa:psa:em16_tgo_nmd::1.0 | urn:esa:psa:em16_tgo_nmd:calibration_files::1.1 | processed | 2026-10-22T08:46:28+00:00 | 16 | refs missing for 16 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:browse::1.4 | processed (superseded) | 2023-09-06T15:21:17+00:00 | 12 | refs missing for 5197 members (refs never written) |
| psa | urn:esa:psa:bc_mtm_mcam::11.2, urn:esa:psa:bc_mtm_mcam::3.0, urn:esa:psa:bc_mtm_mcam::1.3 (+75 more) | urn:esa:psa:bc_mtm_mcam:data_raw::1.4 | processed (superseded) | 2023-09-06T15:40:28+00:00 | 12 | refs missing for 5196 members (refs never written) |
| psa | urn:esa:psa:em16_tgo_frd::1.0, urn:esa:psa:em16_tgo_frd | urn:esa:psa:em16_tgo_frd:data_calibrated::1.0 | processed (superseded) | 2026-10-22T08:44:42+00:00 | 12 | refs complete but 12 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:em16_spice, urn:esa:psa:em16_spice::3.0, urn:esa:psa:em16_spice::2.0 (+8 more) | urn:esa:psa:em16_spice:miscellaneous::10.0 | processed | 2024-02-21T08:22:23+00:00 | 6 | refs complete but 7 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:bc_spice::3.0, urn:esa:psa:bc_spice::1.0, urn:esa:psa:bc_spice::2.0 (+2 more) | urn:esa:psa:bc_spice:miscellaneous::4.0 | processed | 2024-03-20T06:06:10+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| psa | urn:esa:psa:psa_master, urn:esa:psa:psa_master::8.0 | urn:esa:psa:psa_master:xml_schema::7.0 | processed | 2026-10-22T05:00:43+00:00 | 1 | refs missing for 1 members (refs never written) |

## Stamped collections with empty refs

2 collections are stamped with the current version but have no ancestor refs. 0 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 2 have no bundle and are expected.

## Expected pending, by node

1,073,025 products are waiting on the sweeper or a loading collection. This is the number that should shrink on its own.

| Node | collection_not_loaded_pending | collection_pending | refs_missing_pending | Total |
|---|---|---|---|---|
| psa | 138 | 0 | 1,072,887 | 1,073,025 |

## Orphans

21,604 products belong to 18 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:esa:psa:juice:miscellaneous | psa | 11,655 | 0 | 11,655 |
| urn:esa:psa:juice_radem:browse_raw | psa | 2,218 | 30 | 2,248 |
| urn:esa:psa:juice_radem:data_raw | psa | 2,248 | 0 | 2,248 |
| urn:esa:psa:juice_jmc:data_raw | psa | 1,780 | 0 | 1,780 |
| urn:esa:psa:juice_jmc:browse_partially_processed | psa | 1,493 | 102 | 1,595 |
| urn:esa:psa:juice_jmc:data_partially_processed | psa | 1,590 | 0 | 1,590 |
| urn:esa:psa:bc_mpo_mag:data_derived | psa | 264 | 0 | 264 |
| urn:esa:psa:juice_jmc:data_calibrated | psa | 192 | 0 | 192 |
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
| Product_Observational | 452,927 | 225,920 | 678,847 |
| Product_Browse | 619,991 | 29,198 | 649,189 |
| Product_Ancillary | 96 | 368 | 464 |
| Product_SPICE_Kernel | 5 | 150 | 155 |
| Product_Document | 6 | 24 | 30 |
| Product_Context | 2 | 0 | 2 |
| Product_XML_Schema | 0 | 1 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| 1-7d | 1,073,026 | 26 | 1,073,052 |
| 7-30d | 1 | 192,484 | 192,485 |
| >30d | 0 | 63,151 | 63,151 |

## How this maps to the orphan repair report

The ancestry orphan repair dry run prints products examined, repairable (a refs document lists the product under a collection in the registry) and unresolved (no refs document lists it, or only under a collection that is not in the registry).

- The repair examines the 1,328,688 audit candidates plus the 0 products that are not API-visible, because it does not filter on archive status.
- The repair has no grace period, so waiting (`*_pending`) products are counted too.
- The audit counts any stamp other than the current version, the repair only a stamp below it.

| Audit rule | Products | Repair bucket |
|---|---|---|
| refs_missing | 226,198 | unresolved |
| refs_missing_pending | 1,072,887 | unresolved |
| inventory_version_mismatch | 7,997 | unresolved |
| collection_not_loaded_overdue | 21,466 | unresolved unless a refs document lists it under a collection in the registry |
| collection_not_loaded_pending | 138 | unresolved unless a refs document lists it under a collection in the registry |
| no_parent_by_design | 2 | unresolved unless a refs document lists it under a collection in the registry |
| **all (the repair's products examined)** | **1,328,688** |  |

## What each rule means

- **no_parent_by_design** (2 products): These product classes never belong to a collection, so they never receive ancestry. No action is needed.
- **collection_not_loaded_pending** (138 products): The parent collection is not in the registry yet and the product was harvested recently. This is expected to resolve once the collection is loaded and swept.
- **collection_not_loaded_overdue** (21,466 products): The parent collection is still not in the registry (or is not API-visible) long after the product was harvested. Check whether the collection failed to load, is staged or superseded, or whether the product LID does not follow the bundle:collection:product pattern.
- **inventory_version_mismatch** (7,997 products): The collection's inventory (as recorded in registry-refs) lists this product at a different version than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the collection will not help: load the product version the inventory lists, after which the registered version is superseded. Confirm with audit_collection.py --diff.
- **refs_missing_pending** (1,072,887 products): The collection is processed but no registry-refs document lists the product, and the product was harvested within the grace period, so a load may still be running. Re-check after the grace period; if the product is still missing, it is classified like refs_missing.
- **refs_missing** (226,198 products): The collection is processed and has refs, but no registry-refs document lists this product, so the sweeper never selects it. Harvest writes a collection's refs from its inventory when the collection is harvested, so the inventory read at that time did not list the product, or the inventory has changed since, or the refs were not written. Read the collection's current inventory. If it lists this exact product, the refs are stale: the node re-harvests the collection from its current label and inventory so Harvest rewrites the refs. If it lists another version of the product or does not list it, the node's data does not line up and the node fixes it (the audit reports those as inventory_version_mismatch and not_in_collection_inventory when it can read the inventory). The collection named for the product is a best guess from its identifier.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: psa
- Node filter: psa
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated against the baseline of 2026-11-16T22:53:59+00:00.

**FAIL** - 1 invariant(s) violated.

- `no_new_anomalies`: 1 collections newly root anomalous products; 2 rules have more anomalous products than the baseline of 2026-11-16T22:53:59+00:00
  - urn:esa:psa:bc:miscellaneous::12.1
  - collection_not_loaded_overdue: 20,941 -> 21,466
  - refs_missing: 57,525 -> 226,198
