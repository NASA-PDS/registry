# Unprocessed product audit

Run time: 2026-11-16T22:23:50+00:00
Nodes: naif

- Candidates examined: **2**
- Expected (should resolve on their own): **0**
- Anomalous (need attention): **2**

## What needs to happen

**Needs attention: 2 for the node.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Node | **Orphaned**: The collection's inventory lists these products but the registry's refs do not (stale or never written) | 2 | 2 | Re-harvest the collection from its current label and inventory; EN then runs the sweepers |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.

Who fixes what:

- **Node**: the node's data does not line up (a collection or product is missing, at the wrong version, or not in the collection's inventory), or the collection has to be re-harvested by the node so that the registry's refs are rewritten from its inventory; EN then runs the sweepers.

## Anomalies by rule

| Rule | Products |
|---|---|
| refs_missing | 2 |

### By rule and node

| Rule | Node | Products |
|---|---|---|
| refs_missing | naif | 2 |

## Anomalous collections

2 collections root at least one anomalous product, worst first. Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.

| Node | Bundle(s) | Collection | State | Harvested | Affected products | Refs coverage |
|---|---|---|---|---|---|---|
| naif | urn:nasa:pds:dart.spice::1.0, urn:nasa:pds:dart.spice::2.0, urn:nasa:pds:dart.spice (+2 more) | urn:nasa:pds:dart.spice:document::4.0 | processed | 2025-11-05T22:29:41+00:00 | 1 | refs missing for 1 members (refs never written) |
| naif | urn:nasa:pds:dart.spice::1.0, urn:nasa:pds:dart.spice::2.0, urn:nasa:pds:dart.spice (+2 more) | urn:nasa:pds:dart.spice:miscellaneous::4.0 | processed | 2025-11-05T22:30:58+00:00 | 1 | refs missing for 1 members (refs never written) |

## Breakdown

### By product class

| Product class | Expected | Anomalous | Total |
|---|---|---|---|
| Product_Ancillary | 0 | 1 | 1 |
| Product_Document | 0 | 1 | 1 |

### By harvest age

| Age | Expected | Anomalous | Total |
|---|---|---|---|
| >30d | 0 | 2 | 2 |

## What each rule means

- **refs_missing** (2 products): The collection is processed and has refs, but no registry-refs document lists this product, so the sweeper never selects it. Harvest writes a collection's refs from its inventory when the collection is harvested, so the inventory read at that time did not list the product, or the inventory has changed since, or the refs were not written. Read the collection's current inventory. If it lists this exact product, the refs are stale: the node re-harvests the collection from its current label and inventory, then EN runs the sweepers. If it lists another version of the product or does not list it, the node's data does not line up and the node fixes it (the audit reports those as inventory_version_mismatch and not_in_collection_inventory when it can read the inventory). The collection named for the product is a best guess from its identifier.

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: naif
- Node filter: naif
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated with no baseline (any anomaly fails).

**FAIL** - 1 invariant(s) violated.

- `no_anomalous_products`: 2 products are anomalous
  - refs_missing: 2
