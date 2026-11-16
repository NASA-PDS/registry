# Unprocessed product audit

Run time: 2026-11-16T22:23:53+00:00
Nodes: sbnumd

- Candidates examined: **25**
- Expected (should resolve on their own): **0**
- Anomalous (need attention): **25**

## What needs to happen

**Needs attention: 1 for node; 82 for registry operations.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory does not list these products under any version | 1 | 1 | Add them to the inventory, or remove the products from the registry |
| Registry operations | **Not processed**: Linked to their collection, but loaded after the sweepers processed it, so the sweepers never went back | 20 | 9 | Re-harvest the collection, then run the sweepers |
| Registry operations | **Not processed**: Linked to their collection, but processed by an older sweepers version while the collection is on the current one, so the sweepers do not go back | 4 | 2 | Re-harvest the collection, then run the sweepers |
| Registry operations | **Not processed**: The collection is marked processed but has no link to its bundle, so the bundle does not list it as a member | - | 58 | Re-harvest the collection, then run the sweepers (the sweepers bug that caused this is fixed in registry-sweepers PR #286) |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Not processed**: the registry's refs list the product, so its collection is confirmed, but the sweepers never gave it ancestry.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory); only the node can fix it.
- **Registry operations**: the node's data is fine and the registry's own processing missed it; fixed by re-harvesting the collection and running the sweepers.

## Anomalies by rule

| Rule | Products |
|---|---|
| reloaded_after_collection | 20 |
| not_in_collection_inventory | 1 |
| stale_stamp | 4 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| reloaded_after_collection | sbnumd | 20 |
| not_in_collection_inventory | sbnumd | 1 |
| stale_stamp | sbnumd | 4 |

## Anomalous collections

12 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

2 of them are superseded collection versions. Their products are still API-visible, but a superseded version is not re-harvested, so it is left out of `anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| sbnumd | urn:nasa:pds:bopps2014, urn:nasa:pds:bopps2014::1.0 | urn:nasa:pds:bopps2014:raw::1.0 | processed | 2025-06-27T22:25:26+00:00 | 10 | refs complete but 10 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:bopps2014, urn:nasa:pds:bopps2014::1.0 | urn:nasa:pds:bopps2014:groundcalibration::1.0 | processed | 2025-06-30T23:30:39+00:00 | 3 | refs complete but 3 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:lucy.mvic::1.0, urn:nasa:pds:lucy.mvic | urn:nasa:pds:lucy.mvic:document::1.0 | processed (superseded) | 2026-10-07T21:15:07+00:00 | 3 | refs complete but 3 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:bopps2014, urn:nasa:pds:bopps2014::1.0 | urn:nasa:pds:bopps2014:biassub::1.0 | processed | 2025-11-04T22:20:10+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:bopps2014, urn:nasa:pds:bopps2014::1.0 | urn:nasa:pds:bopps2014:calibrated::1.0 | processed | 2025-07-01T23:10:54+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:dart_teleobs, urn:nasa:pds:dart_teleobs::1.0 | urn:nasa:pds:dart_teleobs:data_ldtddp::1.0 | processed (superseded) | 2026-09-21T19:04:10+00:00 | 1 | refs missing for 8 members (refs never written) |
| sbnumd | urn:nasa:pds:liciacube::1.0 | urn:nasa:pds:liciacube:document::1.0 | stamped_empty_refs | 2026-09-17T20:38:08+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:lucy.leisa::2.0 | urn:nasa:pds:lucy.leisa:data_donaldjohanson_calibrated::1.0 | stamped_empty_refs | 2026-09-25T15:38:59+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:lucy.leisa::2.0 | urn:nasa:pds:lucy.leisa:data_donaldjohanson_raw::1.0 | stamped_empty_refs | 2026-09-28T19:48:07+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:lucy.ltes::2.0, urn:nasa:pds:lucy.ltes | urn:nasa:pds:lucy.ltes:data_donaldjohanson_calibrated::1.0 | processed | 2026-10-06T21:31:06+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:lucy.mvic::2.0 | urn:nasa:pds:lucy.mvic:data_donaldjohanson_calibrated::1.0 | stamped_empty_refs | 2026-10-07T21:57:07+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |
| sbnumd | urn:nasa:pds:lucy.rss::2.0 | urn:nasa:pds:lucy.rss:data_dinkinesh_trk234::1.0 | stamped_empty_refs | 2026-10-27T16:16:07+00:00 | 1 | refs complete but 1 members not stamped (sweeper skipped them) |

## Stamped collections with empty refs

58 collections are stamped with the current version but have no ancestor refs. 58 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 0 have no bundle and are expected.

| Node | Bundle(s) | Collection | Harvested |
|---|---|---|---|
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcogt_flical::1.0 | 2026-09-18T17:03:10+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcogt_fliddp::1.0 | 2026-09-18T16:48:08+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcogt_fliraw::1.0 | 2026-10-20T18:41:07+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcogtcal::1.0 | 2026-09-18T23:02:32+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcogtddp::1.0 | 2026-09-18T21:15:10+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcogtraw::1.0 | 2026-09-18T21:52:40+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcoimacscal::1.0 | 2026-09-18T20:33:56+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcoimacsddp::1.0 | 2026-09-18T20:48:08+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcoimacsraw::1.0 | 2026-09-18T21:01:43+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcoswopecal::1.0 | 2026-09-18T20:06:27+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcoswopeddp::1.0 | 2026-09-18T17:40:09+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_lcoswoperaw::1.0 | 2026-09-18T18:40:43+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_ldtddp::2.0 | 2026-09-21T20:23:16+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_ldtraw::2.0 | 2026-09-21T20:40:28+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_mrocal::1.0 | 2026-09-21T17:25:48+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_mroddp::1.0 | 2026-09-21T15:53:04+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:data_mroraw::1.0 | 2026-09-21T16:55:57+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:document_lco::1.0 | 2026-09-21T15:18:17+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:document_lcogt::1.0 | 2026-09-21T15:02:26+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:document_ldt::2.0 | 2026-09-21T20:04:13+00:00 |
| sbnumd | urn:nasa:pds:dart_teleobs::2.0 | urn:nasa:pds:dart_teleobs:document_mro::1.0 | 2026-10-20T20:01:07+00:00 |
| sbnumd | urn:nasa:pds:liciacube::1.0 | urn:nasa:pds:liciacube:data_tnf::1.0 | 2026-09-17T20:18:08+00:00 |
| sbnumd | urn:nasa:pds:liciacube::1.0 | urn:nasa:pds:liciacube:document::1.0 | 2026-09-17T20:38:08+00:00 |
| sbnumd | urn:nasa:pds:liciacube::1.0 | urn:nasa:pds:liciacube:leia_calibrated::1.0 | 2026-09-23T16:00:24+00:00 |
| sbnumd | urn:nasa:pds:liciacube::1.0 | urn:nasa:pds:liciacube:leia_raw::1.0 | 2026-10-20T21:12:07+00:00 |
| sbnumd | urn:nasa:pds:liciacube::1.0 | urn:nasa:pds:liciacube:luke_calibrated::1.0 | 2026-09-22T20:50:37+00:00 |
| sbnumd | urn:nasa:pds:liciacube::1.0 | urn:nasa:pds:liciacube:luke_raw::1.0 | 2026-09-22T17:42:13+00:00 |
| sbnumd | urn:nasa:pds:lucy.leisa::2.0 | urn:nasa:pds:lucy.leisa:calibration::2.0 | 2026-10-26T18:57:06+00:00 |
| sbnumd | urn:nasa:pds:lucy.leisa::2.0 | urn:nasa:pds:lucy.leisa:data_dinkinesh_calibrated::1.0 | 2026-09-23T21:42:13+00:00 |
| sbnumd | urn:nasa:pds:lucy.leisa::2.0 | urn:nasa:pds:lucy.leisa:data_dinkinesh_raw::1.0 | 2026-09-23T22:02:09+00:00 |
| sbnumd | urn:nasa:pds:lucy.leisa::2.0 | urn:nasa:pds:lucy.leisa:data_donaldjohanson_calibrated::1.0 | 2026-09-25T15:38:59+00:00 |
| sbnumd | urn:nasa:pds:lucy.leisa::2.0 | urn:nasa:pds:lucy.leisa:data_donaldjohanson_raw::1.0 | 2026-09-28T19:48:07+00:00 |
| sbnumd | urn:nasa:pds:lucy.leisa::2.0 | urn:nasa:pds:lucy.leisa:document::2.0 | 2026-09-28T20:01:10+00:00 |
| sbnumd | urn:nasa:pds:lucy.llorri::4.0 | urn:nasa:pds:lucy.llorri:data_3i_atlas_partially_processed::1.0 | 2026-10-19T22:45:06+00:00 |
| sbnumd | urn:nasa:pds:lucy.llorri::4.0 | urn:nasa:pds:lucy.llorri:data_didymos_raw::2.0 | 2026-10-19T19:11:09+00:00 |
| sbnumd | urn:nasa:pds:lucy.llorri::4.0 | urn:nasa:pds:lucy.llorri:data_dinkinesh_partially_processed::1.0 | 2026-10-13T20:40:08+00:00 |
| sbnumd | urn:nasa:pds:lucy.llorri::4.0 | urn:nasa:pds:lucy.llorri:data_dinkinesh_raw::1.0 | 2026-10-13T21:01:09+00:00 |
| sbnumd | urn:nasa:pds:lucy.llorri::4.0 | urn:nasa:pds:lucy.llorri:data_donaldjohanson_partially_processed::1.0 | 2026-10-19T19:30:07+00:00 |
| sbnumd | urn:nasa:pds:lucy.llorri::4.0 | urn:nasa:pds:lucy.llorri:data_donaldjohanson_raw::1.0 | 2026-10-23T22:33:05+00:00 |
| sbnumd | urn:nasa:pds:lucy.llorri::4.0 | urn:nasa:pds:lucy.llorri:document::2.0 | 2026-10-13T20:28:09+00:00 |
| sbnumd | urn:nasa:pds:lucy.ltes::2.0 | urn:nasa:pds:lucy.ltes:data_dinkinesh_calibrated::1.0 | 2026-09-29T22:32:09+00:00 |
| sbnumd | urn:nasa:pds:lucy.ltes::2.0 | urn:nasa:pds:lucy.ltes:data_dinkinesh_hkraw::1.0 | 2026-10-06T20:19:07+00:00 |
| sbnumd | urn:nasa:pds:lucy.ltes::2.0 | urn:nasa:pds:lucy.ltes:data_dinkinesh_raw::1.0 | 2026-10-06T20:47:08+00:00 |
| sbnumd | urn:nasa:pds:lucy.ltes::2.0 | urn:nasa:pds:lucy.ltes:document::1.0 | 2026-10-06T20:59:08+00:00 |
| sbnumd | urn:nasa:pds:lucy.mvic::2.0 | urn:nasa:pds:lucy.mvic:data_dinkinesh_calibrated::1.0 | 2026-10-07T15:22:07+00:00 |
| sbnumd | urn:nasa:pds:lucy.mvic::2.0 | urn:nasa:pds:lucy.mvic:data_dinkinesh_raw::1.0 | 2026-10-07T15:34:08+00:00 |
| sbnumd | urn:nasa:pds:lucy.mvic::2.0 | urn:nasa:pds:lucy.mvic:data_donaldjohanson_calibrated::1.0 | 2026-10-07T21:57:07+00:00 |
| sbnumd | urn:nasa:pds:lucy.mvic::2.0 | urn:nasa:pds:lucy.mvic:data_donaldjohanson_raw::1.0 | 2026-10-27T14:43:06+00:00 |
| sbnumd | urn:nasa:pds:lucy.rss::2.0 | urn:nasa:pds:lucy.rss:data_dinkinesh_ion::1.0 | 2026-10-09T14:03:09+00:00 |
| sbnumd | urn:nasa:pds:lucy.rss::2.0 | urn:nasa:pds:lucy.rss:data_dinkinesh_sff::1.0 | 2026-10-27T15:42:08+00:00 |

_8 more collections omitted; the CSV files hold everything._

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Observational | 0 | 15 | 15 |
| Product_Document | 0 | 10 | 10 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| 7-30d | 0 | 3 | 3 |
| >30d | 0 | 22 | 22 |

## What each rule means

- **reloaded_after_collection** (20 products): The product was re-harvested after its collection was processed, so the sweeper has no reason to revisit it. Candidate fix: re-harvest the collection so the sweeper reprocesses it.
- **not_in_collection_inventory** (1 products): The product is registered under this collection's LID, but the collection's current inventory does not list it under any version, so the sweeper can never give it this collection as an ancestor. The provider may have dropped it from the inventory or it may be a leftover. The node should decide whether it belongs in the inventory or should be removed from the registry; re-harvesting or loading more products will not fix it.
- **stale_stamp** (4 products): The product carries an ancestry stamp from an older sweeper version although its collection is already on the current version. The collection will not be revisited, so a re-sweep of the collection may be needed.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: sbnumd
- Node filter: sbnumd
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated with no baseline (any anomaly fails).

**FAIL** - 2 invariant(s) violated.

- `no_anomalous_products`: 25 products are anomalous
  - reloaded_after_collection: 20
  - stale_stamp: 4
  - not_in_collection_inventory: 1
- `no_empty_refs_collection_with_bundle`: 58 collections with a bundle are stamped with empty refs
  - urn:nasa:pds:dart_teleobs:data_lcogt_flical::1.0
  - urn:nasa:pds:dart_teleobs:data_lcogt_fliddp::1.0
  - urn:nasa:pds:dart_teleobs:data_lcogt_fliraw::1.0
  - urn:nasa:pds:dart_teleobs:data_lcogtcal::1.0
  - urn:nasa:pds:dart_teleobs:data_lcogtddp::1.0
  - urn:nasa:pds:dart_teleobs:data_lcogtraw::1.0
  - urn:nasa:pds:dart_teleobs:data_lcoimacscal::1.0
  - urn:nasa:pds:dart_teleobs:data_lcoimacsddp::1.0
  - urn:nasa:pds:dart_teleobs:data_lcoimacsraw::1.0
  - urn:nasa:pds:dart_teleobs:data_lcoswopecal::1.0
  - urn:nasa:pds:dart_teleobs:data_lcoswopeddp::1.0
  - urn:nasa:pds:dart_teleobs:data_lcoswoperaw::1.0
  - urn:nasa:pds:dart_teleobs:data_ldtddp::2.0
  - urn:nasa:pds:dart_teleobs:data_ldtraw::2.0
  - urn:nasa:pds:dart_teleobs:data_mrocal::1.0
  - urn:nasa:pds:dart_teleobs:data_mroddp::1.0
  - urn:nasa:pds:dart_teleobs:data_mroraw::1.0
  - urn:nasa:pds:dart_teleobs:document_lco::1.0
  - urn:nasa:pds:dart_teleobs:document_lcogt::1.0
  - urn:nasa:pds:dart_teleobs:document_ldt::2.0
  - ... and 38 more
