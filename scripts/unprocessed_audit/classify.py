"""Pure classification logic for the unprocessed product audit.

Nothing in this module performs I/O. Callers supply collection state, candidate products and (for
products whose collection was already processed) the ``registry-refs`` lookup result, and receive a
:class:`~unprocessed_audit.model.Verdict` back. The rules follow
``docs/developer/audit-unprocessed-products-design.md``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from datetime import timezone

from unprocessed_audit.inventory import InventoryIndex
from unprocessed_audit.model import Candidate
from unprocessed_audit.model import Collection
from unprocessed_audit.model import CollectionState
from unprocessed_audit.model import NO_PARENT_CLASSES
from unprocessed_audit.model import Population
from unprocessed_audit.model import Rule
from unprocessed_audit.model import Severity
from unprocessed_audit.model import Thresholds
from unprocessed_audit.model import Verdict

logger = logging.getLogger(__name__)

_COLLECTION_LID_SEGMENTS = 5
_BUNDLE_LID_SEGMENTS = 4

_PROCESSED_STATES = (CollectionState.PROCESSED, CollectionState.STAMPED_EMPTY_REFS)

RULE_GUIDANCE: dict[Rule, str] = {
    Rule.NO_PARENT_BY_DESIGN: (
        "These product classes never belong to a collection, so they never receive ancestry. "
        "No action is needed."
    ),
    Rule.COLLECTION_NOT_LOADED_PENDING: (
        "The parent collection is not in the registry yet and the product was harvested recently. "
        "This is expected to resolve once the collection is loaded and swept."
    ),
    Rule.COLLECTION_NOT_LOADED_OVERDUE: (
        "The parent collection is still not in the registry (or is not API-visible) long after the product "
        "was harvested. Check whether the collection failed to load, is staged or superseded, or whether the "
        "product LID does not follow the bundle:collection:product pattern."
    ),
    Rule.COLLECTION_PENDING: (
        "The parent collection has not been through the ancestry sweeper yet but was harvested recently. "
        "This is expected to resolve on its own at the next sweeper run."
    ),
    Rule.COLLECTION_OVERDUE: (
        "The parent collection has not been processed by the ancestry sweeper long after it was harvested, "
        "which leaves all of its products without ancestry. Investigate the collection first (for example "
        "with audit_collection.py); the products are a symptom."
    ),
    Rule.RELOADED_AFTER_COLLECTION: (
        "The product was loaded or overwritten after its collection was processed, so the sweeper has no reason "
        "to revisit it. This is EN's to fix: EN runs the ancestry orphan repair, and the node need not "
        "re-harvest anything."
    ),
    Rule.INVENTORY_VERSION_MISMATCH: (
        "The collection's inventory (as recorded in registry-refs) lists this product at a different version "
        "than the one in the registry, so the sweeper never selects the registered version. Re-harvesting the "
        "collection will not help: load the product version the inventory lists, after which the registered "
        "version is superseded. Confirm with audit_collection.py --diff."
    ),
    Rule.NOT_IN_COLLECTION_INVENTORY: (
        "The product is registered under this collection's LID, but the collection's current inventory does "
        "not list it under any version, so the sweeper can never give it this collection as an ancestor. "
        "The provider may have dropped it from the inventory or it may be a leftover. The node should decide "
        "whether it belongs in the inventory or should be removed from the registry; re-harvesting or "
        "loading more products will not fix it."
    ),
    Rule.SWEEPER_MISS: (
        "The collection was processed and harvested no earlier than the product, and refs list the product, "
        "yet it has no ancestry. Nothing in the registry data explains the gap; this needs a closer look at "
        "the sweeper run for this collection."
    ),
    Rule.REFS_MISSING_PENDING: (
        "The collection is processed but no registry-refs document lists the product, and the product was "
        "harvested within the grace period, so a load may still be running. Re-check after the grace period; "
        "if the product is still missing, it is classified like refs_missing."
    ),
    Rule.REFS_MISSING: (
        "The collection is processed and has refs, but no registry-refs document lists this product, so the "
        "sweeper never selects it. Harvest writes a collection's refs from its inventory when the collection is "
        "harvested, so the inventory read at that time did not list the product, or the inventory has changed "
        "since, or the refs were not written. Read the collection's current inventory. If it lists this exact "
        "product, the refs are stale: the node re-harvests the collection from its current label and "
        "inventory so Harvest rewrites the refs. If it lists another version of the product or does not list it, the "
        "node's data does not line up and the node fixes it (the audit reports those as "
        "inventory_version_mismatch and not_in_collection_inventory when it can read the inventory). The "
        "collection named for the product is a best guess from its identifier."
    ),
    Rule.BARE_LID_IN_INVENTORY: (
        "The collection's inventory lists the product by LID only, without a version. Harvest records that as a "
        "product_lid in the registry-refs document, but the ancestry sweeper follows only product_lidvid, so it "
        "never reaches the product. Re-harvesting the collection writes the same refs; the inventory must list "
        "LIDVIDs, or the sweepers must follow LID references."
    ),
    Rule.STALE_STAMP: (
        "The product carries an ancestry stamp from an older sweeper version although its collection is "
        "already on the current version. The collection will not be revisited. This is EN's to fix: EN runs "
        "the ancestry orphan repair."
    ),
}


# ── parsing helpers ───────────────────────────────────────────────────────────


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp.

    Args:
        value: Timestamp text. A trailing ``Z`` is accepted.

    Returns:
        A timezone-aware datetime (naive input is taken as UTC), or ``None`` when ``value`` is
        missing or unparseable.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text[-1] in ("Z", "z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        logger.debug("Unparseable timestamp: %r", value)
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _aware(when: datetime) -> datetime:
    """Return ``when`` as timezone-aware, taking naive values as UTC."""
    return when if when.tzinfo is not None else when.replace(tzinfo=timezone.utc)


def age_days(when: datetime | None, now: datetime) -> float | None:
    """Return the number of days between ``when`` and ``now``.

    Args:
        when: Earlier time, or ``None`` if unknown.
        now: Reference time.

    Returns:
        Fractional days (negative if ``when`` is in the future), or ``None`` when ``when`` is ``None``.
    """
    if when is None:
        return None
    return (_aware(now) - _aware(when)).total_seconds() / 86400.0


def _lid_prefix(product_lid: str, segments: int, required: int) -> str | None:
    """Join the first ``segments`` colon-separated parts of a LID, if it has ``required`` parts."""
    parts = product_lid.split(":")
    if len(parts) < required:
        return None
    head = parts[:segments]
    if any(not part for part in head):
        return None
    return ":".join(head)


def derive_collection_lid(product_lid: str) -> str | None:
    """Derive the parent collection LID from a product LID.

    Args:
        product_lid: LID of the form ``urn:<agency>:<archive>:<bundle>:<collection>:<product>``.

    Returns:
        The first five segments joined by ``:``, or ``None`` when the LID has fewer than six segments.
    """
    return _lid_prefix(product_lid, _COLLECTION_LID_SEGMENTS, _COLLECTION_LID_SEGMENTS + 1)


def derive_bundle_lid(product_lid: str) -> str | None:
    """Derive the bundle LID from a product (or collection) LID.

    Args:
        product_lid: LID with at least five colon-separated segments.

    Returns:
        The first four segments joined by ``:``, or ``None`` when the LID has fewer than five.
    """
    return _lid_prefix(product_lid, _BUNDLE_LID_SEGMENTS, _BUNDLE_LID_SEGMENTS + 1)


def _lid_of(lidvid: str) -> str:
    """Strip the ``::<version>`` suffix from a LIDVID."""
    return lidvid.split("::", 1)[0]


def is_member_class(product_class: str) -> bool:
    """Return whether products of this class can belong to a collection."""
    return product_class not in NO_PARENT_CLASSES


# ── population and collection state ───────────────────────────────────────────


def population_of(stamp: str | None, has_ancestor_refs: bool, ancestry_version: int) -> Population | None:
    """Decide which population a product falls in.

    Args:
        stamp: Raw ancestry stamp, ``None`` when absent.
        has_ancestor_refs: Whether ``ancestor_refs`` is non-empty.
        ancestry_version: Current ancestry version.

    Returns:
        ``NO_STAMP`` for no stamp, ``STALE_STAMP`` for any stamp other than the current version
        (including non-numeric text), ``EMPTY_REFS`` for a current stamp without refs, and ``None``
        for a fully processed product.
    """
    if stamp is None:
        return Population.NO_STAMP
    if stamp != str(ancestry_version):
        return Population.STALE_STAMP
    if not has_ancestor_refs:
        return Population.EMPTY_REFS
    return None


def classify_collection(collection: Collection, th: Thresholds) -> CollectionState:
    """Classify a collection's ancestry-processing state.

    Args:
        collection: Collection to classify.
        th: Run thresholds.

    Returns:
        The collection state. An unprocessed collection with an unknown harvest time is overdue.
    """
    if collection.stamp == str(th.ancestry_version):
        if collection.ancestor_refs:
            return CollectionState.PROCESSED
        return CollectionState.STAMPED_EMPTY_REFS
    age = age_days(collection.harvest, th.now)
    if age is not None and age <= th.collection_grace_days:
        return CollectionState.UNPROCESSED_PENDING
    return CollectionState.UNPROCESSED_OVERDUE


# ── collection resolution ─────────────────────────────────────────────────────


def _state_of(collection: Collection) -> CollectionState:
    """Return a collection's state, which the caller must already have set."""
    if collection.state is None:
        raise ValueError(f"collection state not set for {collection.lidvid}")
    return collection.state


def _harvest_sort_key(collection: Collection) -> datetime:
    """Sort key placing collections with an unknown harvest time before all others."""
    if collection.harvest is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return _aware(collection.harvest)


def resolve_collection(
    derived_lid: str | None,
    refs_collection_lidvid: str | None,
    collections_by_lid: Mapping[str, Sequence[Collection]],
    product_lidvid: str | None = None,
) -> Collection | None:
    """Find the collection a product belongs to.

    Args:
        derived_lid: Collection LID derived from the product LID (may be ``None``).
        refs_collection_lidvid: ``collection_lidvid`` of the refs document listing the product, if known.
        collections_by_lid: Collections (with ``state`` set) keyed by LID. Superseded versions are included.
        product_lidvid: The product's LIDVID, used to choose among several collection versions.

    Returns:
        With a refs LIDVID, the collection with exactly that LIDVID or ``None``. Otherwise the only
        version; for several versions, the one whose version equals the product's version if exactly
        one does; otherwise a representative among the current (non-superseded) versions, or among all
        of them when none is current: the latest-harvested one when all are processed, else the worst
        unprocessed one (overdue before pending).
    """
    if refs_collection_lidvid is not None:
        for collection in collections_by_lid.get(_lid_of(refs_collection_lidvid), []):
            if collection.lidvid == refs_collection_lidvid:
                return collection
        return None
    if derived_lid is None:
        return None
    versions = collections_by_lid.get(derived_lid, [])
    if not versions:
        return None
    if len(versions) == 1:
        return versions[0]
    if product_lidvid is not None and "::" in product_lidvid:
        # Heuristic: a product registered with the same version number as one collection version
        # (for example ``...::2.1`` under collection ``...::2.1``) belongs to that version.
        product_version = product_lidvid.split("::", 1)[1]
        same_version = [c for c in versions if c.lidvid.split("::", 1)[-1] == product_version]
        if len(same_version) == 1:
            return same_version[0]
    versions = [c for c in versions if c.superseded_by is None] or list(versions)
    if len(versions) == 1:
        return versions[0]
    unprocessed = [c for c in versions if _state_of(c) not in _PROCESSED_STATES]
    if not unprocessed:
        return max(versions, key=_harvest_sort_key)
    overdue = [c for c in unprocessed if _state_of(c) == CollectionState.UNPROCESSED_OVERDUE]
    pool = overdue or unprocessed
    return max(pool, key=_harvest_sort_key)


def needs_refs_lookup(
    candidate: Candidate,
    th: Thresholds,
    collections_by_lid: Mapping[str, Sequence[Collection]],
) -> bool:
    """Return whether ``registry-refs`` must be consulted to classify this candidate.

    Args:
        candidate: Candidate product.
        th: Run thresholds.
        collections_by_lid: API-visible collections keyed by LID.

    Returns:
        ``True`` only for member-class products that are not stale-stamped and whose derived
        collection (resolved without refs) is processed or stamped with empty refs.
    """
    if not is_member_class(candidate.product_class):
        return False
    population = population_of(candidate.stamp, candidate.has_ancestor_refs, th.ancestry_version)
    if population is None or population == Population.STALE_STAMP:
        return False
    collection = resolve_collection(derive_collection_lid(candidate.lid), None, collections_by_lid, candidate.lidvid)
    if collection is None:
        return False
    return _state_of(collection) in _PROCESSED_STATES


# ── product classification ────────────────────────────────────────────────────


def _fmt_age(age: float | None) -> str:
    """Format an age in days to one decimal, or ``unknown``."""
    return "unknown" if age is None else f"{age:.1f}"


def _fmt_ts(when: datetime | None) -> str:
    """Format a timestamp for a rationale, or ``unknown``."""
    return "unknown" if when is None else _aware(when).strftime("%Y-%m-%dT%H:%M:%SZ")


def _version_tuple(lidvid: str) -> tuple[int, ...] | None:
    """Return the numeric parts of a LIDVID's version (``urn:a:b::2.10`` gives ``(2, 10)``), or ``None``."""
    _, _, version = lidvid.partition("::")
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return None


def _compare_versions(registered: str, listed: str) -> int:
    """Compare two LIDVID versions: positive when ``registered`` is newer, negative when older, 0 if equal or unknown."""
    a, b = _version_tuple(registered), _version_tuple(listed)
    if a is None or b is None or a == b:
        return 0
    return 1 if a > b else -1


def classify_product(
    candidate: Candidate,
    th: Thresholds,
    collections_by_lid: Mapping[str, Sequence[Collection]],
    refs_collection_lidvid: str | None = None,
    refs_checked: bool = False,
    listed_in_refs: Sequence[tuple[str, str | None]] = (),
    inventory_for: Callable[[Collection], InventoryIndex | None] | None = None,
) -> Verdict:
    """Assign a rule, severity and rationale to one candidate product.

    Args:
        candidate: Candidate product (must lack current ancestry).
        th: Run thresholds.
        collections_by_lid: API-visible collections (with ``state`` set) keyed by LID.
        refs_collection_lidvid: ``collection_lidvid`` of the refs document listing the product.
        refs_checked: Whether ``registry-refs`` was consulted. When ``True`` and
            ``refs_collection_lidvid`` is ``None``, no refs document lists the product.
        listed_in_refs: Only meaningful when no refs document lists the product's LIDVID: the
            ``(product LIDVID, collection LIDVID)`` pairs under which refs list the same product LID (a
            different version). Only a listing that comes from the product's own collection counts as a version
            mismatch; a listing from another version of the collection says nothing about this one.
        inventory_for: Returns the parsed current inventory of a collection, or ``None`` when it is
            unavailable. Consulted only for a product that no refs document lists, to tell whether the
            inventory lists it (stale refs), lists another version of it, or does not list it at all.

    Returns:
        The verdict for the candidate.

    Raises:
        ValueError: If the candidate is fully processed, or if its collection is processed and
            ``refs_checked`` is ``False`` for a product that needs the refs lookup.
    """
    population = population_of(candidate.stamp, candidate.has_ancestor_refs, th.ancestry_version)
    if population is None:
        raise ValueError("candidate is fully processed")

    in_refs: bool | None = None
    if refs_checked:
        in_refs = refs_collection_lidvid is not None
    bundle_lid = derive_bundle_lid(candidate.lid)
    p_age = age_days(candidate.harvest, th.now)

    def verdict(
        rule: Rule,
        severity: Severity,
        rationale: str,
        collection: Collection | None = None,
        collection_lidvid: str | None = None,
    ) -> Verdict:
        return Verdict(
            population=population,
            rule=rule,
            severity=severity,
            rationale=rationale,
            bundle_lid=bundle_lid,
            collection_lidvid=collection.lidvid if collection is not None else collection_lidvid,
            collection_state=collection.state if collection is not None else None,
            collection_harvest=collection.harvest if collection is not None else None,
            in_refs=in_refs,
        )

    # Rule 1: classes that never have a parent.
    if not is_member_class(candidate.product_class):
        return verdict(
            Rule.NO_PARENT_BY_DESIGN,
            Severity.EXPECTED,
            f"{candidate.product_class} products never belong to a collection, so no ancestry is expected.",
        )

    # Rule 2: the parent collection is not loaded.
    derived_lid = derive_collection_lid(candidate.lid)
    use_refs = refs_collection_lidvid if refs_checked else None
    collection = resolve_collection(derived_lid, use_refs, collections_by_lid, candidate.lidvid)
    if collection is None:
        if use_refs is not None:
            target = f"collection {use_refs} listed in refs"
        elif derived_lid is None:
            target = "collection (the product LID cannot be parsed into a collection LID, treated as not loaded)"
        else:
            target = f"collection {derived_lid}"
        if p_age is None:
            overdue = True
            age_text = "product harvest time unknown, treated as overdue"
        else:
            overdue = p_age > th.product_grace_days
            age_text = f"product harvested {_fmt_age(p_age)} days ago"
        if overdue:
            return verdict(
                Rule.COLLECTION_NOT_LOADED_OVERDUE,
                Severity.ANOMALOUS,
                f"No API-visible {target}; {age_text}, product grace {th.product_grace_days:g} days.",
                collection_lidvid=use_refs,
            )
        return verdict(
            Rule.COLLECTION_NOT_LOADED_PENDING,
            Severity.EXPECTED,
            f"No API-visible {target}; {age_text}, within product grace {th.product_grace_days:g} days.",
            collection_lidvid=use_refs,
        )

    state = _state_of(collection)
    c_age = age_days(collection.harvest, th.now)
    c_desc = f"collection {collection.lidvid} is {state.value}"
    if collection.superseded_by:
        c_desc += f" (superseded by {collection.superseded_by})"

    # Rule 3: collection not yet processed; it is the root cause.
    if state == CollectionState.UNPROCESSED_PENDING:
        return verdict(
            Rule.COLLECTION_PENDING,
            Severity.EXPECTED,
            f"{c_desc}, harvested {_fmt_age(c_age)} days ago, within collection grace "
            f"{th.collection_grace_days:g} days.",
            collection,
        )
    if state == CollectionState.UNPROCESSED_OVERDUE:
        if c_age is None:
            when_text = "collection harvest time unknown, treated as overdue"
        else:
            when_text = f"harvested {_fmt_age(c_age)} days ago, beyond collection grace {th.collection_grace_days:g} days"
        return verdict(
            Rule.COLLECTION_OVERDUE,
            Severity.ANOMALOUS,
            f"{c_desc}, {when_text}; the collection is the root cause.",
            collection,
        )

    # Rule 4: collection processed, product carries an old stamp.
    if population == Population.STALE_STAMP:
        return verdict(
            Rule.STALE_STAMP,
            Severity.ANOMALOUS,
            f"Product stamp {candidate.stamp!r} is not the current version {th.ancestry_version} but {c_desc}.",
            collection,
        )

    if not refs_checked:
        raise ValueError("refs lookup required")

    # Rule 5: collection processed, no refs document lists the product.
    if refs_collection_lidvid is None:

        def version_mismatch(listed: str) -> Verdict:
            direction = _compare_versions(candidate.lidvid, listed)
            if direction > 0:
                advice = (
                    f"The registry holds a newer version than the inventory lists. Either the inventory is out of "
                    f"date or {candidate.lidvid} should not be loaded; the node decides which"
                )
            else:
                advice = f"Load {listed}"
            return verdict(
                Rule.INVENTORY_VERSION_MISMATCH,
                Severity.ANOMALOUS,
                f"The collection's inventory lists this product as {listed} but the registry holds "
                f"{candidate.lidvid}; {c_desc}. {advice}; re-harvesting the collection does not fix it.",
                collection,
            )

        # The collection's own refs already name another version of the product: no need to read the inventory.
        for listed, listed_collection in listed_in_refs:
            if listed != candidate.lidvid and listed_collection == collection.lidvid:
                return version_mismatch(listed)
        inventory = inventory_for(collection) if inventory_for is not None else None
        if inventory is not None and not inventory.lists(candidate.lidvid, candidate.lid):
            other = inventory.other_version(candidate.lid, candidate.lidvid)
            if other is not None:
                return version_mismatch(other)
        if p_age is None:
            pending = False
            age_text = "product harvest time unknown, treated as overdue"
        else:
            pending = p_age <= th.product_grace_days
            age_text = f"product harvested {_fmt_age(p_age)} days ago"
        if pending:
            return verdict(
                Rule.REFS_MISSING_PENDING,
                Severity.EXPECTED,
                f"No refs document lists the product but {c_desc}; {age_text}, within product grace "
                f"{th.product_grace_days:g} days.",
                collection,
            )
        if inventory is not None and candidate.lid in inventory.bare_lids and not inventory.lists_exactly(candidate.lidvid):
            return verdict(
                Rule.BARE_LID_IN_INVENTORY,
                Severity.ANOMALOUS,
                f"The collection's inventory lists this product by LID without a version, which the sweepers do not "
                f"follow, so no refs document names it; {c_desc}; {age_text}. Re-harvesting writes the same refs. "
                f"The inventory needs LIDVIDs, or the sweepers need to support LID references.",
                collection,
            )
        if inventory is not None and inventory.lists_exactly(candidate.lidvid):
            return verdict(
                Rule.REFS_MISSING,
                Severity.ANOMALOUS,
                f"The collection's inventory lists this product but no refs document does, so the refs predate "
                f"the inventory; {c_desc}; {age_text}. Re-harvest the collection to regenerate its refs.",
                collection,
            )
        if inventory is not None:
            return verdict(
                Rule.NOT_IN_COLLECTION_INVENTORY,
                Severity.ANOMALOUS,
                f"The collection's current inventory does not list this product under any version; {c_desc}; "
                f"{age_text}. Decide whether it belongs in the inventory or should be removed from the registry.",
                collection,
            )
        return replace(
            verdict(
                Rule.REFS_MISSING,
                Severity.ANOMALOUS,
                f"No refs document lists the product but {c_desc}; {age_text}, product grace "
                f"{th.product_grace_days:g} days. The collection inventory was not used, so the cause is unknown.",
                collection,
            ),
            inventory_verified=False,
        )

    # Rule 6: collection processed and refs list the product.
    c_when = f"collection harvested {_fmt_ts(collection.harvest)}, product harvested {_fmt_ts(candidate.harvest)}"
    if collection.harvest is None or candidate.harvest is None:
        unknown = "collection" if collection.harvest is None else "product"
        return verdict(
            Rule.SWEEPER_MISS,
            Severity.ANOMALOUS,
            f"Refs list the product and {c_desc}, but the {unknown} harvest time was unknown so the order "
            f"could not be compared; nothing explains the gap.",
            collection,
        )
    if _aware(collection.harvest) < _aware(candidate.harvest):
        return verdict(
            Rule.RELOADED_AFTER_COLLECTION,
            Severity.ANOMALOUS,
            f"Product was loaded or overwritten after the collection was processed ({c_when}); {c_desc}. "
            f"The sweepers never went back to it; EN's ancestry orphan repair fixes it.",
            collection,
        )
    return verdict(
        Rule.SWEEPER_MISS,
        Severity.ANOMALOUS,
        f"Refs list the product and {c_desc} and harvested no earlier than the product ({c_when}); "
        f"nothing explains the gap.",
        collection,
    )
