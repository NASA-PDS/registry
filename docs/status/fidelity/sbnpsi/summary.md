# Unprocessed product audit

Run time: 2026-11-16T22:23:53+00:00
Nodes: sbnpsi

- Candidates examined: **98**
- Expected (should resolve on their own): **29**
- Anomalous (need attention): **69**

## What needs to happen

**Needs attention: 69 products for the node.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Not processed**: Linked to their collection, but processed by an older sweepers version while the collection is on the current one, so the sweepers do not go back | 67 | 9 | Re-harvest the collection; EN then runs the sweepers |
| Node | **Orphaned**: The collection's inventory does not list these products under any version | 1 | 1 | Add them to the inventory, or remove the products from the registry |
| Node | **Orphaned**: No collection with the identifier these products belong to is in the registry | 1 | 1 | Load the collection, or correct the product identifiers |
| No action | **Waiting**: Product classes that never belong to a collection | 29 | - | None |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.
- **Not processed**: the registry's refs list the product, so its collection is confirmed, but the sweepers never gave it ancestry.
- **Waiting**: loaded recently; expected to resolve by itself.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory), or the collection has to be re-harvested by the node so that the registry's refs are rewritten from its inventory; EN then runs the sweepers.
- **No action**: loaded recently; expected to resolve by itself.

## Anomalies by rule

| Rule | Products |
|---|---|
| collection_not_loaded_overdue | 1 |
| not_in_collection_inventory | 1 |
| stale_stamp | 67 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| collection_not_loaded_overdue | sbnpsi | 1 |
| not_in_collection_inventory | sbnpsi | 1 |
| stale_stamp | sbnpsi | 67 |

## Anomalous collections

10 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

9 of them are superseded collection versions. Their products are still API-visible, but a superseded version is not re-harvested, so it is left out of `anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| sbnpsi | urn:nasa:pds:iue.ast.hendrix.spectra, urn:nasa:pds:iue.ast.hendrix.spectra::1.0, urn:nasa:pds:iue.ast.hendrix.spectra::2.0 | urn:nasa:pds:iue.ast.hendrix.spectra:document::1.0 | processed (superseded) | 2022-07-20T22:23:55+00:00 | 21 | refs missing for 136 members (refs never written) |
| sbnpsi | urn:nasa:pds:iue.ast.hendrix.spectra, urn:nasa:pds:iue.ast.hendrix.spectra::1.0, urn:nasa:pds:iue.ast.hendrix.spectra::2.0 | urn:nasa:pds:iue.ast.hendrix.spectra:data::1.0 | processed (superseded) | 2022-07-20T22:23:54+00:00 | 16 | refs missing for 110 members (refs never written) |
| sbnpsi | urn:nasa:pds:neowise_diameters_albedos, urn:nasa:pds:neowise_diameters_albedos::1.0, urn:nasa:pds:neowise_diameters_albedos::2.0 | urn:nasa:pds:neowise_diameters_albedos:data::1.0 | processed (superseded) | 2022-07-20T22:22:09+00:00 | 8 | refs missing for 9 members (refs never written) |
| sbnpsi | urn:nasa:pds:smallbodiesoccultations, urn:nasa:pds:smallbodiesoccultations::3.0, urn:nasa:pds:smallbodiesoccultations::1.0 (+2 more) | urn:nasa:pds:smallbodiesoccultations:data::1.0 | processed (superseded) | 2022-07-20T22:21:53+00:00 | 6 | refs missing for 22 members (refs never written) |
| sbnpsi | urn:nasa:pds:smallbodiesoccultations, urn:nasa:pds:smallbodiesoccultations::3.0, urn:nasa:pds:smallbodiesoccultations::1.0 (+2 more) | urn:nasa:pds:smallbodiesoccultations:data::2.0 | processed (superseded) | 2022-07-20T22:21:58+00:00 | 6 | refs missing for 22 members (refs never written) |
| sbnpsi | urn:nasa:pds:smallbodiesoccultations, urn:nasa:pds:smallbodiesoccultations::3.0, urn:nasa:pds:smallbodiesoccultations::1.0 (+2 more) | urn:nasa:pds:smallbodiesoccultations:data::3.0 | processed (superseded) | 2022-07-20T22:24:05+00:00 | 6 | refs missing for 22 members (refs never written) |
| sbnpsi | urn:nasa:pds:neowise_diameters_albedos, urn:nasa:pds:neowise_diameters_albedos::1.0, urn:nasa:pds:neowise_diameters_albedos::2.0 | urn:nasa:pds:neowise_diameters_albedos:document::1.0 | processed (superseded) | 2022-07-20T22:22:10+00:00 | 2 | refs missing for 5 members (refs never written) |
| sbnpsi | urn:nasa:pds:hst.ast-ceres.uv-spectra::1.0, urn:nasa:pds:hst.ast-ceres.uv-spectra | urn:nasa:pds:hst.ast-ceres.uv-spectra:document::1.0 | processed | 2026-10-09T00:19:14+00:00 | 1 | refs missing for 1 members (refs never written) |
| sbnpsi | urn:nasa:pds:smallbodiesoccultations, urn:nasa:pds:smallbodiesoccultations::3.0, urn:nasa:pds:smallbodiesoccultations::1.0 (+2 more) | urn:nasa:pds:smallbodiesoccultations:document::1.0 | processed (superseded) | 2022-07-20T22:21:54+00:00 | 1 | refs missing for 2 members (refs never written) |
| sbnpsi | urn:nasa:pds:smallbodiesoccultations, urn:nasa:pds:smallbodiesoccultations::3.0, urn:nasa:pds:smallbodiesoccultations::1.0 (+2 more) | urn:nasa:pds:smallbodiesoccultations:document::3.0 | processed (superseded) | 2022-07-20T22:24:06+00:00 | 1 | refs missing for 2 members (refs never written) |

## Orphans

1 products belong to 1 collection LIDs that have no API-visible collection. These are not sweeper bugs: the collection has to be loaded first.

| Collection LID | Node | Overdue | Pending | Products |
|---|---|---|---|---|
| urn:nasa:pds:system_bundle:xml_schema | sbnpsi | 1 | 0 | 1 |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Observational | 0 | 42 | 42 |
| Product_Context | 29 | 0 | 29 |
| Product_Document | 0 | 26 | 26 |
| Product_XML_Schema | 0 | 1 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| >30d | 29 | 69 | 98 |

## What each rule means

- **no_parent_by_design** (29 products): These product classes never belong to a collection, so they never receive ancestry. No action is needed.
- **collection_not_loaded_overdue** (1 products): The parent collection is still not in the registry (or is not API-visible) long after the product was harvested. Check whether the collection failed to load, is staged or superseded, or whether the product LID does not follow the bundle:collection:product pattern.
- **not_in_collection_inventory** (1 products): The product is registered under this collection's LID, but the collection's current inventory does not list it under any version, so the sweeper can never give it this collection as an ancestor. The provider may have dropped it from the inventory or it may be a leftover. The node should decide whether it belongs in the inventory or should be removed from the registry; re-harvesting or loading more products will not fix it.
- **stale_stamp** (67 products): The product carries an ancestry stamp from an older sweeper version although its collection is already on the current version. The collection will not be revisited, so a re-sweep of the collection may be needed.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: sbnpsi
- Node filter: sbnpsi
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated with no baseline (any anomaly fails).

**FAIL** - 1 invariant(s) violated.

- `no_anomalous_products`: 69 products are anomalous
  - stale_stamp: 67
  - collection_not_loaded_overdue: 1
  - not_in_collection_inventory: 1
