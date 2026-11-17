# sbnpsi node audit, 2026-11-16

Terms used below. *Ancestry* is the link from a product to its collection and bundle; the public API
builds `/members` and `/member-of` from it. The *ancestry sweeper* writes it and marks each document with
a *stamp* (the sweeper version, currently 7). *Refs* are the `registry-refs` documents Harvest writes from
a collection's *inventory* (the list of member products that the data provider serves). A *superseded*
product or collection has a newer version.

## Verdict

Mostly healthy, with one cluster to repair. 98 API-visible products have no current ancestry: 29 are
expected, 69 need attention (67 for registry operations, 2 for the node, none for the sweepers team). The audit
ran with `--no-inventory`; I checked the two products that were not stale-stamp rows against the real
inventories by hand.

## What needs to happen

| Who | What is wrong (plain English) | Products | Collections | What to do |
|---|---|---|---|---|
| Node | A document is registered under the HST Ceres collection, but the collection's inventory does not list it. The provider's current label is `...document:hst.hstacs`; the inventory lists `...document:hstacs.hst`, and that label file no longer exists on the provider | 1 | 1 | Correct the inventory to list `hst.hstacs`; decide what happens to the old registered `hstacs.hst` product. Then registry operations re-harvests the collection |
| Node | A Product_XML_Schema (`sp-xml_schema_1.15.0.0_1.3.1.0`) has no collection: no collection named `system_bundle:xml_schema` exists in any node's index. The Hayabusa mission xml_schema collection lists it only as a secondary (bare-LID) member | 1 | 0 (no owning collection found) | List the schema as a primary member (with its LIDVID) in the collection that owns it, as the Hayabusa2 xml_schema collection does for other schemas, or remove it. Low impact (a schema file) |
| Registry operations | 67 current (not superseded) 1.0 products sit in 9 superseded collection versions. They carry the old stamp 6 and no ancestry, so the API lists no members for those collections. Their collections were stamped 7 without them, and the sweeper never revisits a stamped collection | 67 | 9 | Run the ancestry sweeper in overwrite (force) mode for sbnpsi. A normal run is expected to skip them (see Details) |
| No action | JAXA DARTS context products (agency, instrument, ...) never belong to a collection | 29 | 0 | none |

Stale-stamp collections, largest first: `iue.ast.hendrix.spectra:document::1.0` (21),
`iue.ast.hendrix.spectra:data::1.0` (16), `neowise_diameters_albedos:data::1.0` (8),
`smallbodiesoccultations:data::1.0` and `data::2.0` (6 each); 4 more in the same three bundles
(`smallbodiesoccultations` data 3.0 and documents 1.0 and 3.0, `neowise_diameters_albedos:document::1.0`).

## Details

**Node: HST Ceres document.** `audit_collection.py --diff` on `hst.ast-ceres.uv-spectra:document::1.0`: label,
inventory and API all say 7 members; the registry holds 8 non-superseded LIDVIDs, one more than the inventory
(`hst.hstacs::1.0`, harvested 2026-10-09). No refs document lists its LID. I downloaded the inventory: it has
`hstacs.hst`, not `hst.hstacs`. The provider's `hst.hstacs.xml` returns 200 and declares
`...document:hst.hstacs`; `hstacs.hst.xml` returns 404. Both registry documents have the same title.
Confirm: re-run the audit; the product leaves the list once the inventory, refs and sweeper agree.

**Node: XML schema.** Product `...system_bundle:xml_schema:sp-xml_schema_1.15.0.0_1.3.1.0::1.0` has no stamp.
The only refs document naming its LID belongs to `hay.mission:xml_schema::1.0` and has `product_lid` but no
`product_lidvid`; that collection's inventory has five `S,` rows with bare LIDs. The sweeper reads only
`product_lidvid`, so it cannot give the product ancestry. Seven other `system_bundle:xml_schema` products are
stamped 7 because `urn:jaxa:darts:hyb2:xml_schema::3.0` lists them as primary with LIDVIDs; it does not list
this one. The same LIDVID is also registered in the `en` index. Confirm: the audit no longer lists it.

**Registry operations: stale stamp.** All 67 documents (checked by query): archived, not superseded, stamp 6,
no `ancestor_refs`, harvested 2022-07-20, and listed in a refs document of their own collection (those 9 refs
documents carry stamp 1). Their collections carry stamp 7 with `ancestor_refs`. For `iue...:data::1.0`, the
API returns 0 members although the inventory (16 rows) is fully loaded; its superseding collection `data::2.0`
has 110 different products. In the registry-sweepers source on `main`, collections are selected by their own
stamp only and products are reached only through a pending collection, so a normal run would skip these
collections; overwrite mode (a registry-sweepers branch, release status not verified) processes all. I did not
run a sweeper. Why the collections were stamped 7 while their products stayed at 6 is not determined.
Confirm: the 67 products show stamp 7 and `ancestor_refs`, and `/products/<collection>/members` returns hits.

**No action.** 29 `Product_Context` products (harvested 2026-10-15).

## Index mapping

`sbnpsi-registry` has 1356 mapped fields and no discrepancies (0 errors, 0 warnings). It is the reference
mapping the other nodes are compared with (for example `title` and `description` are `text`). Nothing to do.

<!-- product-samples:start -->
## Example products

Up to 3 products from each of the 10 largest problem groups of 11 (one rule in one collection, node problems first). Every group, with up to 10 products and the reason for each, is in [`product_samples.csv`](../audit-output/sbnpsi/product_samples.csv).

| Who | Rule | Collection | Products in group | Examples |
|---|---|---|--:|---|
| Node | `collection_not_loaded_overdue` | `(none found)` | 1 | `urn:nasa:pds:system_bundle:xml_schema:sp-xml_schema_1.15.0.0_1.3.1.0::1.0` |
| Node | `not_in_collection_inventory` | `urn:nasa:pds:hst.ast-ceres.uv-spectra:document::1.0` | 1 | `urn:nasa:pds:hst.ast-ceres.uv-spectra:document:hst.hstacs::1.0` |
| Registry operations | `stale_stamp` | `urn:nasa:pds:iue.ast.hendrix.spectra:document::1.0` | 21 | `urn:nasa:pds:iue.ast.hendrix.spectra:document:22kalliope_lwr12303_ines_fits_headers::1.0`<br>`urn:nasa:pds:iue.ast.hendrix.spectra:document:3juno_lwr01896_ines_fits_headers::1.0`<br>`urn:nasa:pds:iue.ast.hendrix.spectra:document:3juno_lwr05678_ines_fits_headers::1.0` |
| Registry operations | `stale_stamp` | `urn:nasa:pds:iue.ast.hendrix.spectra:data::1.0` | 16 | `urn:nasa:pds:iue.ast.hendrix.spectra:data:hebe_9488_refl_csv::1.0`<br>`urn:nasa:pds:iue.ast.hendrix.spectra:data:hebe_9495_refl_csv::1.0`<br>`urn:nasa:pds:iue.ast.hendrix.spectra:data:hebe_9496_refl_csv::1.0` |
| Registry operations | `stale_stamp` | `urn:nasa:pds:neowise_diameters_albedos:data::1.0` | 8 | `urn:nasa:pds:neowise_diameters_albedos:data:neowise_ambos_tab::1.0`<br>`urn:nasa:pds:neowise_diameters_albedos:data:neowise_centaurs_tab::1.0`<br>`urn:nasa:pds:neowise_diameters_albedos:data:neowise_hildas_tab::1.0` |
| Registry operations | `stale_stamp` | `urn:nasa:pds:smallbodiesoccultations:data::1.0` | 6 | `urn:nasa:pds:smallbodiesoccultations:data:occlist_tab::1.0`<br>`urn:nasa:pds:smallbodiesoccultations:data:occsatlist_tab::1.0`<br>`urn:nasa:pds:smallbodiesoccultations:data:occsatsummary_tab::1.0` |
| Registry operations | `stale_stamp` | `urn:nasa:pds:smallbodiesoccultations:data::2.0` | 6 | `urn:nasa:pds:smallbodiesoccultations:data:occlist_20180322_tab::2.0`<br>`urn:nasa:pds:smallbodiesoccultations:data:occsatlist_20180322_tab::2.0`<br>`urn:nasa:pds:smallbodiesoccultations:data:occsatsummary_20180712_tab::2.0` |
| Registry operations | `stale_stamp` | `urn:nasa:pds:smallbodiesoccultations:data::3.0` | 6 | `urn:nasa:pds:smallbodiesoccultations:data:occlist_2019_tab::3.0`<br>`urn:nasa:pds:smallbodiesoccultations:data:occsatlist_2019_tab::3.0`<br>`urn:nasa:pds:smallbodiesoccultations:data:occsatsummary_2019_tab::3.0` |
| Registry operations | `stale_stamp` | `urn:nasa:pds:neowise_diameters_albedos:document::1.0` | 2 | `urn:nasa:pds:neowise_diameters_albedos:document:aa_document_index::1.0`<br>`urn:nasa:pds:neowise_diameters_albedos:document:ref::1.0` |
| Registry operations | `stale_stamp` | `urn:nasa:pds:smallbodiesoccultations:document::1.0` | 1 | `urn:nasa:pds:smallbodiesoccultations:document:occ2017::1.0` |

<!-- product-samples:end -->

## Reproduce

```bash
ENV_FILE="<path-to-env-file>"
REGISTRY_CLIENT_VENV="<path-to-registry-client-venv>"
PYTHON="${REGISTRY_CLIENT_VENV}/bin/python"
REGISTRY_CLIENT="${REGISTRY_CLIENT_VENV}/bin/pds-registry-client"
NODE="sbnpsi"
OUT_DIR="./audit_unprocessed/${NODE}"
source "${ENV_FILE}"

# The audit (inventory download skipped)
"${PYTHON}" scripts/audit_unprocessed_products.py --output-dir "${OUT_DIR}" --node "${NODE}" --gzip --no-inventory

# Inventory vs registry for one collection
COLLECTION_LIDVID="urn:nasa:pds:hst.ast-ceres.uv-spectra:document::1.0"
"${PYTHON}" scripts/audit_collection.py "${COLLECTION_LIDVID}" --diff --load-status --output-dir "${OUT_DIR}/collection_audit"

# Stamp and ancestry of one stale product
LIDVID="urn:nasa:pds:iue.ast.hendrix.spectra:data:hebe_9488_refl_csv::1.0"
BODY="$(jq -n --arg id "${LIDVID}" '{size: 1, query: {term: {lidvid: $id}}, _source: ["ops:Provenance/ops:registry_sweepers_ancestry_version", "ops:Provenance/ops:ancestor_refs", "ops:Provenance/ops:superseded_by"]}')"
"${REGISTRY_CLIENT}" -d "${BODY}" "/${NODE}-registry/_search"

# API symptom: members of its collection
API_BASE="https://pds.mcp.nasa.gov/api/search/1"
PARENT="urn:nasa:pds:iue.ast.hendrix.spectra:data::1.0"
ENCODED="$(jq -rn --arg id "${PARENT}" '$id | @uri')"
curl -s -G "${API_BASE}/products/${ENCODED}/members" --data-urlencode "limit=1"
```
