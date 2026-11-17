# en node audit, 2026-11-16

## Verdict

793 products in the `en` registry index could appear in the public API; 705 need attention and all 705 are for the node (nothing for registry operations or the sweepers team), and 88 need no action. The biggest problem is that the registry stops at version 56.0 of the two Deep Archive collections while the data provider now publishes version 64.0.

## What needs to happen

"Ancestry" is the parent link (collection, bundle) the sweepers add to each product; without it the API leaves the product out of its collection's member list. "Refs" are the registry-refs documents written from a collection's inventory file when the collection is harvested; the sweepers reach a product only through them.

| Who | What is wrong (plain English) | Products | Collections | What to do |
|---|---|---|---|---|
| Node | Collection versions 57.0 to 64.0 of the AIP and SIP Deep Archive collections are published by the provider but not loaded. 180 AIP and 180 SIP products are already in the registry but appear in no inventory the registry holds, so they have no refs and no ancestry | 360 | 2 | Load the current versions (up to 64.0) of `product_aip` and `product_sip_deep_archive`, and the ~456 products each lists that are not loaded yet. Then registry operations runs the sweepers |
| Node | The `xml_schema` collection of the System Bundle (and two foreign copies of it) is not in the registry, so its schema products have no parent | 342 | 4 collection IDs | Load the collection `urn:nasa:pds:system_bundle:xml_schema` (the bundle label lists it). One product has a malformed LID (`tbd_urnprefixsystem_bundle:...`): fix it. Decide what to do with the `jaxa:darts` and `kari:kpds` schema products |
| Node | Two policy documents are registered under `document_policy` but not listed in its inventory file under any version | 2 | 1 | Add them to the inventory and re-harvest the collection, or remove them from the registry |
| Node | `lids_deprecated` has three different versions: refs say 1.1, the inventory file now says 1.0, the registry holds 1.2 | 1 | 1 | Make the inventory and the loaded version agree, then re-harvest |
| Registry operations | none found | 0 | 0 | - |
| Sweepers team | none found (no `sweeper_miss`, no empty-refs collection with a bundle) | 0 | 0 | - |
| Needs a closer look | none: every `refs_missing` product was checked against the inventory | 0 | 0 | - |
| No action | 87 services and 1 context product never belong to a collection | 88 | - | - |

Collections: `urn:nasa:pds:system_bundle:product_aip` (registry current 56.0), `urn:nasa:pds:system_bundle:product_sip_deep_archive` (56.0), `urn:nasa:pds:system_bundle:xml_schema` (not loaded), `urn:nasa:pds:system_bundle:document_policy::1.0`, `urn:nasa:pds:context:miscellaneous::1.1`.

## Details

**Deep Archive (360 products).** The unprocessed-products audit ran with `--no-inventory`, so these showed as `refs_missing`, filed under old superseded collections 1.0 and 2.0 by a version-number guess. Checked by hand:
- `audit_collection.py ... product_aip::56.0 --diff --load-status` (and the SIP twin): inventory 463 rows, 462 loaded, registry holds 642 visible products, 180 of them absent from the inventory; the API `/members` returns 462.
- I downloaded the provider's inventory for every version 1.0 to 64.0. None of v1 to v56 lists the 180 flagged AIP products; every one of v57 to v64 lists all 180. v64 (file dated 2026-11-15 by the server) has 1099 rows, 456 of them not in the registry. SIP gave the same numbers.
- No collection `::57.0` to `::64.0` exists in any registry index and the API returns 404 for `product_aip::64.0`.
- Re-harvesting 56.0 cannot help: its inventory does not list these products. The products were harvested on 2025-03-05 and 2025-07-16 without the newer collections; I did not establish why.
- Confirm the fix: collection 64.0 present, `/members` of it returns about 1099 items, next audit shows 0 for these.

**XML schema (342).** `urn:nasa:pds:system_bundle:xml_schema` (336), `urn:jaxa:darts:system_bundle:xml_schema` (3), `urn:kari:kpds:system_bundle:xml_schema` (2), one malformed LID. A search of all indices for those three LIDs returns nothing. The bundle `urn:nasa:pds:system_bundle::1.0` label lists the xml_schema collection, but the API returns 4 members for it (no xml_schema). All 392 schema products were harvested by Harvest 4.0.5 and carry relative `file_ref` values (no `https://`). I did not check whether the provider publishes a label for the collection. Confirm: the collection exists and the schema products leave the audit.

**document_policy (2).** Collection `::1.0` is stamped with empty refs but no bundle lists it (the bundle label has no `document_policy` entry), so this is not the sweeper bug. Its registered `file_ref` is relative, so the script cannot download the inventory; I fetched it from the same data-provider host (assumed): 34 rows, label says 31 records, and `pdsmc_data_integrity_schedule_policy::2.0` and `pdsmc_formats_policy::2.0` are in no row under any version. The inventory lists 3 products the registry does not hold. `document_pds3_standards::1.0` is the other empty-refs collection without a bundle (expected).

**lids_deprecated (1).** Refs document `...::P1` of collection `miscellaneous::1.1` names `lids_deprecated::1.1`; the inventory file lists `::1.0`; the registry holds `::1.2`. `--diff` shows 0 of 1 inventory product loaded. Confirm: audit shows 0.

**Confirming everything.** Re-run the audit with `--previous-csv`; expect 0 anomalous. The independent candidate count (`_count` query from the reference doc) gave 793, equal to the audit.

## Index mapping

From `mapping_discrepancies.csv` (`en-registry`): no field missing at error level; `superseded_by`, `vid`, `lidvid` and the ancestry fields are mapped. Two type conflicts at error level, both against `sbnumd-registry`: `nh:Mission_Elapsed_Time/nh:clock_partition` (en `long`, sbnumd `keyword`) and `sb:Exposure/sb:exposure_description` (en `text`, sbnumd `keyword`). Seven more `sb:` fields (en `double` or `date`, sbnumd `keyword`) and two `insight:` fields (en `integer`, geo `keyword`) are flagged on the other node. Effect: a query across all nodes that treats such a field as a number, date or text can fail or behave differently on one of the two. Ten warnings: fields mapped on most nodes but not here (`pds:Collection/pds:description`, `pds:Observation_Area/pds:comment`, six `pds:SPICE_Kernel` fields, `pds:Special_Constants/pds:not_applicable_constant`, `ref_lid_data`); such values would be returned but not searchable. The en documents I sampled do not carry them; I did not check all. Owner: registry operations with the index owners.

<!-- product-samples:start -->
## Example products

Up to 3 products from each of the 6 largest problem groups of 6 (one rule in one collection, node problems first). Every group, with up to 10 products and the reason for each, is in [`product_samples.csv`](../audit-output/en/product_samples.csv).

| Who | Rule | Collection | Products in group | Examples |
|---|---|---|--:|---|
| Node | `collection_not_loaded_overdue` | `(none found)` | 342 | `tbd_urnprefixsystem_bundle:xml_schema:img-xml_schema::1.0`<br>`urn:jaxa:darts:system_bundle:xml_schema:hyb2-xml_schema_1.14.0.0_1.0.0.0::1.0`<br>`urn:jaxa:darts:system_bundle:xml_schema:hyb2-xml_schema_1.14.0.0_1.1.0.0::1.0` |
| Node | `not_in_collection_inventory` | `urn:nasa:pds:system_bundle:product_sip_deep_archive::1.0` | 180 | `urn:nasa:pds:system_bundle:product_sip_deep_archive:astromat_v1.0_20240528::1.0`<br>`urn:nasa:pds:system_bundle:product_sip_deep_archive:asurgcps_slides_jovian_system_v1.0_20240209::1.0`<br>`urn:nasa:pds:system_bundle:product_sip_deep_archive:bc_spice_v1.0_20231128::1.0` |
| Node | `not_in_collection_inventory` | `urn:nasa:pds:system_bundle:product_aip::1.0` | 179 | `urn:nasa:pds:system_bundle:product_aip:astromat_v1.0_20240528::1.0`<br>`urn:nasa:pds:system_bundle:product_aip:asurgcps_slides_jovian_system_v1.0_20240209::1.0`<br>`urn:nasa:pds:system_bundle:product_aip:bc_spice_v1.0_20231128::1.0` |
| Node | `inventory_version_mismatch` | `urn:nasa:pds:context:miscellaneous::1.1` | 1 | `urn:nasa:pds:context:miscellaneous:lids_deprecated::1.2` |
| Node | `not_in_collection_inventory` | `urn:nasa:pds:system_bundle:product_aip::2.0` | 1 | `urn:nasa:pds:system_bundle:product_aip:msl_gt_diagenesis_supplement_v1.1_20240209::2.0` |
| Needs a closer look | `refs_missing` | `urn:nasa:pds:system_bundle:document_policy::1.0` | 2 | `urn:nasa:pds:system_bundle:document_policy:pdsmc_data_integrity_schedule_policy::2.0`<br>`urn:nasa:pds:system_bundle:document_policy:pdsmc_formats_policy::2.0` |

<!-- product-samples:end -->

## Reproduce

```bash
ENV_FILE="<path-to-your-registry-client-env-file>"
VENV="<path-to-registry-client-venv>"
OUT_DIR="./audit_unprocessed/en"
source "${ENV_FILE}"
"${VENV}/bin/python" scripts/audit_unprocessed_products.py --output-dir "${OUT_DIR}" --node en --gzip --no-inventory --check

# Per-collection inventory comparison (en index only; the default index also counts the legacy mirror)
for COLLECTION in urn:nasa:pds:system_bundle:product_aip::56.0 urn:nasa:pds:system_bundle:product_sip_deep_archive::56.0 urn:nasa:pds:context:miscellaneous::1.1; do
  "${VENV}/bin/python" scripts/audit_collection.py "${COLLECTION}" --diff --load-status --registry-index /en-registry/_count
done

# Is a product in a newer inventory? (counts 1 when listed)
INV_URL="https://pds.nasa.gov/data/pds4/documents/manifests/inventory/Collection_product_aip_v64.0.csv"
LIDVID="urn:nasa:pds:system_bundle:product_aip:astromat_v1.0_20240528::1.0"
curl -s "${INV_URL}" | grep -c -F "${LIDVID}"

# Is a collection version loaded? (hits 0 means no)
BODY='{"size":5,"query":{"term":{"lidvid":"urn:nasa:pds:system_bundle:product_aip::64.0"}},"_source":["lidvid"]}'
"${VENV}/bin/pds-registry-client" -d "${BODY}" "/*-registry/_search"

# Bundle members seen by the public API
API_BASE="https://pds.mcp.nasa.gov/api/search/1"
curl -s "${API_BASE}/products/urn:nasa:pds:system_bundle::1.0/members"
```
