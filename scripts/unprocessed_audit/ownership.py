"""Who has to act on each audit finding, in plain language.

The audit rules are technical. This module maps each rule to the party that can fix it, to the kind of problem it
is, and to a one-line description of the problem and the fix, so a report can say "the node must load these
collections" or "registry operations must re-harvest these collections" instead of listing rule names.

Ancestry is produced in two steps. Harvest writes ``registry-refs`` documents from a collection's inventory when
the collection is harvested; they are the registry's record of which products belong to which collection. The
ancestry sweeper then reaches a non-aggregate product only through those refs, and does not revisit a collection
once it is stamped. A product therefore lacks ancestry in one of two ways:

* **Orphaned**: no registry record confirms its parent collection. The collection a report names for it is a best
  guess from its identifier (``bundle:collection:product``) and the collection versions that are registered; the
  product may really belong to a collection version that is not loaded. Usually the node's data does not line up
  (the collection is not loaded, the inventory lists another version, the inventory does not list the product);
  sometimes the refs are stale or were never written, which registry operations fix by re-harvesting.
* **Not processed**: the refs do list the product, so its parent is confirmed, but the sweepers never gave it
  ancestry (it was loaded after its collection was processed, it carries an older stamp, or a sweepers bug).
"""

from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from unprocessed_audit.model import Collection
from unprocessed_audit.model import CollectionState
from unprocessed_audit.model import Rule


class Owner(str, Enum):
    """The party that can fix a finding."""

    NODE = "node"
    REGISTRY_OPERATIONS = "registry_operations"
    SWEEPERS_TEAM = "sweepers_team"
    NEEDS_CHECK = "needs_check"
    NO_ACTION = "no_action"


class Kind(str, Enum):
    """What kind of problem a finding is."""

    ORPHANED = "orphaned"
    NOT_PROCESSED = "not_processed"
    WAITING = "waiting"


OWNER_LABELS: dict[Owner, str] = {
    Owner.NODE: "Node",
    Owner.REGISTRY_OPERATIONS: "Registry operations",
    Owner.SWEEPERS_TEAM: "Sweepers team",
    Owner.NEEDS_CHECK: "Needs a closer look",
    Owner.NO_ACTION: "No action",
}

OWNER_MEANING: dict[Owner, str] = {
    Owner.NODE: "the node's data does not line up (a collection or product is missing, at the wrong version, or "
    "not in the collection's inventory); only the node can fix it",
    Owner.REGISTRY_OPERATIONS: "the node's data is fine and the registry's own processing missed it; fixed by "
    "re-harvesting the collection and running the sweepers",
    Owner.SWEEPERS_TEAM: "everything looks right but the sweepers cannot or do not follow it; a software gap, "
    "possibly worked around by the node",
    Owner.NEEDS_CHECK: "the cause cannot be told apart because the collection inventory could not be used",
    Owner.NO_ACTION: "loaded recently; expected to resolve by itself",
}

KIND_LABELS: dict[Kind, str] = {
    Kind.ORPHANED: "Orphaned",
    Kind.NOT_PROCESSED: "Not processed",
    Kind.WAITING: "Waiting",
}

KIND_MEANING: dict[Kind, str] = {
    Kind.ORPHANED: "no registry record confirms which collection the product belongs to. The collection named for "
    "it in this report is a best guess from its identifier; it may really belong to a collection version that is "
    "not loaded",
    Kind.NOT_PROCESSED: "the registry's refs list the product, so its collection is confirmed, but the sweepers "
    "never gave it ancestry",
    Kind.WAITING: "loaded recently; expected to resolve by itself",
}

_OWNER_ORDER = list(Owner)


@dataclass(frozen=True)
class Problem:
    """A finding in plain language.

    Attributes:
        owner: Who fixes it.
        kind: Whether the product is orphaned, not processed, or only waiting.
        title: What is wrong.
        action: What to do about it.
    """

    owner: Owner
    kind: Kind
    title: str
    action: str


RULE_PROBLEMS: dict[Rule, Problem] = {
    Rule.COLLECTION_NOT_LOADED_OVERDUE: Problem(
        Owner.NODE,
        Kind.ORPHANED,
        "No collection with the identifier these products belong to is in the registry",
        "Load the collection, or correct the product identifiers",
    ),
    Rule.INVENTORY_VERSION_MISMATCH: Problem(
        Owner.NODE,
        Kind.ORPHANED,
        "The collection's inventory lists a different version of these products than the one loaded",
        "Load the version the inventory lists, or correct the inventory",
    ),
    Rule.NOT_IN_COLLECTION_INVENTORY: Problem(
        Owner.NODE,
        Kind.ORPHANED,
        "The collection's inventory does not list these products under any version",
        "Add them to the inventory, or remove the products from the registry",
    ),
    Rule.BARE_LID_IN_INVENTORY: Problem(
        Owner.SWEEPERS_TEAM,
        Kind.ORPHANED,
        "The collection's inventory lists these products by LID without a version, which the sweepers do not follow",
        "Re-harvesting does not help. The node lists LIDVIDs in the inventory, or the sweepers support LID references",
    ),
    Rule.REFS_MISSING: Problem(
        Owner.REGISTRY_OPERATIONS,
        Kind.ORPHANED,
        "The collection's inventory lists these products but the registry's refs do not (stale or never written)",
        "Re-harvest the collection, then run the sweepers",
    ),
    Rule.RELOADED_AFTER_COLLECTION: Problem(
        Owner.REGISTRY_OPERATIONS,
        Kind.NOT_PROCESSED,
        "Linked to their collection, but loaded after the sweepers processed it, so the sweepers never went back",
        "Re-harvest the collection, then run the sweepers",
    ),
    Rule.STALE_STAMP: Problem(
        Owner.REGISTRY_OPERATIONS,
        Kind.NOT_PROCESSED,
        "Linked to their collection, but processed by an older sweepers version while the collection is on the "
        "current one, so the sweepers do not go back",
        "Re-harvest the collection, then run the sweepers",
    ),
    Rule.COLLECTION_OVERDUE: Problem(
        Owner.REGISTRY_OPERATIONS,
        Kind.NOT_PROCESSED,
        "The collection these products belong to is loaded but the sweepers never processed it",
        "Run the sweepers (re-harvest the collection first if it has no refs)",
    ),
    Rule.SWEEPER_MISS: Problem(
        Owner.SWEEPERS_TEAM,
        Kind.NOT_PROCESSED,
        "Linked to their collection, and the collection and its refs look complete, yet the sweepers skipped them",
        "Report to the sweepers team with the collection list",
    ),
    Rule.COLLECTION_NOT_LOADED_PENDING: Problem(
        Owner.NO_ACTION, Kind.WAITING, "Waiting for the collection to be loaded", "None; re-check later"
    ),
    Rule.COLLECTION_PENDING: Problem(
        Owner.NO_ACTION, Kind.WAITING, "Waiting for the sweepers to process the collection", "None; re-check later"
    ),
    Rule.REFS_MISSING_PENDING: Problem(
        Owner.NO_ACTION, Kind.WAITING, "Not in the registry's refs yet", "None; re-check later"
    ),
    Rule.NO_PARENT_BY_DESIGN: Problem(
        Owner.NO_ACTION, Kind.WAITING, "Product classes that never belong to a collection", "None"
    ),
}

REFS_MISSING_UNVERIFIED = Problem(
    Owner.NEEDS_CHECK,
    Kind.ORPHANED,
    "No refs record lists these products and the collection inventory could not be used to say why",
    "Re-run the audit with the inventories (not --no-inventory), or check the collection's inventory by hand",
)

EMPTY_REFS_PROBLEM = Problem(
    Owner.REGISTRY_OPERATIONS,
    Kind.NOT_PROCESSED,
    "The collection is marked processed but has no link to its bundle, so the bundle does not list it as a member",
    "Re-harvest the collection, then run the sweepers (the sweepers bug that caused this is fixed in "
    "registry-sweepers PR #286)",
)


@dataclass(frozen=True)
class ActionRow:
    """One line of the "what needs to happen" table.

    Attributes:
        problem: The problem in plain language.
        rule: The audit rule behind it, or ``None`` for the empty-refs collection row.
        products: Products affected; ``None`` when the row is about collections only.
        collections: Collections affected; ``None`` when not applicable.
    """

    problem: Problem
    rule: Rule | None
    products: int | None
    collections: int | None

    @property
    def owner(self) -> Owner:
        """Who fixes it."""
        return self.problem.owner

    @property
    def kind(self) -> Kind:
        """What kind of problem it is."""
        return self.problem.kind


def owner_of(rule: Rule | str, verified: bool = True) -> Owner:
    """Return who fixes findings of a rule.

    Args:
        rule: The audit rule.
        verified: For ``refs_missing`` only: whether the collection inventory was used to reach the verdict.

    Returns:
        The owner; an unverified ``refs_missing`` needs a closer look.
    """
    rule = Rule(rule)
    if rule is Rule.REFS_MISSING and not verified:
        return REFS_MISSING_UNVERIFIED.owner
    return RULE_PROBLEMS[rule].owner


def count_by_owner(rule_counts: Mapping[str, int], unverified_refs_missing: int = 0) -> dict[str, int]:
    """Sum product counts by owner.

    Args:
        rule_counts: Product count per rule value.
        unverified_refs_missing: How many of the ``refs_missing`` products were reached without the inventory.

    Returns:
        Product count per owner value, with every owner present.
    """
    totals = {owner.value: 0 for owner in Owner}
    for rule, count in rule_counts.items():
        if Rule(rule) is Rule.REFS_MISSING:
            totals[REFS_MISSING_UNVERIFIED.owner.value] += unverified_refs_missing
            count -= unverified_refs_missing
        totals[owner_of(rule).value] += count
    return totals


def empty_refs_collections(collections: Iterable[Collection]) -> list[Collection]:
    """Return the current collections that are stamped with empty refs although they have a bundle."""
    return [
        c
        for c in collections
        if c.state is CollectionState.STAMPED_EMPTY_REFS and c.bundle_lidvids and not c.superseded_by
    ]


def build_rows(
    anomalous_counts: Mapping[str, int],
    expected_counts: Mapping[str, int],
    collections_per_rule: Mapping[str, int],
    empty_refs_count: int,
    unverified_refs_missing: int = 0,
) -> list[ActionRow]:
    """Build the table rows, ordered by owner and then by product count.

    Args:
        anomalous_counts: Anomalous product count per rule value.
        expected_counts: Expected (pending) product count per rule value.
        collections_per_rule: Number of collections that root anomalous products, per rule value.
        empty_refs_count: Collections stamped with empty refs that have a bundle.
        unverified_refs_missing: How many of the ``refs_missing`` products were reached without the inventory.

    Returns:
        The rows; owners with nothing to report are absent.
    """
    rows: list[ActionRow] = []
    for rule_value, count in anomalous_counts.items():
        rule = Rule(rule_value)
        collections = collections_per_rule.get(rule_value)
        if rule is Rule.REFS_MISSING and unverified_refs_missing:
            rows.append(ActionRow(REFS_MISSING_UNVERIFIED, rule, unverified_refs_missing, collections))
            count -= unverified_refs_missing
        if count > 0:
            rows.append(ActionRow(RULE_PROBLEMS[rule], rule, count, collections))
    for rule_value, count in expected_counts.items():
        if count:
            rows.append(ActionRow(RULE_PROBLEMS[Rule(rule_value)], Rule(rule_value), count, None))
    if empty_refs_count:
        rows.append(ActionRow(EMPTY_REFS_PROBLEM, None, None, empty_refs_count))
    return sorted(rows, key=lambda r: (_OWNER_ORDER.index(r.owner), -(r.products or 0), -(r.collections or 0)))


def collections_per_rule(rule_counts_by_collection: Iterable[Mapping[str, int]]) -> dict[str, int]:
    """Count, per rule, the collections that root at least one anomalous product of that rule."""
    totals: dict[str, int] = {}
    for rule_counts in rule_counts_by_collection:
        for rule, count in rule_counts.items():
            if count:
                totals[rule] = totals.get(rule, 0) + 1
    return totals


def verdict(rows: Iterable[ActionRow]) -> str:
    """Summarise the rows in one sentence.

    Args:
        rows: Rows from ``build_rows``.

    Returns:
        A sentence such as ``Needs attention: 1,200 for node; 30 for registry operations.``.
    """
    needs: dict[Owner, int] = {}
    for row in rows:
        if row.owner is Owner.NO_ACTION:
            continue
        amount = row.products if row.products is not None else row.collections or 0
        needs[row.owner] = needs.get(row.owner, 0) + amount
    if not needs:
        return "Healthy: nothing needs doing."
    parts = [f"{count:,} for {OWNER_LABELS[owner].lower()}" for owner, count in needs.items()]
    return "Needs attention: " + "; ".join(parts) + "."
