# sbnumd node audit, 2026-11-16

## Verdict

Products are healthy, but bundle pages are not: 25 of 2,121,887 products need attention (all 25 for the node: 1 data problem and 24 fixed by re-harvesting, after which EN runs the sweepers; 0 for the sweepers team), and 58 collections are missing their link to their bundle, so 8 bundles list few or none of their collections through the public API. Superseded (replaced) versions are not counted.

Terms: "ancestry" is the list of parents (collection, bundle) that the ancestry sweeper writes on each product; a product without it is missing from its parent's `/members` list in the public API. "Refs" are the member lists Harvest writes when a collection is loaded; the sweeper finds products only through them. "Inventory" is the member list file the data provider publishes with each collection.

## What needs to happen

| Who | What is wrong (plain English) | Products | Collections | What to do |
|---|---|---|---|---|
| Node | The collection's published inventory names a product that does not exist (`collectin_inventory`), while the registered product is `collection_overview`. The inventory lists no version of the registered product (rule `not_in_collection_inventory`; the audit showed it as `refs_missing`, see Details) | 1 | 1 | Fix the name in the inventory (or in the product label), then re-harvest the collection and tell EN to run the sweepers |
| Node | Collections were swept for ancestry, then their products were loaded again, which erased the products' ancestry; the sweeper never revisits a swept collection (`reloaded_after_collection`) | 20 | 9 | Re-harvest the collection, then run the sweepers |
| Node | Products carry an older sweeper stamp (6) than their collection (7), so they were not reprocessed (`stale_stamp`); their collections are superseded versions | 4 | 2 | Re-harvest the collections and EN runs the sweepers; see Details for a caveat |
| EN | Collections were marked swept with an empty parent list, so the bundle's `/members` is empty or short (sweeper bug, fixed in registry-sweepers PR #286) | 0 directly (4 of the 20 above sit in these) | 58 (8 bundles) | EN re-harvests the 58 collections and runs the sweepers that include the PR #286 fix |
| Sweepers team | none | 0 | 0 | none |
| Needs a closer look | none | 0 | 0 | none |
| No action | none (no pending or by-design items) | 0 | 0 | none |

Collections: reloaded products - `bopps2014:raw::1.0` (10 products), `bopps2014:groundcalibration::1.0` (3), `bopps2014:biassub::1.0` (1), `bopps2014:calibrated::1.0` (1), `lucy.ltes:data_donaldjohanson_calibrated::1.0` (1); four more single-product collections are in the 58. Empty parent list - 21 `dart_teleobs`, 7 `lucy.llorri`, 6 `liciacube`, 6 `lucy.leisa`, 5 `lucy.rss`, 5 `lucy.ttcam`, 4 `lucy.ltes`, 4 `lucy.mvic` collections (full list in `metrics.json`, `empty_refs_with_bundle`). Stale stamp - `lucy.mvic:document::1.0` (3), `dart_teleobs:data_ldtddp::1.0` (1).

## Details

**Node: inventory names a product that does not exist (1 product).** The audit ran with `--no-inventory`, so it reported `lucy.rss:data_dinkinesh_trk234:collection_overview::1.0` as `refs_missing`. I fetched the collection's current inventory with `audit_collection.py --diff --load-status` on `lucy.rss:data_dinkinesh_trk234::1.0`: label 143 records, inventory 143 rows, registry 143 products, public API 142 members. The inventory does not list `collection_overview::1.0` (or any version of that LID); it lists `...:collectin_inventory::1.0`, which is not in the registry. A refs search by product LIDVID and by LID for both names found nothing. So this is not stale refs; re-harvesting alone cannot fix it. I could not tell whether the typo is in the inventory or in the product label. Confirm: `--diff` shows both difference lists empty and the API returns 143 members. This collection is also one of the 58 below.

**Node re-harvest: products loaded again after the collection (20 products).** Sampled `bopps2014:raw:jaca_4_041959996_n016_0003r_fit::1.0`: no ancestry, harvested 2026-09-30; its collection is stamped 7 with parents present, harvested 2025-06-27; one refs document lists the product. The liciacube and lucy.ltes samples matched. `--diff --load-status` on `liciacube:document::1.0`, `lucy.ltes:data_donaldjohanson_calibrated::1.0` and `lucy.mvic:data_donaldjohanson_calibrated::1.0`: inventory and registry hold identical LIDVIDs (8/8, 2/2, 11/11), fully loaded, API one member short each, so the node has nothing to fix. The four bopps2014 collections hold about 772,000 members, so the sweeper run after re-harvest is large; I did not test whether ancestry overwrite mode for the node is cheaper. Why the products were loaded again is unknown. Confirm: the products show a current stamp with parents and the next audit lists no `reloaded_after_collection`.

**EN re-harvest: 58 collections with an empty parent list.** Seen for `liciacube:document::1.0` and `lucy.rss:data_dinkinesh_trk234::1.0` (stamp 7, empty parents); the other collections come from the audit. API `/members` of the bundles returned: liciacube 1.0 = 0, lucy.leisa 2.0 = 0, lucy.ttcam 2.0 = 0, dart_teleobs 2.0 = 1, lucy.llorri 4.0 = 1, lucy.mvic 2.0 = 1, lucy.ltes 2.0 = 3, lucy.rss 2.0 = 4. The cause is taken from the playbook; I did not inspect a sweeper run, and did not verify that the deployed sweeper has PR #286. Confirm: each bundle's `/members` lists all its collections and `empty_refs_with_bundle` is empty in the next audit. Three more superseded versions with empty parents have no bundle and are not counted.

**Node re-harvest: stale stamp (4 products).** `lucy.mvic:document:mvic_sis::1.0` and `dart_teleobs:data_ldtddp:collection_data_ldtddp_overview::1.0` are stamped 6 and are harvested within a second of their collection, which is stamped 7 and superseded by version 2.0. I did not find why they stayed at 6. A sweeper run reaches products only through unswept collections, so these may need the collection re-swept; I did not test this. Confirm: stamp 7 with parents, or the product is superseded.

**Counts check.** My own `_count` of API-visible non-aggregate products without current ancestry returned 25, equal to the audit.

## Index mapping

`sbnumd-registry` has no missing-field errors; 3 unmapped `pds:` fields (`Bundle/description`, `SPICE_Kernel/description`, `SPICE_Kernel/object_length`) hold no data (warnings only). It has 11 error-level type conflicts: `keyword` here where `en` maps number/date/text/long (`sb:Timing/midobservation_time_UTC_YMD` and `_JD` on 508,978 products, `sb:Instrument_Position_Angles` y/z axis angles, `sb:Exposure/exposure_duration` and `exposure_description`, `sb:Filter` long/short wavelength limits, `nh:Mission_Elapsed_Time/clock_partition` on 555,936) and where `sbnpsi` maps double/date (`ebt:Airmass` airmass and airmass_time, no data yet).
What it breaks: number or date range and sort queries on these fields compare text on `sbnumd` and behave differently from `en`, so a search across nodes gives inconsistent results; `exposure_description` is not full-text searchable here.
Who fixes it: EN with the owners of the `en`, `sbnpsi` and `sbnumd` indices; a changed field type needs a new index and a reindex.

<!-- product-samples:start -->
## Example products

Up to 3 products from each of the 10 largest problem groups of 12 (one rule in one collection, node problems first). Every group, with up to 10 products and the reason for each, is in [`product_samples.csv`](../audit-output/sbnumd/product_samples.csv).

| Who | Rule | Collection | Products in group | Examples |
|---|---|---|--:|---|
| Node | `reloaded_after_collection` | `urn:nasa:pds:bopps2014:raw::1.0` | 10 | `urn:nasa:pds:bopps2014:raw:jaca_4_041959996_n016_0003r_fit::1.0`<br>`urn:nasa:pds:bopps2014:raw:jaca_4_042759996_n016_0003r_fit::1.0`<br>`urn:nasa:pds:bopps2014:raw:jacb_3_043960000_n017_0122r_fit::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:bopps2014:groundcalibration::1.0` | 3 | `urn:nasa:pds:bopps2014:groundcalibration:st28_9_021159996_p012_0003r_fit::1.0`<br>`urn:nasa:pds:bopps2014:groundcalibration:st79_3_161259986_p018_0014b_fit::1.0`<br>`urn:nasa:pds:bopps2014:groundcalibration:st79_3_161259986_p018_0014r_fit::1.0` |
| Node | `stale_stamp` | `urn:nasa:pds:lucy.mvic:document::1.0` | 3 | `urn:nasa:pds:lucy.mvic:document:collection_overview::1.0`<br>`urn:nasa:pds:lucy.mvic:document:lralph_mvic_cal_procedure::1.0`<br>`urn:nasa:pds:lucy.mvic:document:mvic_sis::1.0` |
| Node | `not_in_collection_inventory` | `urn:nasa:pds:lucy.rss:data_dinkinesh_trk234::1.0` | 1 | `urn:nasa:pds:lucy.rss:data_dinkinesh_trk234:collection_overview::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:bopps2014:biassub::1.0` | 1 | `urn:nasa:pds:bopps2014:biassub:jca2_3_054000012_n019_0007b_fit::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:bopps2014:calibrated::1.0` | 1 | `urn:nasa:pds:bopps2014:calibrated:jca2_3_054000012_n019_0007e_fit::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:liciacube:document::1.0` | 1 | `urn:nasa:pds:liciacube:document:asi_liciacube_leialuke_calibration_pipeline_description::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:lucy.leisa:data_donaldjohanson_calibrated::1.0` | 1 | `urn:nasa:pds:lucy.leisa:data_donaldjohanson_calibrated:collection_overview::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:lucy.leisa:data_donaldjohanson_raw::1.0` | 1 | `urn:nasa:pds:lucy.leisa:data_donaldjohanson_raw:collection_overview::1.0` |
| Node | `reloaded_after_collection` | `urn:nasa:pds:lucy.ltes:data_donaldjohanson_calibrated::1.0` | 1 | `urn:nasa:pds:lucy.ltes:data_donaldjohanson_calibrated:collection_overview::1.0` |

<!-- product-samples:end -->

## Reproduce

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
REGISTRY_CLIENT_VENV="<path-to-registry-client-venv>"
PYTHON="${REGISTRY_CLIENT_VENV}/bin/python"
API_BASE="https://pds.mcp.nasa.gov/api/search/1"
NODE="sbnumd"
OUT_DIR="./audit_nodes/${NODE}"
source "${ENV_FILE}"

# The audit (add --check to turn it into a pass/fail test; drop --no-inventory for the full run)
"${PYTHON}" scripts/audit_unprocessed_products.py --output-dir "${OUT_DIR}" --node "${NODE}" --gzip --no-inventory

# Inventory against registry for one collection
COLLECTION_LIDVID="urn:nasa:pds:lucy.rss:data_dinkinesh_trk234::1.0"
"${PYTHON}" scripts/audit_collection.py "${COLLECTION_LIDVID}" --diff --load-status --active-days 3

# A bundle's members through the public API
BUNDLE_LIDVID="urn:nasa:pds:liciacube::1.0"
ENCODED="$(jq -rn --arg id "${BUNDLE_LIDVID}" '$id | @uri')"
curl -s -G "${API_BASE}/products/${ENCODED}/members" --data-urlencode "limit=5" | jq '.summary.hits'

# Index mappings (read the rows for sbnumd-registry)
"${PYTHON}" scripts/audit_index_mappings.py --output-dir ./audit_mappings
```
