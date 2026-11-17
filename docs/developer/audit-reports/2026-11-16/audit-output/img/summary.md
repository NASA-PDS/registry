# Unprocessed product audit

Run time: 2026-11-16T22:23:49+00:00
Nodes: img

- Candidates examined: **36,839**
- Expected (should resolve on their own): **0**
- Anomalous (need attention): **36,839**

## What needs to happen

**Needs attention: 36,839 products for the node; 6 collections for EN.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Not processed**: Linked to their collection, but loaded after the sweepers processed it, so the sweepers never went back | 36,323 | 5 | Re-harvest the collection; EN then runs the sweepers |
| Node | **Orphaned**: The collection's inventory lists a different version of these products than the one loaded | 516 | 1 | Load the version the inventory lists, or correct the inventory |
| EN | **Not processed**: The collection is marked processed but has no link to its bundle, so the bundle does not list it as a member (a sweepers bug, fixed in registry-sweepers PR #286) | - | 6 | EN re-harvests the collection and runs the sweepers that include the fix |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Not processed**: the registry's refs list the product, so its collection is confirmed, but the sweepers never gave it ancestry.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory), or the collection has to be re-harvested by the node so that the registry's refs are rewritten from its inventory; EN then runs the sweepers.
- **EN**: EN fixes the registry itself: runs the sweepers, repairs collections the sweepers bug left without a bundle link, and fixes index mappings.

## Anomalies by rule

| Rule | Products |
|---|---|
| reloaded_after_collection | 36,323 |
| inventory_version_mismatch | 516 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| reloaded_after_collection | img | 36,323 |
| inventory_version_mismatch | img | 516 |

## Anomalous collections

6 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| img | urn:nasa:pds:artemis2_crew_camera::1.0, urn:nasa:pds:artemis2_crew_camera | urn:nasa:pds:artemis2_crew_camera:data_processed::1.0 | processed | 2026-10-02T03:54:08+00:00 | 9,961 | refs complete but 9961 members not stamped (sweeper skipped them) |
| img | urn:nasa:pds:artemis2_crew_camera::1.0 | urn:nasa:pds:artemis2_crew_camera:data_raw::1.0 | stamped_empty_refs | 2026-10-02T09:31:16+00:00 | 9,141 | refs complete but 9141 members not stamped (sweeper skipped them) |
| img | urn:nasa:pds:artemis2_crew_camera::1.0 | urn:nasa:pds:artemis2_crew_camera:data_source::1.0 | stamped_empty_refs | 2026-10-02T14:27:04+00:00 | 8,671 | refs complete but 8671 members not stamped (sweeper skipped them) |
| img | urn:nasa:pds:artemis2_crew_camera::1.0 | urn:nasa:pds:artemis2_crew_camera:browse::1.0 | stamped_empty_refs | 2026-10-02T01:41:44+00:00 | 8,530 | refs complete but 8530 members not stamped (sweeper skipped them) |
| img | urn:nasa:pds:mars2020_navcam_ops_mosaic::13.0, urn:nasa:pds:mars2020_navcam_ops_mosaic::1.1, urn:nasa:pds:mars2020_navcam_ops_mosaic::1.0 (+2 more) | urn:nasa:pds:mars2020_navcam_ops_mosaic:data::16.0 | processed | 2026-08-14T01:19:19+00:00 | 516 | refs complete but 516 members not stamped (sweeper skipped them) |
| img | urn:nasa:pds:lro-l-lroc-2-edr | urn:nasa:pds:lro-l-lroc-2-edr:lrolrc_0001_data::1.0 | stamped_empty_refs | 2026-09-16T07:39:50+00:00 | 20 | refs complete but 20 members not stamped (sweeper skipped them) |

## Stamped collections with empty refs

36 collections are stamped with the current version but have no ancestor refs. 6 of them have a bundle, so that bundle's `/members` is empty (anomaly). The other 30 have no bundle and are expected.

| Node | Bundle(s) | Collection | Harvested |
|---|---|---|---|
| img | urn:nasa:pds:artemis2_crew_camera::1.0 | urn:nasa:pds:artemis2_crew_camera:browse::1.0 | 2026-10-02T01:41:44+00:00 |
| img | urn:nasa:pds:artemis2_crew_camera::1.0 | urn:nasa:pds:artemis2_crew_camera:data_raw::1.0 | 2026-10-02T09:31:16+00:00 |
| img | urn:nasa:pds:artemis2_crew_camera::1.0 | urn:nasa:pds:artemis2_crew_camera:data_source::1.0 | 2026-10-02T14:27:04+00:00 |
| img | urn:nasa:pds:mars2020_hazcam_ops_stereo::13.0 | urn:nasa:pds:mars2020_hazcam_ops_stereo:data::16.0 | 2026-11-04T20:27:20+00:00 |
| img | urn:nasa:pds:mars2020_mastcamz_ops_stereo::13.0 | urn:nasa:pds:mars2020_mastcamz_ops_stereo:data::16.0 | 2026-11-04T20:28:45+00:00 |
| img | urn:nasa:pds:mars2020_navcam_ops_stereo::13.0 | urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 | 2026-11-04T20:27:37+00:00 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Observational | 0 | 19,122 | 19,122 |
| Product_Native | 0 | 8,671 | 8,671 |
| Product_Browse | 0 | 8,530 | 8,530 |
| Product_File_Text | 0 | 516 | 516 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| 1-7d | 0 | 20 | 20 |
| >30d | 0 | 36,819 | 36,819 |

## What each rule means

- **reloaded_after_collection** (36,323 products): The product was re-harvested after its collection was processed, so the sweeper has no reason to revisit it. Candidate fix: re-harvest the collection so the sweeper reprocesses it.
- **inventory_version_mismatch** (516 products): The collection's inventory (as recorded in registry-refs) lists this product at a different version than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the collection will not help: load the product version the inventory lists, after which the registered version is superseded. Confirm with audit_collection.py --diff.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: img
- Node filter: img
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated with no baseline (any anomaly fails).

**FAIL** - 2 invariant(s) violated.

- `no_anomalous_products`: 36,839 products are anomalous
  - reloaded_after_collection: 36,323
  - inventory_version_mismatch: 516
- `no_empty_refs_collection_with_bundle`: 6 collections with a bundle are stamped with empty refs
  - urn:nasa:pds:artemis2_crew_camera:browse::1.0
  - urn:nasa:pds:artemis2_crew_camera:data_raw::1.0
  - urn:nasa:pds:artemis2_crew_camera:data_source::1.0
  - urn:nasa:pds:mars2020_hazcam_ops_stereo:data::16.0
  - urn:nasa:pds:mars2020_mastcamz_ops_stereo:data::16.0
  - urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0
