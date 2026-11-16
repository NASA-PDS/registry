# naif node audit, 2026-11-16

Terms used below. *Ancestry* is the link from a product to its collection and bundle; the public API
builds `/members` from it. The *ancestry sweeper* writes it. *Refs* are the `registry-refs` documents
Harvest writes from a collection's *inventory* (the list of member products that the data provider serves);
the sweeper reaches a product only through them. A *superseded* product has a newer version.

## Verdict

Data is healthy; search is degraded. Only 2 products (of 7,496 documents) lack ancestry; both are for registry
operations, none for the node or the sweepers team. The larger problem is the index mapping: `title`,
`description` and 8 other text fields are mapped as exact-match `keyword`, and 97 `pds:` fields are not
mapped at all.

## What needs to happen

| Who | What is wrong (plain English) | Products | Collections | What to do |
|---|---|---|---|---|
| Registry operations | The two DART SPICE 4.0 collections have no refs documents at all, although their inventories list the registered product as a primary member. So the sweeper never links the two 4.0 products, and the API lists no members for either collection | 2 | 2 | Re-harvest both collections from their current label and inventory, then run the sweepers |
| Registry operations (index owners) | NAIF maps text fields as `keyword` and lacks 97 `pds:` fields (see Index mapping) | - | all | Correct the `naif-registry` mapping and reindex |

Collections: `dart.spice:document::4.0` and `dart.spice:miscellaneous::4.0`.

## Details

**Missing refs.** The audit labelled both products `inventory_version_mismatch`; that is wrong here.
I downloaded both inventories. Each has four rows: `S,` rows for versions 1.0 to 3.0 and a `P,` row for
`::4.0`, the exact LIDVID the registry holds (`urn:nasa:pds:dart.spice:document:spiceds::4.0` and
`urn:nasa:pds:dart.spice:miscellaneous:checksum_checksum::4.0`). `naif-registry-refs` has refs documents for
versions 1.0 to 3.0 of both collections but none for either `::4.0` collection (query on `collection_lid`
returned 10 documents, none for 4.0). Versions 1.0 to 3.0 of both products are registered, superseded and
stamped 7. So the `audit_collection.py --load-status` verdict "3 products not loaded, node must load them"
is a false alarm: those three are the already-registered superseded versions, which the diff skips. The
collections are stamped 7, harvested 2025-11-05; the products (no stamp, no ancestry) were harvested
2025-11-05 too; the API returns 0 members for both. I did not determine why Harvest wrote no refs for the 4.0
collections. After a re-harvest the collection documents are replaced and are no longer stamped, so a normal
sweeper run then picks them up. Confirm: a refs document exists for each 4.0 collection, the product shows
stamp 7 with `ancestor_refs`, and `/products/<collection>/members` returns 1.

## Index mapping

Warnings and errors from `mapping_discrepancies.csv` (`naif-registry`: 134 mapped fields, 10 errors, 97 warnings):

- 10 errors: `title`, `description`, `pds:Bundle/pds:description`, `pds:Collection/pds:description`,
  `pds:Document/pds:description`, `pds:Document/pds:document_name`, `pds:Citation_Information/pds:author_list`,
  `pds:Citation_Information/pds:description`, `pds:Field_Character/pds:description` and
  `pds:SPICE_Kernel/pds:description` are `keyword` on naif and `text` on every other node.
- Effect on search (queried the index directly): a word match for `BepiColombo` in `title` finds 0 NAIF
  products, the exact full title finds 5, and a case-sensitive wildcard `*BepiColombo*` finds 43. The same kind
  of word match on sbnpsi `title` finds 17,515. Free-text and relevance search on NAIF titles and descriptions
  does not work; I did not test how the public API translates its searches.
- 97 warnings: `pds:` fields (for example `pds:Science_Facets/*`, `pds:Observing_System/pds:name`,
  `pds:Table_Delimited` and `pds:Field_Binary` fields, `pds:Modification_Detail/*`) are absent from the mapping,
  so their values cannot be searched or filtered. Fixing the types normally needs a new index and a reindex
  (not verified). Owner: registry operations with the index owners.

## Reproduce

```bash
ENV_FILE="<path-to-env-file>"
REGISTRY_CLIENT_VENV="<path-to-registry-client-venv>"
PYTHON="${REGISTRY_CLIENT_VENV}/bin/python"
REGISTRY_CLIENT="${REGISTRY_CLIENT_VENV}/bin/pds-registry-client"
NODE="naif"
OUT_DIR="./audit_unprocessed/${NODE}"
source "${ENV_FILE}"

# The audit (inventory download skipped)
"${PYTHON}" scripts/audit_unprocessed_products.py --output-dir "${OUT_DIR}" --node "${NODE}" --gzip --no-inventory

# Inventory vs registry (the inventory has a P row for ::4.0 and S rows for older versions)
COLLECTION_LIDVID="urn:nasa:pds:dart.spice:document::4.0"
"${PYTHON}" scripts/audit_collection.py "${COLLECTION_LIDVID}" --diff --load-status --active-days 14 --output-dir "${OUT_DIR}/collection_audit"

# Refs documents for every version of the collection
COLLECTION_LID="urn:nasa:pds:dart.spice:document"
BODY="$(jq -n --arg lid "${COLLECTION_LID}" '{size: 20, query: {term: {collection_lid: $lid}}, _source: ["collection_lidvid", "reference_type", "product_lidvid"]}')"
"${REGISTRY_CLIENT}" -d "${BODY}" "/${NODE}-registry-refs/_search"

# Search symptom: word match versus exact title
WORD_QUERY='{"query": {"match": {"title": "BepiColombo"}}}'
"${REGISTRY_CLIENT}" -d "${WORD_QUERY}" "/${NODE}-registry/_count"
WILDCARD_QUERY='{"query": {"wildcard": {"title": "*BepiColombo*"}}}'
"${REGISTRY_CLIENT}" -d "${WILDCARD_QUERY}" "/${NODE}-registry/_count"

# Mapping audit rows for this node
MAPPING_CSV="<path-to-mapping_discrepancies.csv>"
grep "^registry,${NODE}-registry," "${MAPPING_CSV}"
```
