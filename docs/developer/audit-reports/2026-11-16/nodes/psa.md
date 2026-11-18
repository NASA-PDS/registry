# psa node audit, 2026-11-16

## Verdict

Not healthy, but mostly one event. 319,567 products lack "ancestry" (the record of which collection and bundle a product belongs to, which the public API needs for `/members` and `/ancestors`); a further 1,242,225 are still inside the 7-day waiting window. 233,104 of the 319,567 come from PSA publishing ten collections as version `1.0` on 2026-10-22 and loading products into them afterwards; 28,938 are for the node; 57,525 cannot be assigned because PSA's collection inventories sit behind a login. The load that produced the 1.24 million waiting products stopped on 2026-11-15 and will not clear on its own (see Details, row 5).

## What needs to happen

Terms: the inventory is the list of products in a collection, published by the node. The refs are the registry's copy of that list, written when the collection is harvested (loaded). The sweepers are the scheduled scripts that add ancestry; they reach a product only through its refs and never revisit a collection they have already processed ("stamped").

| Who | What is wrong (plain English) | Products | Collections | What to do |
|---|---|---|---|---|
| Node | The parent collection is not visible: 7 collections exist only as `staged` (hidden from the API), 10 are in no registry index at all. JUICE products are still being loaded without them | 20,941 | 17 | Load (and archive) the collections, or correct the product identifiers |
| Node | The registry holds a newer product version (4.0, or a newer SPICE kernel) than the collection's inventory lists (3.0, or 1.0 to 10.0) | 7,997 | 10 | Publish inventories that list the versions PSA now holds |
| Node | Collections were stamped on 2026-10-22; products were loaded after that and the sweepers never went back. Ask PSA first whether `1.0` is the live version (Details, row 3) | 233,104 | 10 | After PSA answers: re-harvest the ten collections, then run the sweepers |
| Sweepers team | Products skipped with no explanation in the data | 0 | 0 | None |
| Needs a closer look | No refs document lists the product and the inventory cannot be downloaded (HTTP 401, login required). 153 are SPICE kernels that the NAIF index does list | 57,525 | 29 | PSA supplies the 26 inventories (or access), then re-run `audit_collection.py --diff`; decide on the 3 SPICE duplicates |
| No action | Harvested 2026-11-11 to 2026-11-15, within the 7-day window; 663 more wait for a missing collection, 2 never have a collection | 1,242,225 | - | Re-check after 2026-11-22 (see Details, row 5) |

Node, row 1: `urn:esa:psa:juice:miscellaneous` (11,372, staged only), `juice_radem:browse_raw` (2,218), `juice_radem:data_raw` (2,218), `juice_jmc:data_raw` (1,676), `juice_jmc:browse_partially_processed` (1,493).
Node, row 2: `em16_tgo_cas:browse_calibrated::2.0` (5,673), `em16_tgo_cas:browse_raw::2.0` (912), `em16_tgo_cas:data_raw::105.1` (912), `bc_mtm_mcam:browse::2.0` (236), `bc_mtm_mcam:data_raw::2.0` (236).
Collections the node re-harvests: `em16_tgo_cas:data_raw::1.0` (113,135), `em16_tgo_cas:browse_raw::1.0` (111,867), `em16_tgo_nmd:data_raw::1.0` (2,813), `em16_tgo_acs:data_raw::1.0` (1,860), `em16_tgo_nmd:data_partially_processed::1.0` (1,840).
Closer look: `em16_tgo_cas:browse_raw::2.0` (13,000), `em16_tgo_cas:data_raw::105.1` (13,000), `em16_tgo_nmd:data_calibrated::4.0` (8,606), `em16_tgo_cas:data_calibrated::4.0` (5,856), `em16:miscellaneous_ancillary::125.3` (5,374).
Waiting: `em16_tgo_cas:browse_calibrated::2.0` (601,275), `em16_tgo_cas:data_calibrated::4.0` (600,506), `em16_tgo_cas:data_raw::105.1` (18,640), `em16_tgo_cas:browse_raw::2.0` (18,584), `em16:miscellaneous_ancillary::125.3` (1,731). Collection ids above omit the `urn:esa:psa:` prefix.

## Details

**Row 1 (collections not visible, 20,941).** I searched every registry index for the 17 collection ids. Seven are in `psa-registry` only as `staged` (archive status that the API hides): `juice:miscellaneous` (::0.1), `bc_mpo_mag:data_derived`, and the `bc_mpo_{serena,berm,isa,mixs,sixs}:document` collections, 11,648 products. Ten are in no index: `juice_radem` (browse_raw, data_raw, miscellaneous, document), `juice_jmc` (four collections), `bc_mpo_more:document`, `bc_mpo_mgns:document`, 9,293 products. No other node's index holds them, so this is not a case of a LIDVID registered under another node. The `juice_jmc` and `juice_radem` bundles are not in the registry either. Products in these collections were harvested as late as 2026-11-14, so PSA is loading JUICE products ahead of their collections. Fixed when the audit shows no `collection_not_loaded_overdue`.

**Row 2 (inventory older than the registry, 7,997).** Direction: the registry is newer. Sample 1, `browse_calibrated:cas_cal_sc_browse_20180901...::4.0`: the registry holds 3.0 (2023, has ancestry, marked replaced by 4.0) and 4.0 (harvested 2026-10-23, no ancestry); the refs of `browse_calibrated::2.0` and `::1.0` list only 3.0. PSA's own modification note says all products are 4.0 from DPS 5.0 on, so this is the reprocessing from 3.0 to 4.0. Sample 2, SPICE: `audit_collection.py --diff` on `em16_spice:spice_kernels::10.0` (inventory read from NAIF's public copy) shows the inventory lists `mk_em16::1.0` to `::10.0` while the registry holds `mk_em16::18.0`; same for `bc_spice:spice_kernels::4.0` (`mk_bc::1.0` to `::4.0` versus `::11.0`). I could not run `--diff` on the CaSSIS collections (row 4). Fixed when the audit lists none of these.

**Row 3 (233,104 loaded after the collection was stamped).** Mechanism confirmed on `em16_tgo_nmd:data_raw::1.0` and `em16_tgo_acs:data_raw::1.0` (and `em16_tgo_cas:data_raw::1.0`):
- The collection was harvested 2026-10-22 (nmd 08:48, acs 05:26, cas 07:45 UTC), carries stamp 7 and only its bundle as ancestor. The bundle `em16_tgo_cas::1.0` was harvested the same morning; no collection or bundle has been harvested since (newest: 2026-10-22 08:49).
- Every stamped product of the nmd and acs data_raw lines was harvested on or before 2026-09-09; the unstamped ones start at 2026-10-24 00:42 (nmd) and 2026-10-23 19:46 (acs). The unstamped counts (2,813 and 1,860) equal the audit's counts exactly.
- The products arrived in two bursts after the stamp: 2026-10-23/24 (167,261) and 2026-11-11 to 2026-11-15 (65,843), so they were loaded one after the other, not before. All 233,104 are in a refs document of their collection and have no ancestry. Sample `cas_raw_hk_hk0_20260306t000000-20260306t055959::4.0` is in refs batch 79 of `data_raw::1.0`, and the API `/members` of that collection filtered to it returns 0 hits (the collection lists 11,088,663 members).
- Surprise: the registry marks all ten `::1.0` collections as replaced by older-numbered ones (for example `data_raw::1.0` by `::105.1`), because 1.0 sorts below 105.1. But the `::1.0` label was created 2026-10-22, declares 18,004,981 records against 15,580,847 for `::105.1`, and the API lists 11.1 million members for `::1.0` versus 8.6 million for `::105.1`. So `::1.0` looks like the live line and PSA's version numbers went backwards; I could not confirm that with PSA. The audit leaves superseded collections out of `anomalous_collections.txt`, so these ten need to be re-harvested by name.
- The refs of these `::1.0` collections hold fewer entries than their labels declare (for example 17,527,822 versus 18,004,981 for `cas:data_raw::1.0`, 477,159 short). I did not find why (duplicates or secondary rows in the inventory are possible). A re-harvest rewrites the refs from the current inventory.
- Fixed when `reloaded_after_collection` is 0 and `/members` of each collection approaches its refs count.

**Row 4 (57,525 not checked against an inventory).**
- Why: all 29 collections are registered with an `https://archives.esac.esa.int/psa/repo/...` file location (checked in the registry for all 29). That host answers every request, including a collection label, a product label and the repository folders, with HTTP 401 and a Basic login prompt; `audit_collection.py --diff` on `bc_mtm_mcam:browse::2.0` logs `Failed to download inventory file: 401 Client Error: Unauthorized` and skips the diff. The file locations are absolute URLs on a host that answers, so this is not a relative-path or 404 problem. I did not try any credentials. So 26 of the 29 collections cannot be settled from here. Needed: the 26 inventory files (or a read login) from PSA, then `audit_collection.py --diff` per collection.
- Three SPICE collections (`bc_spice:spice_kernels::4.0` 91, `em16_spice:spice_kernels::10.0` 57, `em16_spice:miscellaneous::10.0` 5; 153 products) are also registered in the NAIF index with a public inventory. `--diff` shows all 91 and all 57 are absent from that inventory under any version. A sample of 29 products (12, 12 and 5) is listed in NAIF refs, under later collection versions (for example `em16_spice:spice_kernels::16.0` to `::18.0`), and the NAIF copy has ancestry. These are duplicate PSA registrations of NAIF products; decide whether the PSA copies should exist.
- For the other 57,372, I took a sample of 330 products across all 29 collections (12 per collection, fewer in the smallest); the 29 SPICE ones are in NAIF refs and the other 301 are listed in no refs document of any node. Without the inventories the best evidence is the label's declared record count (`pds:Inventory/pds:records`, the provider's claim at harvest time) against the refs entries. Equal for the collections holding 20,113 of the products (14 `bc_mtm_mcam` versions, the three `miscellaneous_ancillary::4.0`, `nmd:data_calibrated::4.0`, `cas:browse_calibrated::2.0`): the harvested inventory did not list these products, which points to the node. Refs short of the label for the collections holding 31,403 (`cas:browse_raw::2.0`, `cas:data_raw::105.1`, `em16:miscellaneous_ancillary::125.3`, and three tiny ones where the gap equals the missing count exactly: `frd:data_calibrated::1.0` 12, `nmd:calibration_files::1.1` 16, `psa_master:xml_schema::7.0` 1; those 29 look like stale refs, which the node fixes by re-harvesting). `cas:data_calibrated::4.0` (5,856) declares 0 records and cannot be read this way. Most products were harvested 2025-2026 into collections harvested years earlier, so they probably belong to collection versions PSA has not published or loaded. This is inference; I did not see an inventory.
- Fixed when the products appear in a refs document or leave the audit.

**Row 5 (1,242,225 waiting).** Not loading right now. Harvest times of the waiting products run from 2026-11-11 16:08 to 2026-11-15 01:24 UTC (about 30,000 per hour); nothing has been harvested since, about 47 hours before this check. PSA loads in bursts: weeks starting 05-18, 06-08, 07-06, 08-03, 09-07, 10-19, 11-09 (1,308,507 products, seven times the usual). Sampled 600 of them (200 each from three collections): each has one version only, so they are new products. No collection has been harvested since 2026-10-22, so no refs document will list them until PSA's collections are re-harvested. The window ends 2026-11-18 to 2026-11-22; after that these will show as `refs_missing` and, with the inventories unreadable, land in "needs a closer look". Re-check on 2026-11-23, and ask PSA whether the burst is finished and when its collections will be re-harvested.

## Index mapping

`psa-registry` has no error-level problems and `psa-registry-refs` has none at all. Six warning-level fields, absent from `psa-registry` but present on 8 of 10 nodes: `pds:Affiliation/pds:organization_name`, `pds:Person/pds:family_name`, `pds:Person/pds:given_name`, `pds:Person/pds:person_orcid`, `pds:Context_Area/pds:comment`, `pds:Special_Constants/pds:invalid_constant`. Because the index is not dynamic, products carrying them can be fetched but those fields cannot be searched. I did not check whether PSA documents carry them. Owner: EN with the index owners.

<!-- product-samples:start -->
## Example products

Up to 3 products from each of the 10 largest problem groups of 50 (one rule in one collection, node problems first). Every group, with up to 10 products and the reason for each, is in [`product_samples.csv`](../audit-output/psa/product_samples.csv).

| Who | Rule | Collection | Products in group | Examples |
|---|---|---|--:|---|
| Node | `reloaded_after_collection` | `urn:esa:psa:em16_tgo_cas:data_raw::1.0` | 113,135 | `urn:esa:psa:em16_tgo_cas:data_raw:cas_raw_hk_hk0_20260306t000000-20260306t055959::4.0`<br>`urn:esa:psa:em16_tgo_cas:data_raw:cas_raw_hk_hk0_20260306t060000-20260306t115959::4.0`<br>`urn:esa:psa:em16_tgo_cas:data_raw:cas_raw_hk_hk0_20260306t120000-20260306t175959::4.0` |
| Node | `reloaded_after_collection` | `urn:esa:psa:em16_tgo_cas:browse_raw::1.0` | 111,867 | `urn:esa:psa:em16_tgo_cas:browse_raw:cas_raw_sc_browse_20260306t012624-20260306t012628-36947-60-blu-1417845708-0-3::4.0`<br>`urn:esa:psa:em16_tgo_cas:browse_raw:cas_raw_sc_browse_20260306t012624-20260306t012628-36947-60-nir-1417845708-0-2::4.0`<br>`urn:esa:psa:em16_tgo_cas:browse_raw:cas_raw_sc_browse_20260306t012624-20260306t012628-36947-60-pan-1417845708-0-0::4.0` |
| Node | `collection_not_loaded_overdue` | `(none found)` | 20,941 | `urn:esa:psa:bc_mpo_berm:document:ber_doc_pinto_2022::1.0`<br>`urn:esa:psa:bc_mpo_berm:document:eaicd::2.1`<br>`urn:esa:psa:bc_mpo_berm:document:pdd::1.2` |
| Node | `inventory_version_mismatch` | `urn:esa:psa:em16_tgo_cas:browse_calibrated::2.0` | 5,673 | `urn:esa:psa:em16_tgo_cas:browse_calibrated:cas_cal_sc_browse_20180901t033549-20180901t033553-3446-36-blu-275493888-0-2::4.0`<br>`urn:esa:psa:em16_tgo_cas:browse_calibrated:cas_cal_sc_browse_20180901t033549-20180901t033553-3446-36-blu-275493888-1-2::4.0`<br>`urn:esa:psa:em16_tgo_cas:browse_calibrated:cas_cal_sc_browse_20180901t033549-20180901t033553-3446-36-blu-275493888-2-2::4.0` |
| Node | `reloaded_after_collection` | `urn:esa:psa:em16_tgo_nmd:data_raw::1.0` | 2,813 | `urn:esa:psa:em16_tgo_nmd:data_raw:nmd_raw_hk_hk1_20260306t000000-20260306t055959::4.0`<br>`urn:esa:psa:em16_tgo_nmd:data_raw:nmd_raw_hk_hk1_20260306t060000-20260306t115959::4.0`<br>`urn:esa:psa:em16_tgo_nmd:data_raw:nmd_raw_hk_hk1_20260306t120000-20260306t175959::4.0` |
| Node | `reloaded_after_collection` | `urn:esa:psa:em16_tgo_acs:data_raw::1.0` | 1,860 | `urn:esa:psa:em16_tgo_acs:data_raw:acs_raw_hk_be_20260306t000000-20260306t055959::4.0`<br>`urn:esa:psa:em16_tgo_acs:data_raw:acs_raw_hk_be_20260306t060000-20260306t115959::4.0`<br>`urn:esa:psa:em16_tgo_acs:data_raw:acs_raw_hk_be_20260306t120000-20260306t175959::4.0` |
| Node | `reloaded_after_collection` | `urn:esa:psa:em16_tgo_nmd:data_partially_processed::1.0` | 1,840 | `urn:esa:psa:em16_tgo_nmd:data_partially_processed:nmd_par_hk_hk1_20260306t000000-20260306t055959::4.0`<br>`urn:esa:psa:em16_tgo_nmd:data_partially_processed:nmd_par_hk_hk1_20260306t060000-20260306t115959::4.0`<br>`urn:esa:psa:em16_tgo_nmd:data_partially_processed:nmd_par_hk_hk1_20260306t120000-20260306t175959::4.0` |
| Node | `reloaded_after_collection` | `urn:esa:psa:em16_tgo_cas:data_partially_processed::1.0` | 976 | `urn:esa:psa:em16_tgo_cas:data_partially_processed:cas_par_hk_hk0_20260306t000000-20260306t055959::4.0`<br>`urn:esa:psa:em16_tgo_cas:data_partially_processed:cas_par_hk_hk0_20260306t060000-20260306t115959::4.0`<br>`urn:esa:psa:em16_tgo_cas:data_partially_processed:cas_par_hk_hk0_20260306t120000-20260306t175959::4.0` |
| Node | `inventory_version_mismatch` | `urn:esa:psa:em16_tgo_cas:browse_raw::2.0` | 912 | `urn:esa:psa:em16_tgo_cas:browse_raw:cas_raw_sc_browse_20180621t095757-20180621t095801-2570-24-blu-273699053-4-2::4.0`<br>`urn:esa:psa:em16_tgo_cas:browse_raw:cas_raw_sc_browse_20180621t095757-20180621t095801-2570-24-nir-273699053-4-1::4.0`<br>`urn:esa:psa:em16_tgo_cas:browse_raw:cas_raw_sc_browse_20180621t095757-20180621t095801-2570-24-pan-273699053-4-0::4.0` |
| Node | `inventory_version_mismatch` | `urn:esa:psa:em16_tgo_cas:data_raw::105.1` | 912 | `urn:esa:psa:em16_tgo_cas:data_raw:cas_raw_sc_20180621t095757-20180621t095801-2570-24-blu-273699053-4-2::4.0`<br>`urn:esa:psa:em16_tgo_cas:data_raw:cas_raw_sc_20180621t095757-20180621t095801-2570-24-nir-273699053-4-1::4.0`<br>`urn:esa:psa:em16_tgo_cas:data_raw:cas_raw_sc_20180621t095757-20180621t095801-2570-24-pan-273699053-4-0::4.0` |

<!-- product-samples:end -->

## Reproduce

```bash
ENV_FILE="<path-to-registry-client-env-file>"
PYTHON="<path-to-registry-client-venv>/bin/python"
REGISTRY_CLIENT="<path-to-registry-client-venv>/bin/pds-registry-client"
OUT_DIR="<output-directory>"
API_BASE="https://pds.mcp.nasa.gov/api/search/1"
COLLECTION_LIDVID="urn:esa:psa:em16_spice:spice_kernels::10.0"
COLLECTION_ENCODED="urn%3Aesa%3Apsa%3Aem16_tgo_cas%3Adata_raw%3A%3A1.0"
source "${ENV_FILE}"

# Audit of the node's unprocessed products
"${PYTHON}" scripts/audit_unprocessed_products.py --output-dir "${OUT_DIR}" --node psa --gzip

# Inventory versus registry (works for the SPICE collections, whose inventory is public).
# --registry-index keeps en-legacy-registry out of the counts.
"${PYTHON}" scripts/audit_collection.py "${COLLECTION_LIDVID}" --registry-index /psa-registry/_count --diff --load-status --active-days 14 --output-dir "${OUT_DIR}/collection_audit"

# The PSA inventory host answers 401 (prints the status code)
curl -s -o /dev/null -w "%{http_code}\n" "https://archives.esac.esa.int/psa/repo/esa/psa/em16_tgo_cas/browse_raw/2.0/collection_browse_raw.csv"

# Members the API lists for a collection (hits)
curl -s -G "${API_BASE}/products/${COLLECTION_ENCODED}/members" --data-urlencode "limit=1" | jq '.summary.hits'

# Newest harvest time in the node, and harvests per day (is a load running?)
BODY='{"size":0,"query":{"range":{"ops:Harvest_Info/ops:harvest_date_time":{"gte":"now-14d"}}},"aggs":{"d":{"date_histogram":{"field":"ops:Harvest_Info/ops:harvest_date_time","calendar_interval":"day"}},"newest":{"max":{"field":"ops:Harvest_Info/ops:harvest_date_time"}}}}'
"${REGISTRY_CLIENT}" -d "${BODY}" /psa-registry/_search | jq '.aggregations'

# Unstamped products of a collection line: count and earliest harvest time (compare with the collection's harvest time)
LID_PREFIX="urn:esa:psa:em16_tgo_nmd:data_raw:"
BODY="$(jq -n --arg p "${LID_PREFIX}" '{size: 0, query: {prefix: {lid: $p}}, aggs: {unstamped: {filter: {bool: {must_not: [{exists: {field: "ops:Provenance/ops:ancestor_refs"}}]}}, aggs: {first: {min: {field: "ops:Harvest_Info/ops:harvest_date_time"}}}}}}')"
"${REGISTRY_CLIENT}" -d "${BODY}" /psa-registry/_search | jq '.aggregations.unstamped'

# Which nodes' refs list a product (empty hits: listed nowhere)
PRODUCT_LIDVID="urn:esa:psa:em16_spice:spice_kernels:spk_mar097_20160314_20500101.bsp::1.0"
BODY="$(jq -n --arg id "${PRODUCT_LIDVID}" '{size: 5, query: {term: {product_lidvid: $id}}, _source: ["collection_lidvid"]}')"
"${REGISTRY_CLIENT}" -d "${BODY}" "/*-registry-refs/_search" | jq '[.hits.hits[] | {index: ._index, collection: ._source.collection_lidvid}]'
```

The per-product checks (`show_doc`, `show_refs`, `api_member_hits`) are in the verification toolkit of `audit-unprocessed-products-reference.md`.
