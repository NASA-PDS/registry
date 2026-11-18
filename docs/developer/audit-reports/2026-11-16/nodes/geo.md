# geo node audit, 2026-11-16

## Verdict

Mostly healthy. 1,373 of about 10.6 million visible products (0.013%) are missing "ancestry" (the record of which collection and bundle a product belongs to, which the public API needs for `/members` and `/ancestors`). The 1,373 split as: 1,324 for the node (1,322 data problems and 2 products fixed by re-harvesting, plus 2 collections to re-harvest), and 49 for the sweepers team (or the node: see Details). The final audit output in `../audit-output/geo/` read the collection inventories; an earlier run without them labelled some of these differently, and every group below was also checked against the collection's current inventory by hand.

## What needs to happen

Terms: the inventory is the list of products in a collection, published by the node. The refs are the registry's copy of that list, written when the collection is harvested. The sweepers are the scheduled scripts that add ancestry; they reach a product only through the refs, and never revisit a collection they have already processed.

| Who | What is wrong | Products | Collections | What to do |
|---|---|---|---|---|
| Node | The inventory lists older product versions (1.0) than the registry shows as current (1.1, 2.0, 4.0). The older versions are already loaded and carry ancestry, but the registry hides them behind the newer ones. The provider's current labels are the older versions | 1,152 | 3 | Confirm which version is intended. If the older ones are: EN removes the newer versions. If the newer ones: fix the labels and the inventory, then re-harvest |
| Node | 168 products are registered under a collection but are in none of its inventory entries, and their labels now return 404 at the provider | 168 | 1 | Say whether they are retired. If yes, EN removes them; if not, add them to the inventory and re-harvest |
| Node | 2 products belong to a collection that is not loaded in `geo-registry` | 2 | 2 | Load the collection, or fix the product ids |
| EN | 2 collections are marked as swept but have no ancestors, and their bundle does not list them as members | 0 (4 products already counted in row 1) | 2 | EN re-harvests both and runs the sweepers with the registry-sweepers PR #286 fix |
| Node | 2 products carry an old ancestry stamp (version 3) | 2 | 1 | Re-harvest the collection and EN runs the sweepers (or EN runs them in overwrite mode), but expect no change until row 1 is settled (same stale versions) |
| Sweepers team | MESSENGER document collections: the inventories list the products by id without a version; the refs store them the same way and the sweepers read only versioned ids (registry-sweepers#299) | 49 | 11 | Decide between two fixes (see Details) |
| Needs a closer look | None | 0 | 0 | - |
| No action | None | 0 | 0 | - |

Collections, row 1: `mars2020_mission:calibration_camera::1.1` (1,127), `mars2020_mission:miscellaneous::1.1` (21), `mars2020_mission:document_camera::16.0` (4).
Row 2: `mars2020_mission:calibration_camera::1.1`. Row 3: `urn:nasa:pds:messenger:document` (1 product), `urn:nasa:pds:system_bundle:xml_schema` (1 product).
EN re-harvests: `mars2020_mission:document_camera::16.0`, `mars2020_rimfax:document::16.0`. Node (re-harvest, then EN runs the sweepers): stale stamp in `mars2020_mission:miscellaneous::1.1`.
Sweepers team: the 11 `urn:nasa:pds:mess_*:document::1.0` collections (grs, mla, ns, rs and xrs bundles in their raw, calibrated and derived variants); the largest are `mess_grs_derived` (8) and `mess_rs_derived` (6).

## Details

**Row 1 (older versions listed, newer shown).** Run: `audit_collection.py --diff --load-status` on the three collections.
- Calibration camera: the inventory has 1,127 entries, all `::1.0`. The registry shows 1,041 of those products at 1.1, 85 at 2.0 and 1 at 4.0. The API `/members` of the collection returns 0.
- All 1,127 `::1.0` ids are in the registry, archived, marked as replaced by the newer version, with ancestry, harvested 2026-09 (Harvest 5.2.0-SNAPSHOT). The newer versions were harvested 2025-08 (Harvest 4.0.7) and have none.
- I downloaded the provider's current label for 166 of them (all 86 not at 1.1, plus 80 of 1.1). Every one says `version_id` 1.0 and its md5 equals the registry's `::1.0` document, not the shown one. Example: `fm102_flat_raw_bias_mask` label is 1,641 bytes, md5 `91f81106581a690d5623866f63e20cbd`; the shown 1.1 document has md5 `95551badce29f23ea71502648b3acbeb`.
- Same result for `miscellaneous` (23 of 23 shown versions, including the 2 old-stamp ones) and `document_camera` (5 of 5).
- Not verified: why the registry holds the newer versions, or whether the provider reverted on purpose. Whether the older documents become visible after the newer ones are removed depends on the sweepers recomputing "replaced by"; I did not test it.
- Fixed when: the next audit lists none of these, and `/products/<collection lidvid>/members` returns the inventory count (1,127).

**Row 2 (168 not in inventory).** The 168 are `::1.0` documents harvested 2022-11 and 2023-07, with no ancestry and in no refs document (by id or by versioned id). The inventory has no entry for them under any version. I requested all 168 label URLs: 168 returned 404. Fixed when: they leave the audit.

**Row 3 (collection missing).** `urn:nasa:pds:messenger:document::1.0` exists only in `ppi-registry` (archived), and its `/members` does not list the geo product. `urn:nasa:pds:system_bundle:xml_schema` is in no registry index. Fixed when: the audit shows no `collection_not_loaded_overdue`.

**EN re-harvest (empty-refs collections), and the node for the old-stamp products.** `mars2020_mission:document_camera::16.0` and `mars2020_rimfax:document::16.0` are stamped with current version and empty ancestors, and each has a bundle. The bundle `/members` is not empty: `mars2020_mission::4.0` returns 3 collections and `mars2020_rimfax::1.0` returns 4; the stamped collection is the one missing from each. Fixed when: the bundle's `/members` includes it and `empty_refs_with_bundle` is empty in `metrics.json`. The 2 old-stamp products (`mipl_browse.vm::2.0`, `msam_velocity_macros.vmac::8.0`) have provider labels at 1.0 too.

**Sweepers team (49 products, 11 collections).** All 49 are in their collection's current inventory, but as an id without a version (0 of the entries carry a version). The refs documents of all 11 collections have `product_lid` and no `product_lidvid`. The sweepers' source (`develop`) reads only `product_lidvid`, so these are never selected, and a re-harvest alone would write the same refs (not tested). Fix options: (a) the node lists exact versioned ids in the inventories, then the node re-harvests and EN runs the sweepers; or (b) the sweepers team resolves unversioned refs to the latest version. Fixed when: the 49 leave the audit.

## Index mapping

`geo-registry` has no missing fields. It has 2 error-level type mismatches, both `keyword` where the other nodes use `integer`: `insight:Observation_Information/insight:release_number` (integer in en, ppi, temp-atm) and `insight:Observation_Information/insight:spacecraft_clock_count_partition` (integer in en, ppi). On geo these cannot be searched as numbers (no range queries, string ordering), and a search across all nodes mixes types. `img:Exposure/img:exposure_duration_count` is `double` on geo and sbnpsi, `long` on img and temp-atm (reported against img and temp-atm). Owner: EN with the index owners; changing a type needs a new index and reindex.

<!-- product-samples:start -->
## Example products

Up to 3 products from each of the 10 largest problem groups of 17 (one rule in one collection, node problems first). Every group, with up to 10 products and the reason for each, is in [`product_samples.csv`](../audit-output/geo/product_samples.csv).

| Who | Rule | Collection | Products in group | Examples |
|---|---|---|--:|---|
| Node | `inventory_version_mismatch` | `urn:nasa:pds:mars2020_mission:calibration_camera::1.1` | 1,127 | `urn:nasa:pds:mars2020_mission:calibration_camera:fm102_flat_raw_bias_mask::1.1`<br>`urn:nasa:pds:mars2020_mission:calibration_camera:fm102_flat_rgb_bias_mask::1.1`<br>`urn:nasa:pds:mars2020_mission:calibration_camera:fm103_flat_raw_bias_mask::1.1` |
| Node | `not_in_collection_inventory` | `urn:nasa:pds:mars2020_mission:calibration_camera::1.1` | 168 | `urn:nasa:pds:mars2020_mission:calibration_camera:heli_nav_fm_mframe.cahvore::1.0`<br>`urn:nasa:pds:mars2020_mission:calibration_camera:l0_0000_cont_v1::1.0`<br>`urn:nasa:pds:mars2020_mission:calibration_camera:l0_0660_cont_v1::1.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:mars2020_mission:miscellaneous::1.1` | 21 | `urn:nasa:pds:mars2020_mission:miscellaneous:ancillary_file_text.vm::2.0`<br>`urn:nasa:pds:mars2020_mission:miscellaneous:cal_file_image.vm::3.0`<br>`urn:nasa:pds:mars2020_mission:miscellaneous:cal_file_text.vm::2.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:mars2020_mission:document_camera::16.0` | 4 | `urn:nasa:pds:mars2020_mission:document_camera:helicam_release_notes.txt::12.0`<br>`urn:nasa:pds:mars2020_mission:document_camera:mars2020_camera_bundle_sis.pdf::3.0`<br>`urn:nasa:pds:mars2020_mission:document_camera:mars2020_camera_sis_pipeline_flow.pdf::2.0` |
| Node | `collection_not_loaded_overdue` | `(none found)` | 2 | `urn:nasa:pds:messenger:document:geo_notes_and_errata::1.0`<br>`urn:nasa:pds:system_bundle:xml_schema:speclib-xml_schema_1.22.0.0_1.5.0.0::1.0` |
| Node | `stale_stamp` | `urn:nasa:pds:mars2020_mission:miscellaneous::1.1` | 2 | `urn:nasa:pds:mars2020_mission:miscellaneous:mipl_browse.vm::2.0`<br>`urn:nasa:pds:mars2020_mission:miscellaneous:msam_velocity_macros.vmac::8.0` |
| Sweepers team | `bare_lid_in_inventory` | `urn:nasa:pds:mess_grs_derived:document::1.0` | 8 | `urn:nasa:pds:mess_grs_derived:document:geometry_info::1.0`<br>`urn:nasa:pds:mess_grs_derived:document:grs_cdr-rdr-dap_sis::1.0`<br>`urn:nasa:pds:mess_grs_derived:document:mess_grs_cdr_rdr_ds::1.0` |
| Sweepers team | `bare_lid_in_inventory` | `urn:nasa:pds:mess_rs_derived:document::1.0` | 6 | `urn:nasa:pds:mess_rs_derived:document:mess_rs_inst::1.0`<br>`urn:nasa:pds:mess_rs_derived:document:mess_rs_occsum_sis::1.0`<br>`urn:nasa:pds:mess_rs_derived:document:mess_rs_rdr_ds::1.0` |
| Sweepers team | `bare_lid_in_inventory` | `urn:nasa:pds:mess_mla_calibrated:document::1.0` | 5 | `urn:nasa:pds:mess_mla_calibrated:document:jp2info::1.0`<br>`urn:nasa:pds:mess_mla_calibrated:document:mess_mla_cdr_rdr_ds::1.0`<br>`urn:nasa:pds:mess_mla_calibrated:document:mess_mla_gdr_v1_ds::1.0` |
| Sweepers team | `bare_lid_in_inventory` | `urn:nasa:pds:mess_mla_derived:document::1.0` | 5 | `urn:nasa:pds:mess_mla_derived:document:jp2info::1.0`<br>`urn:nasa:pds:mess_mla_derived:document:mess_mla_gdr_v2_ds::1.0`<br>`urn:nasa:pds:mess_mla_derived:document:mess_mla_rdr_ds::1.0` |

<!-- product-samples:end -->

## Reproduce

```bash
ENV_FILE="<path-to-registry-client-env-file>"
PYTHON="<path-to-registry-client-venv>/bin/python"
OUT_DIR="<output-directory>"
COLLECTION_LIDVID="urn:nasa:pds:mars2020_mission:calibration_camera::1.1"
API_BASE="https://pds.mcp.nasa.gov/api/search/1"
source "${ENV_FILE}"
"${PYTHON}" scripts/audit_unprocessed_products.py --output-dir "${OUT_DIR}" --node geo --gzip --no-inventory
"${PYTHON}" scripts/audit_collection.py "${COLLECTION_LIDVID}" --diff --load-status --active-days 14 --output-dir "${OUT_DIR}/collection_audit"
curl -s -G "${API_BASE}/products/${COLLECTION_LIDVID}/members" --data-urlencode "limit=1"
```

Provider label check: set `LABEL_URL` to a product's `label_url` from `${API_BASE}/products/<lidvid>`, run `curl -s -o label.xml "${LABEL_URL}"`, then `md5 label.xml` (or `md5sum`) and compare with `ops:Label_File_Info.ops:md5_checksum` of each version's API document. Refs check: send `{"size":2,"query":{"term":{"collection_lidvid":"<collection lidvid>"}}}` to `/geo-registry-refs/_search` with `pds-registry-client -d @<query-file>` and look for `product_lidvid`.
Note: `audit_collection.py` sends `Accept: application/json`, and the data provider answers the inventory download with HTTP 406. I ran it with that header set to `*/*`; without that, `--diff` cannot run for these collections.
