# img node audit, 2026-11-16

## Verdict

Mostly healthy: 36,839 of 26,339,723 products the public API can show (0.14 percent) lack ancestry, meaning the registry has not recorded which collection and bundle they belong to, so they are missing from the API's `/members` lists. All are for the node: 36,323 are fixed by re-harvesting collections (EN then runs the sweepers) and 516 by loading the listed versions. None are for EN alone or the sweepers team. Separately, 6 bundles have an empty member list, and one collection's inventory disagrees with the registry for 35,109 more products.

## What needs to happen

| Who | What is wrong | Products | Collections | What to do |
|---|---|---|---|---|
| Node | The inventory of one collection lists a newer version of 516 products than the registry holds (registry has version 1.0, inventory lists 2.0 to 9.0) | 516 | 1 | Load the listed versions, or correct the inventory if 1.0 is right |
| Node | Sweepers processed these collections while the node was still loading their products; products loaded afterwards were never processed (sweepers do not revisit a processed collection) | 36,323 | 5 | Re-harvest the collections, then run the sweepers |
| Node | Collections stamped as processed with an empty ancestor list although their bundle exists, so the bundle's `/members` is empty (sweeper bug fixed in registry-sweepers PR #286) | 0 (3 of the 6 collections are also in the row above) | 6 | Re-harvest the collections, then run the sweepers that include PR #286 |
| Sweepers team | Products the sweepers skipped with no explanation in the data | 0 | 0 | None |
| Needs a closer look | Same collection as the node row: the inventory lists an older version than the registry holds, for products that already have ancestry (not counted in the 36,839) | 35,109 | 1 | Node confirms which versions the collection should contain |
| No action | Products still within the grace period, and service/context products that never have a collection | 0 | 0 | None |

Collections the node re-harvests: `urn:nasa:pds:artemis2_crew_camera:data_processed::1.0` (9,961 products), `:data_raw::1.0` (9,141), `:data_source::1.0` (8,671), `:browse::1.0` (8,530), `urn:nasa:pds:lro-l-lroc-2-edr:lrolrc_0001_data::1.0` (20). Empty-refs collections with a bundle: Artemis 2 `browse`, `data_raw`, `data_source` and `urn:nasa:pds:mars2020_{hazcam,mastcamz,navcam}_ops_stereo:data::16.0`. Collection for the node: `urn:nasa:pds:mars2020_navcam_ops_mosaic:data::16.0`.

## Details

**Products loaded after their collection was processed (36,323).**
- Sample: product `...artemis2_crew_camera:data_processed:art002e024601_nkd5015_prc.tif::1.0` has no ancestry stamp and no ancestor list; it was harvested 2026-10-02 08:43 UTC. Its collection `data_processed::1.0` was harvested 03:54 UTC, carries stamp 7 and an ancestor list naming the bundle. A refs document (the list of a collection's products that the sweepers read) names the product under that collection. The API's `/members` for the collection, filtered to this product, returns 0 hits, and the collection shows 368 members although its refs list 10,329.
- Mechanism: in each Artemis 2 collection the stamped products are exactly those harvested before one cut-off, and everything after it is unstamped. Last stamped / first unstamped harvest time: `browse` 02:04:46 / 02:04:47, `data_processed` 04:04:49 / 04:04:51, `data_raw` 10:03:46 / 10:03:48, `data_source` 15:04:27 / 15:04:30 (stamped counts 1,799, 368, 1,188, 1,658). Each collection was harvested 11 to 37 minutes before its cut-off, so the sweepers ran part-way through each load, processed the collection with the products that existed then, and never came back. The harvest times show one sequential load (collection, then its products), so "re-harvested" in the audit's rule name really means "harvested after". I did not check the sweepers' schedule.
- LROC: exactly the 20 products harvested since 2026-11-01 in `lrolrc_0001_data::1.0` (harvested 2026-11-12) are unstamped; the collection was harvested 2026-09-16 and its other 106,270 products are visible in `/members`. A sample product is in refs batch 1 and returns 0 hits from `/members`.
- Whether re-harvest plus a sweeper run fixes it follows from the documented sweeper behaviour; I did not run it (read-only audit).
- Confirm: re-run the audit; `reloaded_after_collection` falls to 0 and `/members` of each collection reports 10,329 (Artemis 2) or 106,290 (LROC).

**Empty member lists (6 collections).**
- `/members` of bundle `urn:nasa:pds:artemis2_crew_camera::1.0` returns 1 member (`data_processed`) although the bundle names 4 collections. `/members` of the `mars2020_{hazcam,mastcamz,navcam}_ops_stereo::13.0` bundles returns 0 members. The six collections have stamp 7 and an empty ancestor list in the registry.
- I could not establish the cause. The three stereo collections were re-harvested on 2026-11-04 after their bundles, the pattern in the playbook for the PR #286 bug. The Artemis 2 bundle was harvested at 03:54 on 2026-10-02, before `data_raw` and `data_source` but after `browse`, so load order does not explain all three. I could not verify whether the sweepers now deployed include PR #286.
- 30 `lro-l-lroc-2-edr` collections are also stamped with empty refs but no bundle exists in the registry (the API returns 404 for it), so the audit treats them as expected. When that bundle is loaded, those collections will already be processed and the bundle's `/members` will be empty unless they are re-harvested first.
- Confirm: `/members` of each bundle lists all its collections, and the audit's stamped-with-empty-refs list is empty for bundles.

**Version mismatch (516, node).**
- Sample `...mars2020_navcam_ops_mosaic:data:n_lrgb_1764xxyz_0840000_cyl_l_autogenj.lis::1.0`: the registry holds only version 1.0 (not superseded, harvested 2026-08-14). No refs document lists that LIDVID; one lists the same LID under `data::16.0`. The collection inventory lists version 6.0.
- `audit_collection.py --diff` on the collection: inventory 54,030 LIDVIDs, registry 54,030 non-superseded, 35,625 on each side of the difference. All 516 products are in the registry-only list; all 516 are text (`.lis`) products held at 1.0 while the inventory lists 2.0 to 9.0 (186 list 2.0, 113 list 3.0, 75 list 4.0).
- Load status: 18,405 inventory products are loaded, the newest harvested 94.8 days before the check, so nothing is loading right now (3-day window). Do not read "35,625 not loaded" as 35,625 missing products; see the next item.
- Confirm: the 516 leave the audit once the listed versions are loaded (the old 1.0 versions are then superseded).

**Inventory older than the registry (35,109, closer look).**
- For 35,109 products in the same collection the registry holds a higher version than the inventory lists (for example registry 2.1, inventory 2.0). In the sample, 2.0 is marked superseded by 2.1 and 2.1 has ancestry naming collection 12.1, not 16.0, so it does not appear in `/members` of 16.0 (API reports 18,405 of 54,030). They are not in the audit count because they have ancestry. Whether the inventory or the registry is wrong is for the node to say; I checked one product.
- Confirm: `/members` of the collection approaches the inventory row count.

## Index mapping

- One error-level problem: `img:Exposure/img:exposure_duration_count` is a whole-number type (`long`) on img and atm, and a decimal type (`double`) on geo and sbnpsi. In img the values are whole numbers (sampled top values 0, 1, 3, 10, 200; examples 173, 188, 214), so img itself is unaffected. A search across several nodes' indices on this field may behave differently per node; I did not test that.
- No error-level missing fields on img (the `superseded_by` and `vid` errors are atm's) and none on `img-registry-refs`.
- 22 warning-level fields are absent from img but present on most nodes, mainly table and binary-record descriptions (`pds:Table_Binary/*`, `pds:Field_Binary/*`, `pds:Record_Binary/*`) plus `pds:Collection/pds:description` and `ref_lid_facility`. Products carrying them can be fetched but those fields cannot be searched on img. I did not check whether img holds such products.
- Owner: EN with the index owners; none of this blocks the actions above.

<!-- product-samples:start -->
## Example products

Up to 3 products from each of the 6 largest problem groups of 6 (one rule in one collection, node problems first). Every group, with up to 10 products and the reason for each, is in [`product_samples.csv`](../audit-output/img/product_samples.csv).

| Who | Rule | Collection | Products in group | Examples |
|---|---|---|--:|---|
| Node | `reloaded_after_collection` | `urn:nasa:pds:artemis2_crew_camera:data_processed::1.0` | 9,961 | `urn:nasa:pds:artemis2_crew_camera:data_processed:art002e004437_nkd5015_prc.tif::1.0`<br>`urn:nasa:pds:artemis2_crew_camera:data_processed:art002e004438_nkd5015_prc.tif::1.0`<br>`urn:nasa:pds:artemis2_crew_camera:data_processed:art002e004439_nkd5017_prc.tif::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:artemis2_crew_camera:data_raw::1.0` | 9,141 | `urn:nasa:pds:artemis2_crew_camera:data_raw:art002e009179_nkd5017_raw.tif::1.0`<br>`urn:nasa:pds:artemis2_crew_camera:data_raw:art002e009180_nkd5017_raw.tif::1.0`<br>`urn:nasa:pds:artemis2_crew_camera:data_raw:art002e009181_nkd5017_raw.tif::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:artemis2_crew_camera:data_source::1.0` | 8,671 | `urn:nasa:pds:artemis2_crew_camera:data_source:art002e009276_nkd5017_src.nef::1.0`<br>`urn:nasa:pds:artemis2_crew_camera:data_source:art002e009277_nkd5015_src.nef::1.0`<br>`urn:nasa:pds:artemis2_crew_camera:data_source:art002e009278_nkd5015_src.nef::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:artemis2_crew_camera:browse::1.0` | 8,530 | `urn:nasa:pds:artemis2_crew_camera:browse:art002e009624_nkd5015_prc.png::1.0`<br>`urn:nasa:pds:artemis2_crew_camera:browse:art002e009625_nkd5015_prc.png::1.0`<br>`urn:nasa:pds:artemis2_crew_camera:browse:art002e009626_nkd5015_prc.png::1.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:mars2020_navcam_ops_mosaic:data::16.0` | 516 | `urn:nasa:pds:mars2020_navcam_ops_mosaic:data:n_lrgb_1756_fdr_0831252_cyl_l_autogenj.lis::1.0`<br>`urn:nasa:pds:mars2020_navcam_ops_mosaic:data:n_lrgb_1756_fdr_0831252_cyl_l_hrestopj.lis::1.0`<br>`urn:nasa:pds:mars2020_navcam_ops_mosaic:data:n_lrgb_1756_fdr_0831252_cyp_r_autogenj.lis::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:lro-l-lroc-2-edr:lrolrc_0001_data::1.0` | 20 | `urn:nasa:pds:lro-l-lroc-2-edr:lrolrc_0001_data:wac.m101013765ce::2.0`<br>`urn:nasa:pds:lro-l-lroc-2-edr:lrolrc_0001_data:wac.m101014131ce::2.0`<br>`urn:nasa:pds:lro-l-lroc-2-edr:lrolrc_0001_data:wac.m101014500ce::2.0` |

<!-- product-samples:end -->

## Reproduce

```bash
ENV_FILE="<path-to-registry-client-env-file>"
REGISTRY_CLIENT_VENV="<path-to-registry-client-venv>"
PYTHON="${REGISTRY_CLIENT_VENV}/bin/python"
REGISTRY_CLIENT="${REGISTRY_CLIENT_VENV}/bin/pds-registry-client"
API_BASE="https://pds.mcp.nasa.gov/api/search/1"
OUT_DIR="./audit_unprocessed/img"
COLLECTION_LIDVID="urn:nasa:pds:mars2020_navcam_ops_mosaic:data::16.0"
BUNDLE_ENCODED="urn%3Anasa%3Apds%3Aartemis2_crew_camera%3A%3A1.0"
source "${ENV_FILE}"

# Unprocessed-product audit (no inventory downloads; the 516 mismatches are found through refs)
"${PYTHON}" scripts/audit_unprocessed_products.py --output-dir "${OUT_DIR}" --node img --gzip --no-inventory

# Inventory versus registry, and whether a load is running, for the mosaic collection
"${PYTHON}" scripts/audit_collection.py "${COLLECTION_LIDVID}" --diff --load-status --active-days 3 --output-dir "${OUT_DIR}/collection_audit"

# Bundle member list (hits is the number of members)
curl -s -G "${API_BASE}/products/${BUNDLE_ENCODED}/members" --data-urlencode "limit=1" | jq '.summary.hits'

# Harvest time of the newest stamped product in a collection (the cut-off); change the lid prefix per collection
LID_PREFIX="urn:nasa:pds:artemis2_crew_camera:data_processed:*"
BODY="$(jq -n --arg p "${LID_PREFIX}" '{size: 0, query: {bool: {filter: [{wildcard: {lid: $p}},
  {term: {"ops:Provenance/ops:registry_sweepers_ancestry_version": "7"}},
  {exists: {field: "ops:Provenance/ops:ancestor_refs"}}]}},
  aggs: {newest: {max: {field: "ops:Harvest_Info/ops:harvest_date_time"}}}}')"
"${REGISTRY_CLIENT}" -d "${BODY}" /img-registry/_search | jq '.aggregations.newest.value_as_string'
```

Per-product checks (`show_doc`, `show_refs`, `api_member_hits`) are in the verification toolkit of `audit-unprocessed-products-reference.md`.
