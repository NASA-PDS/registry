# atm node audit, 2026-11-16

Tracking issue: NASA-PDS/registry#610, which has the per-collection tables.

## Verdict

2,784,370 API-visible products have no ancestry (they are missing from their collection's and bundle's `/members`). 2,782,642 of them are the node's to fix: the registry holds one version of each product and the collection's inventory lists another, so the node has to finish or correct its loads. Nothing is currently loading. The earlier repair of collections stamped without a link to their bundle is complete.

## What needs to happen

"Ancestry" is the parent link (collection, bundle) the sweepers add to each product. "Refs" are the registry's copy of each collection's inventory, written when the collection is harvested; the sweepers reach a product only through them.

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | The collection's inventory lists a different version of these products than the one loaded (16 `maven.iuvs.*` collections) | 2,765,640 | 16 | Load the version the inventory lists, or correct the inventory |
| Node | The collection's inventory does not list these products under any version | 16,960 | 8 | Add them to the inventory, or remove the products from the registry |
| Node | No collection with the identifier these products belong to is in the registry (`juno_uvs:data_raw`) | 42 | 1 | Load the collection, or correct the product identifiers |
| Sweepers team | The collection's inventory lists a product by LID without a version, which the sweepers do not follow (`maven.iuvs.kp:document:sis::7.0`) | 1 | 1 | The node lists a LIDVID, or the sweepers support LID references (registry-sweepers#299) |
| Needs a closer look | Two products of the `pds-ama:sample_bundle` sample have no refs and their collection's inventory cannot be downloaded (the files were loaded from a local path) | 2 | 1 | Decide whether the sample stays in the registry (see NASA-PDS/registry#614) |
| Registry operations | None | 0 | 0 | - |
| No action | Harvested in the last week in `maven.iuvs.processed:occultation::13.0`, within the grace period | 1,725 | 1 | Re-check later |

## Details

- **Why the node's counts are so high.** The 2,765,640 products belong mostly to `maven.iuvs.raw:disk::13.0` and `:limb::13.0` (about 1.3 million together) and the other `maven.iuvs.*` `::13.0` collections. Each collection's inventory lists product versions that are not loaded; the sweepers reach only the products the inventory lists. Re-harvesting does not help. Of the 22 collections that are partially loaded or not started, none is loading: where there are loaded members, the newest was harvested 130 to 535 days ago.
- **Registered but not listed (16,960).** Eight collections, the largest `juno_mwr:data_calibrated::2.1` (6,130, superseded by `::3.0`), `maven_ngims:l1b::1.0` (4,622) and `juno_mwr:data_raw::2.0` (3,065).
- **Repair of empty-refs collections.** All 45 collections that had a bundle but empty `ancestor_refs` now have the bundle in `ancestor_refs`: 44 after the re-harvest and the sweeper run with registry-sweepers PR #286, and `juno_mwr:document::3.0` on 2026-11-16. The audit lists none.
- **Confirm a fix.** Re-run `audit_unprocessed_products.py --node atm --check --baseline <this run's metrics.json>`; the node rows should shrink as loads complete.

## Index mapping

`atm-registry` (concrete index `temp-atm-registry`) has two error-level problems: `ops:Provenance/ops:superseded_by` and `vid` are not mapped, so superseded products cannot be excluded in searches and `vid` cannot be searched or sorted (NASA-PDS/registry#611). It also has 2 warning-level missing fields and one type conflict (`img:Exposure/img:exposure_duration_count` is `long` here and on `img`, `double` on `geo` and `sbnpsi`). Owner: registry operations, by mapping the two fields and rewriting the documents.

<!-- product-samples:start -->
## Example products

Up to 3 products from each of the 10 largest problem groups of 27 (one rule in one collection, node problems first). Every group, with up to 10 products and the reason for each, is in [`product_samples.csv`](../audit-output/atm/product_samples.csv).

| Who | Rule | Collection | Products in group | Examples |
|---|---|---|--:|---|
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.raw:disk::13.0` | 662,080 | `urn:nasa:pds:maven.iuvs.raw:disk:mvn_iuv_l1a_apoapse-orbit00107-fuv_20141018t084026::13.1`<br>`urn:nasa:pds:maven.iuvs.raw:disk:mvn_iuv_l1a_apoapse-orbit00107-fuv_20141018t084402::13.1`<br>`urn:nasa:pds:maven.iuvs.raw:disk:mvn_iuv_l1a_apoapse-orbit00107-fuv_20141018t085130::13.1` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.raw:limb::13.0` | 652,875 | `urn:nasa:pds:maven.iuvs.raw:limb:mvn_iuv_l1a_inlimb-orbit03442-fuv_20160706t060729::13.0`<br>`urn:nasa:pds:maven.iuvs.raw:limb:mvn_iuv_l1a_inlimb-orbit03442-fuv_20160706t060934::13.0`<br>`urn:nasa:pds:maven.iuvs.raw:limb:mvn_iuv_l1a_inlimb-orbit03442-fuvdark_20160706t061138::13.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.calibrated:disk::13.0` | 572,804 | `urn:nasa:pds:maven.iuvs.calibrated:disk:mvn_iuv_l1b_apoapse-orbit00107-fuv_20141018t084026::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:disk:mvn_iuv_l1b_apoapse-orbit00107-fuv_20141018t084402::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:disk:mvn_iuv_l1b_apoapse-orbit00107-fuv_20141018t085130::13.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.calibrated:limb::13.0` | 564,930 | `urn:nasa:pds:maven.iuvs.calibrated:limb:mvn_iuv_l1b_inlimb-orbit03190-fuv_20160520t144707::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:limb:mvn_iuv_l1b_inlimb-orbit03190-fuv_20160520t144912::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:limb:mvn_iuv_l1b_inlimb-orbit03190-muv_20160520t144707::13.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.raw:calibration::13.0` | 70,966 | `urn:nasa:pds:maven.iuvs.raw:calibration:mvn_iuv_l1a_centroid-orbit00420-muvdark_20141217t073310::13.0`<br>`urn:nasa:pds:maven.iuvs.raw:calibration:mvn_iuv_l1a_centroid-orbit00421-muvdark_20141217t102809::13.0`<br>`urn:nasa:pds:maven.iuvs.raw:calibration:mvn_iuv_l1a_centroid-orbit00424-muvdark_20141218t015237::13.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.raw:echelle::13.0` | 68,592 | `urn:nasa:pds:maven.iuvs.raw:echelle:mvn_iuv_l1a_apoapse-orbit00727-echdark_20150213t191758::13.0`<br>`urn:nasa:pds:maven.iuvs.raw:echelle:mvn_iuv_l1a_apoapse-orbit00729-echdark_20150214t042312::13.0`<br>`urn:nasa:pds:maven.iuvs.raw:echelle:mvn_iuv_l1a_apoapse-orbit00737-echdark_20150215t163859::13.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.calibrated:calibration::13.0` | 62,437 | `urn:nasa:pds:maven.iuvs.calibrated:calibration:mvn_iuv_l1b_centroid-orbit00458-fuv_20141224t133833::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:calibration:mvn_iuv_l1b_centroid-orbit00462-fuv_20141225t075759::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:calibration:mvn_iuv_l1b_centroid-orbit00466-fuv_20141226t021718::13.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.calibrated:echelle::13.0` | 41,947 | `urn:nasa:pds:maven.iuvs.calibrated:echelle:mvn_iuv_l1b_apoapse-orbit01274-ech_20150527t050045::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:echelle:mvn_iuv_l1b_apoapse-orbit01274-ech_20150527t052719::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:echelle:mvn_iuv_l1b_apoapse-orbit01274-ech_20150527t055351::13.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.raw:corona::13.0` | 28,542 | `urn:nasa:pds:maven.iuvs.raw:corona:mvn_iuv_l1a_incorona-orbit03442-fuv_20160706t054634::13.0`<br>`urn:nasa:pds:maven.iuvs.raw:corona:mvn_iuv_l1a_incorona-orbit03442-fuvdark_20160706t054600::13.0`<br>`urn:nasa:pds:maven.iuvs.raw:corona:mvn_iuv_l1a_incorona-orbit03442-muv_20160706t054634::13.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:maven.iuvs.calibrated:corona::13.0` | 17,617 | `urn:nasa:pds:maven.iuvs.calibrated:corona:mvn_iuv_l1b_incorona-orbit03190-fuv_20160520t142612::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:corona:mvn_iuv_l1b_incorona-orbit03190-muv_20160520t142612::13.0`<br>`urn:nasa:pds:maven.iuvs.calibrated:corona:mvn_iuv_l1b_incorona-orbit03442-fuv_20160706t054634::13.0` |

<!-- product-samples:end -->

## Reproduce

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
OUTPUT_DIR="./audit_atm/"
source "${ENV_FILE}"
python scripts/audit_unprocessed_products.py --output-dir "${OUTPUT_DIR}" --node atm --gzip --check --inventory-cache-dir "./inventory_cache/"
```

The run reads provider inventories and takes over an hour on ATM. The audit output (`summary.md`, `metrics.json`, `collections.csv`, `anomalous_collections.txt`) is in `../audit-output/atm/`; the 2.78-million-row per-product CSV is not committed.
