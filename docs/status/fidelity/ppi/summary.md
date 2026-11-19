# Unprocessed product audit

Run time: 2026-11-19T04:03:22+00:00
Nodes: ppi

No candidate products were found: every API-visible product has current ancestry.
- Not API-visible (staged etc.) without ancestry, not counted above: 17,604 (staged 17,604)

## What needs to happen

**Healthy: nothing needs doing.**

## How this maps to the orphan repair report

The ancestry orphan repair dry run prints products examined, repairable (a refs document lists the product under a collection in the registry) and unresolved (no refs document lists it, or only under a collection that is not in the registry).

- The repair examines the 0 audit candidates plus the 17,604 products that are not API-visible, because it does not filter on archive status.
- The repair has no grace period, so waiting (`*_pending`) products are counted too.
- The audit counts any stamp other than the current version, the repair only a stamp below it.

| Audit rule | Products | Repair bucket |
|---|---|---|
| not API-visible (not audited) | 17,604 | repairable if a refs document lists it, else unresolved |
| **all (the repair's products examined)** | **17,604** |  |

## Run parameters

- Ancestry version: 7
- Collection grace period: 1 days
- Product grace period: 7 days
- Nodes: ppi
- Node filter: ppi
- Refs coverage queried for up to: 200 collections

## Regression check

Evaluated against the baseline of 2026-11-16T22:23:51+00:00.

**PASS** - every invariant holds.
