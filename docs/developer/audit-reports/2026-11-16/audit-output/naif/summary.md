# Unprocessed product audit

Run time: 2026-11-16T22:23:50+00:00
Nodes: naif

- Candidates examined: **2**
- Expected (should resolve on their own): **0**
- Anomalous (need attention): **2**

## What needs to happen

**Needs attention: 2 for registry operations.**

| Who | What is wrong | Products | Collections | What to do |
|---|---|--:|--:|---|
| Registry operations | **Orphaned**: The collection's inventory lists these products but the registry's refs do not (stale or never written) | 2 | 2 | Re-harvest the collection, then run the sweepers |

Kinds of problem:

- **Orphaned**: no registry record confirms which collection the product belongs to. The collection named for it in this report is a best guess from its identifier; it may really belong to a collection version that is not loaded.

Who fixes what:

- **Registry operations**: the node's data is fine and the registry's own processing missed it; fixed by re-harvesting the collection and running the sweepers.

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

- **refs_missing** (2 products): The collection is processed but no registry-refs document lists the product, so the sweeper never selects it. The refs were probably never written for this product; the loader or harvest step is the likely place to look.

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
