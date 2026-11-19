"""Tests for ``unprocessed_audit.classify``."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from unprocessed_audit.classify import age_days
from unprocessed_audit.classify import classify_collection
from unprocessed_audit.classify import classify_product
from unprocessed_audit.classify import derive_bundle_lid
from unprocessed_audit.classify import derive_collection_lid
from unprocessed_audit.classify import is_member_class
from unprocessed_audit.classify import needs_refs_lookup
from unprocessed_audit.classify import parse_timestamp
from unprocessed_audit.classify import population_of
from unprocessed_audit.classify import resolve_collection
from unprocessed_audit.classify import RULE_GUIDANCE
from unprocessed_audit.inventory import InventoryIndex
from unprocessed_audit.inventory import parse_inventory
from unprocessed_audit.model import Candidate
from unprocessed_audit.model import Collection
from unprocessed_audit.model import CollectionState
from unprocessed_audit.model import Population
from unprocessed_audit.model import Rule
from unprocessed_audit.model import Severity
from unprocessed_audit.model import Thresholds

NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
TH = Thresholds(now=NOW, collection_grace_days=1.0, product_grace_days=7.0, ancestry_version=7)

COLL_LID = "urn:nasa:pds:bun:col"
COLL_LIDVID = COLL_LID + "::1.0"
PROD_LID = COLL_LID + ":prod1"
PROD_LIDVID = PROD_LID + "::1.0"


def days_ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


def make_collection(
    state: CollectionState | None,
    harvest: datetime | None = None,
    lidvid: str = COLL_LIDVID,
) -> Collection:
    return Collection(
        lidvid=lidvid,
        lid=lidvid.split("::")[0],
        node="atm",
        stamp="7",
        ancestor_refs=["urn:nasa:pds:bun::1.0"],
        harvest=harvest,
        state=state,
    )


def make_candidate(
    harvest: datetime | None = None,
    stamp: str | None = None,
    has_refs: bool = False,
    product_class: str = "Product_Observational",
    lid: str = PROD_LID,
) -> Candidate:
    return Candidate(
        lidvid=lid + "::1.0",
        lid=lid,
        product_class=product_class,
        node="atm",
        stamp=stamp,
        has_ancestor_refs=has_refs,
        harvest=harvest,
    )


def by_lid(*collections: Collection) -> dict[str, list[Collection]]:
    result: dict[str, list[Collection]] = {}
    for collection in collections:
        result.setdefault(collection.lid, []).append(collection)
    return result


# ── parsing helpers ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value, expected",
    [
        ("2026-01-02T03:04:05Z", datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)),
        ("2026-01-02T03:04:05.250Z", datetime(2026, 1, 2, 3, 4, 5, 250000, tzinfo=timezone.utc)),
        ("2026-01-02T03:04:05+00:00", datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)),
        ("2026-01-02T03:04:05", datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)),
        ("2026-01-02T05:04:05+02:00", datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)),
        ("2026-01-02", datetime(2026, 1, 2, tzinfo=timezone.utc)),
    ],
)
def test_parse_timestamp_valid(value: str, expected: datetime) -> None:
    parsed = parse_timestamp(value)
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed == expected


@pytest.mark.parametrize("value", [None, "", "   ", "not a date", "2026-13-45T00:00:00Z"])
def test_parse_timestamp_invalid(value: str | None) -> None:
    assert parse_timestamp(value) is None


def test_age_days() -> None:
    assert age_days(None, NOW) is None
    assert age_days(days_ago(2.5), NOW) == pytest.approx(2.5)
    assert age_days(NOW + timedelta(days=1), NOW) == pytest.approx(-1.0)


def test_age_days_naive_is_utc() -> None:
    naive = datetime(2026, 6, 14, 12, 0, 0)
    assert age_days(naive, NOW) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "lid, collection, bundle",
    [
        ("urn:nasa:pds:bun:col:prod", "urn:nasa:pds:bun:col", "urn:nasa:pds:bun"),
        ("urn:nasa:pds:bun:col:prod:extra", "urn:nasa:pds:bun:col", "urn:nasa:pds:bun"),
        ("urn:nasa:pds:bun:col", None, "urn:nasa:pds:bun"),
        ("urn:nasa:pds:bun", None, None),
        ("garbage", None, None),
        ("", None, None),
        ("urn:nasa:pds::col:prod", None, None),
    ],
)
def test_derive_lids(lid: str, collection: str | None, bundle: str | None) -> None:
    assert derive_collection_lid(lid) == collection
    assert derive_bundle_lid(lid) == bundle


def test_is_member_class() -> None:
    assert is_member_class("Product_Observational")
    assert not is_member_class("Product_Service")
    assert not is_member_class("Product_Context")


# ── population and collection state ───────────────────────────────────────────


@pytest.mark.parametrize(
    "stamp, has_refs, expected",
    [
        (None, False, Population.NO_STAMP),
        (None, True, Population.NO_STAMP),
        ("6", True, Population.STALE_STAMP),
        ("6", False, Population.STALE_STAMP),
        ("8", True, Population.STALE_STAMP),
        ("abc", True, Population.STALE_STAMP),
        ("", False, Population.STALE_STAMP),
        ("7", False, Population.EMPTY_REFS),
        ("7", True, None),
    ],
)
def test_population_of(stamp: str | None, has_refs: bool, expected: Population | None) -> None:
    assert population_of(stamp, has_refs, 7) == expected


def _coll(stamp: str | None, refs: list[str], harvest: datetime | None) -> Collection:
    return Collection(COLL_LIDVID, COLL_LID, "atm", stamp, refs, harvest)


@pytest.mark.parametrize(
    "stamp, refs, harvest, expected",
    [
        ("7", ["b"], days_ago(30), CollectionState.PROCESSED),
        ("7", [], days_ago(30), CollectionState.STAMPED_EMPTY_REFS),
        ("7", [], None, CollectionState.STAMPED_EMPTY_REFS),
        (None, [], days_ago(0.5), CollectionState.UNPROCESSED_PENDING),
        ("6", ["b"], days_ago(0.5), CollectionState.UNPROCESSED_PENDING),
        (None, [], days_ago(1.0), CollectionState.UNPROCESSED_PENDING),
        (None, [], days_ago(1.01), CollectionState.UNPROCESSED_OVERDUE),
        ("6", [], days_ago(40), CollectionState.UNPROCESSED_OVERDUE),
        (None, [], None, CollectionState.UNPROCESSED_OVERDUE),
    ],
)
def test_classify_collection(
    stamp: str | None, refs: list[str], harvest: datetime | None, expected: CollectionState
) -> None:
    assert classify_collection(_coll(stamp, refs, harvest), TH) == expected


# ── resolve_collection ────────────────────────────────────────────────────────


def test_resolve_collection_none_cases() -> None:
    assert resolve_collection(None, None, {}) is None
    assert resolve_collection(COLL_LID, None, {}) is None


def test_resolve_collection_single_version() -> None:
    col = make_collection(CollectionState.PROCESSED)
    assert resolve_collection(COLL_LID, None, by_lid(col)) is col


def test_resolve_collection_refs_exact_version() -> None:
    v1 = make_collection(CollectionState.PROCESSED, days_ago(10), COLL_LID + "::1.0")
    v2 = make_collection(CollectionState.UNPROCESSED_OVERDUE, days_ago(5), COLL_LID + "::2.0")
    cols = by_lid(v1, v2)
    assert resolve_collection(COLL_LID, COLL_LID + "::1.0", cols) is v1
    assert resolve_collection(None, COLL_LID + "::2.0", cols) is v2
    assert resolve_collection(COLL_LID, COLL_LID + "::3.0", cols) is None
    assert resolve_collection(COLL_LID, "urn:nasa:pds:bun:other::1.0", cols) is None


def test_resolve_collection_all_processed_picks_latest_harvest() -> None:
    old = make_collection(CollectionState.PROCESSED, days_ago(10), COLL_LID + "::1.0")
    new = make_collection(CollectionState.STAMPED_EMPTY_REFS, days_ago(3), COLL_LID + "::2.0")
    unknown = make_collection(CollectionState.PROCESSED, None, COLL_LID + "::0.5")
    assert resolve_collection(COLL_LID, None, by_lid(old, unknown, new)) is new
    assert resolve_collection(COLL_LID, None, by_lid(unknown, old)) is old


def test_resolve_collection_worst_state_wins() -> None:
    processed = make_collection(CollectionState.PROCESSED, days_ago(1), COLL_LID + "::1.0")
    pending = make_collection(CollectionState.UNPROCESSED_PENDING, days_ago(0.5), COLL_LID + "::2.0")
    overdue = make_collection(CollectionState.UNPROCESSED_OVERDUE, days_ago(9), COLL_LID + "::3.0")
    assert resolve_collection(COLL_LID, None, by_lid(processed, pending)) is pending
    assert resolve_collection(COLL_LID, None, by_lid(processed, pending, overdue)) is overdue


# ── needs_refs_lookup ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "state, product_class, stamp, lid, expected",
    [
        (CollectionState.PROCESSED, "Product_Observational", None, PROD_LID, True),
        (CollectionState.STAMPED_EMPTY_REFS, "Product_Observational", "7", PROD_LID, True),
        (CollectionState.PROCESSED, "Product_Observational", "6", PROD_LID, False),
        (CollectionState.PROCESSED, "Product_Service", None, PROD_LID, False),
        (CollectionState.UNPROCESSED_PENDING, "Product_Observational", None, PROD_LID, False),
        (CollectionState.UNPROCESSED_OVERDUE, "Product_Observational", None, PROD_LID, False),
        (None, "Product_Observational", None, "urn:nasa:pds:bun:other:prod", False),
        (None, "Product_Observational", None, "urn:nasa:pds", False),
    ],
)
def test_needs_refs_lookup(
    state: CollectionState | None, product_class: str, stamp: str | None, lid: str, expected: bool
) -> None:
    cols = by_lid(make_collection(state)) if state is not None else {}
    candidate = make_candidate(days_ago(2), stamp=stamp, product_class=product_class, lid=lid)
    assert needs_refs_lookup(candidate, TH, cols) is expected


def test_needs_refs_lookup_fully_processed_candidate() -> None:
    cols = by_lid(make_collection(CollectionState.PROCESSED))
    assert not needs_refs_lookup(make_candidate(stamp="7", has_refs=True), TH, cols)


# ── classify_product: one case per rule ───────────────────────────────────────


def test_rule_no_parent_by_design() -> None:
    cand = make_candidate(days_ago(100), product_class="Product_Service", lid="urn:nasa:pds:svc")
    v = classify_product(cand, TH, {})
    assert v.rule == Rule.NO_PARENT_BY_DESIGN
    assert v.severity == Severity.EXPECTED
    assert v.population == Population.NO_STAMP
    assert v.collection_lidvid is None
    assert v.in_refs is None


def test_rule_collection_not_loaded_pending() -> None:
    v = classify_product(make_candidate(days_ago(2)), TH, {})
    assert v.rule == Rule.COLLECTION_NOT_LOADED_PENDING
    assert v.severity == Severity.EXPECTED
    assert v.bundle_lid == "urn:nasa:pds:bun"
    assert "2.0" in v.rationale


def test_rule_collection_not_loaded_overdue() -> None:
    v = classify_product(make_candidate(days_ago(20)), TH, {})
    assert v.rule == Rule.COLLECTION_NOT_LOADED_OVERDUE
    assert v.severity == Severity.ANOMALOUS
    assert "20.0" in v.rationale


def test_collection_not_loaded_grace_boundary() -> None:
    assert classify_product(make_candidate(days_ago(7.0)), TH, {}).rule == Rule.COLLECTION_NOT_LOADED_PENDING
    assert classify_product(make_candidate(days_ago(7.01)), TH, {}).rule == Rule.COLLECTION_NOT_LOADED_OVERDUE


def test_collection_not_loaded_unknown_harvest() -> None:
    v = classify_product(make_candidate(None), TH, {})
    assert v.rule == Rule.COLLECTION_NOT_LOADED_OVERDUE
    assert v.severity == Severity.ANOMALOUS
    assert "unknown" in v.rationale


def test_collection_not_loaded_unparseable_lid() -> None:
    v = classify_product(make_candidate(days_ago(1), lid="garbage"), TH, {})
    assert v.rule == Rule.COLLECTION_NOT_LOADED_PENDING
    assert "cannot be parsed" in v.rationale
    assert v.bundle_lid is None
    v = classify_product(make_candidate(days_ago(30), lid="garbage"), TH, {})
    assert v.rule == Rule.COLLECTION_NOT_LOADED_OVERDUE


def test_collection_listed_in_refs_but_not_loaded() -> None:
    v = classify_product(
        make_candidate(days_ago(30), stamp="7"),
        TH,
        {},
        refs_collection_lidvid=COLL_LID + "::9.0",
        refs_checked=True,
    )
    assert v.rule == Rule.COLLECTION_NOT_LOADED_OVERDUE
    assert v.collection_lidvid == COLL_LID + "::9.0"
    assert v.in_refs is True


def test_rule_collection_pending() -> None:
    col = make_collection(CollectionState.UNPROCESSED_PENDING, days_ago(0.5))
    v = classify_product(make_candidate(days_ago(50)), TH, by_lid(col))
    assert v.rule == Rule.COLLECTION_PENDING
    assert v.severity == Severity.EXPECTED
    assert v.collection_lidvid == COLL_LIDVID
    assert v.collection_state == CollectionState.UNPROCESSED_PENDING
    assert v.collection_harvest == col.harvest
    assert v.in_refs is None


def test_rule_collection_overdue() -> None:
    col = make_collection(CollectionState.UNPROCESSED_OVERDUE, days_ago(9))
    v = classify_product(make_candidate(days_ago(1)), TH, by_lid(col))
    assert v.rule == Rule.COLLECTION_OVERDUE
    assert v.severity == Severity.ANOMALOUS
    assert "9.0" in v.rationale
    assert COLL_LIDVID in v.rationale


def test_collection_overdue_unknown_harvest() -> None:
    col = make_collection(CollectionState.UNPROCESSED_OVERDUE, None)
    v = classify_product(make_candidate(days_ago(1)), TH, by_lid(col))
    assert v.rule == Rule.COLLECTION_OVERDUE
    assert "unknown" in v.rationale


def test_rule_stale_stamp() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(10))
    v = classify_product(make_candidate(days_ago(30), stamp="6", has_refs=True), TH, by_lid(col))
    assert v.rule == Rule.STALE_STAMP
    assert v.severity == Severity.ANOMALOUS
    assert v.population == Population.STALE_STAMP
    assert v.in_refs is None


def test_stale_stamp_with_stamped_empty_collection() -> None:
    col = make_collection(CollectionState.STAMPED_EMPTY_REFS, days_ago(10))
    v = classify_product(make_candidate(days_ago(30), stamp="abc"), TH, by_lid(col))
    assert v.rule == Rule.STALE_STAMP


def test_stale_stamp_with_refs_checked_records_in_refs() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(10))
    v = classify_product(make_candidate(days_ago(30), stamp="6"), TH, by_lid(col), COLL_LIDVID, True)
    assert v.rule == Rule.STALE_STAMP
    assert v.in_refs is True


def test_stale_stamp_in_pending_collection_is_collection_rule() -> None:
    col = make_collection(CollectionState.UNPROCESSED_PENDING, days_ago(0.2))
    v = classify_product(make_candidate(days_ago(30), stamp="6"), TH, by_lid(col))
    assert v.rule == Rule.COLLECTION_PENDING


def test_rule_refs_missing_anomalous() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    v = classify_product(make_candidate(days_ago(8)), TH, by_lid(col), None, True)
    assert v.rule == Rule.REFS_MISSING
    assert v.severity == Severity.ANOMALOUS
    assert v.in_refs is False
    assert v.collection_lidvid == COLL_LIDVID
    assert v.collection_state == CollectionState.PROCESSED


def inventory_listing(*lidvids: str) -> InventoryIndex:
    return parse_inventory([f"P,{lidvid}" for lidvid in lidvids])


def test_inventory_lists_the_product_means_the_refs_are_stale() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    inv = inventory_listing(candidate.lidvid)
    v = classify_product(candidate, TH, by_lid(col), None, True, inventory_for=lambda collection: inv)
    assert v.rule == Rule.REFS_MISSING
    assert "refs predate the inventory" in v.rationale
    assert "Re-harvest the collection" in v.rationale


def test_inventory_without_the_product_under_any_version() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    inv = inventory_listing("urn:nasa:pds:bun:col:other::1.0")
    v = classify_product(candidate, TH, by_lid(col), None, True, inventory_for=lambda collection: inv)
    assert v.rule == Rule.NOT_IN_COLLECTION_INVENTORY
    assert v.severity == Severity.ANOMALOUS
    assert v.in_refs is False
    assert v.collection_lidvid == COLL_LIDVID
    assert "does not list this product under any version" in v.rationale


def test_inventory_listing_another_version_is_a_version_mismatch() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    inv = inventory_listing(candidate.lid + "::2.0")
    v = classify_product(candidate, TH, by_lid(col), None, True, inventory_for=lambda collection: inv)
    assert v.rule == Rule.INVENTORY_VERSION_MISMATCH
    assert candidate.lid + "::2.0" in v.rationale


def test_a_recent_product_missing_from_the_inventory_is_still_pending() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(2))
    inv = inventory_listing("urn:nasa:pds:bun:col:other::1.0")
    v = classify_product(candidate, TH, by_lid(col), None, True, inventory_for=lambda collection: inv)
    assert v.rule == Rule.REFS_MISSING_PENDING
    assert v.severity == Severity.EXPECTED


def test_unavailable_inventory_falls_back_to_refs_missing() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    v = classify_product(candidate, TH, by_lid(col), None, True, inventory_for=lambda collection: None)
    assert v.rule == Rule.REFS_MISSING
    assert "refs predate" not in v.rationale


def test_inventory_is_not_downloaded_when_the_refs_already_name_another_version() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    calls: list[str] = []

    def provider(collection: Collection) -> InventoryIndex | None:
        calls.append(collection.lidvid)
        return None

    v = classify_product(candidate, TH, by_lid(col), None, True, [(candidate.lid + "::2.0", COLL_LIDVID)], provider)
    assert v.rule == Rule.INVENTORY_VERSION_MISMATCH
    assert calls == []


def test_inventory_is_not_consulted_when_a_refs_document_lists_the_product() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(10))
    candidate = make_candidate(days_ago(2))
    calls: list[str] = []

    def provider(collection: Collection) -> InventoryIndex | None:
        calls.append(collection.lidvid)
        return None

    v = classify_product(candidate, TH, by_lid(col), COLL_LIDVID, True, inventory_for=provider)
    assert v.rule == Rule.RELOADED_AFTER_COLLECTION
    assert calls == []


def test_rule_inventory_version_mismatch() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    listed = candidate.lid + "::2.0"
    v = classify_product(candidate, TH, by_lid(col), None, True, [(listed, COLL_LIDVID)])
    assert v.rule == Rule.INVENTORY_VERSION_MISMATCH
    assert v.severity == Severity.ANOMALOUS
    assert v.in_refs is False
    assert v.collection_lidvid == COLL_LIDVID
    assert listed in v.rationale
    assert candidate.lidvid in v.rationale
    assert "does not fix it" in v.rationale


def test_inventory_version_mismatch_applies_inside_the_product_grace_period() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(1))
    v = classify_product(candidate, TH, by_lid(col), None, True, [(candidate.lid + "::2.0", COLL_LIDVID)])
    assert v.rule == Rule.INVENTORY_VERSION_MISMATCH


def test_listed_lidvid_equal_to_the_candidate_does_not_make_a_mismatch() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    v = classify_product(candidate, TH, by_lid(col), None, True, [(candidate.lidvid, COLL_LIDVID)])
    assert v.rule == Rule.REFS_MISSING


def test_listed_lidvid_is_ignored_when_a_refs_document_lists_the_product() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(10))
    candidate = make_candidate(days_ago(2))
    v = classify_product(candidate, TH, by_lid(col), COLL_LIDVID, True, [(candidate.lid + "::2.0", COLL_LIDVID)])
    assert v.rule == Rule.RELOADED_AFTER_COLLECTION


def test_a_listing_from_another_collection_version_is_not_a_version_mismatch() -> None:
    # Refs of an older collection version name an older product version; the current collection version has no
    # refs at all and its inventory lists the exact product, so the refs are missing, not the product version.
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    other_collection = COLL_LID + "::0.5"
    v = classify_product(
        candidate, TH, by_lid(col), None, True, [(candidate.lid + "::0.5", other_collection)],
        inventory_for=lambda c: InventoryIndex(lidvids={candidate.lidvid}, listed_by_lid={candidate.lid: candidate.lidvid}),
    )  # fmt: skip
    assert v.rule == Rule.REFS_MISSING
    assert v.inventory_verified is True
    assert "inventory lists this product" in v.rationale


def test_refs_missing_without_the_inventory_is_marked_unverified() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    v = classify_product(candidate, TH, by_lid(col), None, True)
    assert v.rule == Rule.REFS_MISSING
    assert v.inventory_verified is False
    assert "inventory was not used" in v.rationale


def make_superseded(version: str, harvest: datetime | None = None) -> Collection:
    col = make_collection(CollectionState.PROCESSED, harvest or days_ago(400), lidvid=f"{COLL_LID}::{version}")
    col.superseded_by = f"{COLL_LID}::3.0"
    return col


def test_resolve_prefers_the_collection_version_matching_the_product_version() -> None:
    old = make_superseded("2.1")
    current = make_collection(CollectionState.PROCESSED, days_ago(1), lidvid=f"{COLL_LID}::3.0")
    found = resolve_collection(COLL_LID, None, by_lid(old, current), f"{PROD_LID}::2.1")
    assert found is old


def test_resolve_prefers_current_versions_when_no_version_matches() -> None:
    old = make_superseded("2.1")
    current = make_collection(CollectionState.PROCESSED, days_ago(1), lidvid=f"{COLL_LID}::3.0")
    assert resolve_collection(COLL_LID, None, by_lid(old, current), f"{PROD_LID}::9.9") is current
    assert resolve_collection(COLL_LID, None, by_lid(old, current)) is current


def test_resolve_falls_back_to_superseded_versions_when_none_is_current() -> None:
    older = make_superseded("1.0", days_ago(500))
    newer = make_superseded("2.0", days_ago(300))
    assert resolve_collection(COLL_LID, None, by_lid(older, newer), f"{PROD_LID}::9.9") is newer


def test_refs_resolve_to_a_superseded_collection_exactly() -> None:
    old = make_superseded("2.1")
    current = make_collection(CollectionState.PROCESSED, days_ago(1), lidvid=f"{COLL_LID}::3.0")
    assert resolve_collection(COLL_LID, old.lidvid, by_lid(old, current), f"{PROD_LID}::9.9") is old


def test_product_of_a_superseded_collection_is_reported_against_it() -> None:
    from dataclasses import replace

    old = make_superseded("2.1")
    current = make_collection(CollectionState.PROCESSED, days_ago(1), lidvid=f"{COLL_LID}::3.0")
    candidate = replace(make_candidate(days_ago(20)), lidvid=f"{PROD_LID}::2.1")
    assert needs_refs_lookup(candidate, TH, by_lid(old, current))
    v = classify_product(candidate, TH, by_lid(old, current), None, True)
    assert v.rule == Rule.REFS_MISSING
    assert v.collection_lidvid == old.lidvid
    assert f"superseded by {COLL_LID}::3.0" in v.rationale


def test_rule_refs_missing_pending_and_boundary() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    v = classify_product(make_candidate(days_ago(7.0)), TH, by_lid(col), None, True)
    assert v.rule == Rule.REFS_MISSING_PENDING
    assert v.severity == Severity.EXPECTED
    v = classify_product(make_candidate(days_ago(7.01)), TH, by_lid(col), None, True)
    assert v.rule == Rule.REFS_MISSING


def test_refs_missing_unknown_harvest_is_overdue() -> None:
    col = make_collection(CollectionState.STAMPED_EMPTY_REFS, days_ago(30))
    v = classify_product(make_candidate(None), TH, by_lid(col), None, True)
    assert v.rule == Rule.REFS_MISSING
    assert "unknown" in v.rationale


def test_rule_reloaded_after_collection() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(10))
    v = classify_product(make_candidate(days_ago(2)), TH, by_lid(col), COLL_LIDVID, True)
    assert v.rule == Rule.RELOADED_AFTER_COLLECTION
    assert v.severity == Severity.ANOMALOUS
    assert v.in_refs is True
    assert "loaded or overwritten after the collection was processed" in v.rationale
    assert "EN's ancestry orphan repair" in v.rationale
    assert "re-harvest" not in v.rationale


def test_rule_sweeper_miss() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(2))
    v = classify_product(make_candidate(days_ago(10)), TH, by_lid(col), COLL_LIDVID, True)
    assert v.rule == Rule.SWEEPER_MISS
    assert v.severity == Severity.ANOMALOUS
    assert v.in_refs is True
    assert "nothing explains the gap" in v.rationale


def test_equal_harvest_is_sweeper_miss() -> None:
    harvest = days_ago(5)
    col = make_collection(CollectionState.PROCESSED, harvest)
    v = classify_product(make_candidate(harvest), TH, by_lid(col), COLL_LIDVID, True)
    assert v.rule == Rule.SWEEPER_MISS


def test_collection_strictly_earlier_is_reloaded() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(5))
    v = classify_product(make_candidate(days_ago(5) + timedelta(seconds=1)), TH, by_lid(col), COLL_LIDVID, True)
    assert v.rule == Rule.RELOADED_AFTER_COLLECTION


@pytest.mark.parametrize("coll_harvest, prod_harvest, which", [(None, days_ago(3), "collection"), (days_ago(3), None, "product")])
def test_unknown_harvest_is_sweeper_miss(
    coll_harvest: datetime | None, prod_harvest: datetime | None, which: str
) -> None:
    col = make_collection(CollectionState.PROCESSED, coll_harvest)
    v = classify_product(make_candidate(prod_harvest), TH, by_lid(col), COLL_LIDVID, True)
    assert v.rule == Rule.SWEEPER_MISS
    assert f"{which} harvest time was unknown" in v.rationale


def test_refs_collection_lidvid_selects_exact_version() -> None:
    v1 = make_collection(CollectionState.PROCESSED, days_ago(20), COLL_LID + "::1.0")
    v2 = make_collection(CollectionState.UNPROCESSED_OVERDUE, days_ago(9), COLL_LID + "::2.0")
    cand = make_candidate(days_ago(2), stamp="7")
    v = classify_product(cand, TH, by_lid(v1, v2), COLL_LID + "::1.0", True)
    assert v.rule == Rule.RELOADED_AFTER_COLLECTION
    assert v.collection_lidvid == COLL_LID + "::1.0"
    v = classify_product(cand, TH, by_lid(v1, v2), COLL_LID + "::2.0", True)
    assert v.rule == Rule.COLLECTION_OVERDUE
    assert v.collection_lidvid == COLL_LID + "::2.0"


def test_refs_not_used_when_not_checked() -> None:
    col = make_collection(CollectionState.UNPROCESSED_OVERDUE, days_ago(9))
    v = classify_product(make_candidate(days_ago(2)), TH, by_lid(col), "urn:nasa:pds:bun:zzz::1.0", False)
    assert v.rule == Rule.COLLECTION_OVERDUE
    assert v.collection_lidvid == COLL_LIDVID


# ── error paths ───────────────────────────────────────────────────────────────


def test_fully_processed_candidate_raises() -> None:
    with pytest.raises(ValueError, match="fully processed"):
        classify_product(make_candidate(days_ago(1), stamp="7", has_refs=True), TH, {})


@pytest.mark.parametrize("state", [CollectionState.PROCESSED, CollectionState.STAMPED_EMPTY_REFS])
def test_refs_lookup_required_raises(state: CollectionState) -> None:
    col = make_collection(state, days_ago(10))
    with pytest.raises(ValueError, match="refs lookup required"):
        classify_product(make_candidate(days_ago(2)), TH, by_lid(col))


# ── guidance ──────────────────────────────────────────────────────────────────


def test_rule_guidance_covers_every_rule_in_ascii() -> None:
    assert set(RULE_GUIDANCE) == set(Rule)
    for text in RULE_GUIDANCE.values():
        assert text
        assert text.isascii()
    assert "ancestry orphan repair" in RULE_GUIDANCE[Rule.RELOADED_AFTER_COLLECTION]
    assert "ancestry orphan repair" in RULE_GUIDANCE[Rule.STALE_STAMP]


def test_rationales_are_single_line_ascii() -> None:
    col_ok = make_collection(CollectionState.PROCESSED, days_ago(10))
    verdicts = [
        classify_product(make_candidate(days_ago(2)), TH, by_lid(col_ok), COLL_LIDVID, True),
        classify_product(make_candidate(days_ago(20), stamp="6"), TH, by_lid(col_ok)),
        classify_product(make_candidate(None, lid="garbage"), TH, {}),
    ]
    for v in verdicts:
        assert v.rationale.isascii()
        assert "\n" not in v.rationale


def test_a_registry_version_newer_than_the_inventory_lists_is_not_told_to_load_the_listed_one() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))  # registered ::1.0
    older = [(candidate.lid + "::0.9", COLL_LIDVID)]
    v = classify_product(candidate, TH, by_lid(col), None, True, older)
    assert v.rule == Rule.INVENTORY_VERSION_MISMATCH
    assert "newer version than the inventory lists" in v.rationale
    assert "Load " not in v.rationale
    newer = [(candidate.lid + "::2.0", COLL_LIDVID)]
    assert "Load " + candidate.lid + "::2.0" in classify_product(candidate, TH, by_lid(col), None, True, newer).rationale


def test_an_inventory_that_lists_the_product_by_lid_only_is_not_stale_refs() -> None:
    # Harvest records a bare LID as product_lid; the sweepers follow product_lidvid only, so re-harvesting cannot help.
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    inventory = InventoryIndex(lidvids=set(), listed_by_lid={}, bare_lids={candidate.lid})
    v = classify_product(candidate, TH, by_lid(col), None, True, inventory_for=lambda c: inventory)
    assert v.rule == Rule.BARE_LID_IN_INVENTORY
    assert v.severity == Severity.ANOMALOUS
    assert "without a version" in v.rationale
    assert v.inventory_verified is True


def test_a_lidvid_listing_wins_over_a_bare_lid_listing() -> None:
    col = make_collection(CollectionState.PROCESSED, days_ago(30))
    candidate = make_candidate(days_ago(20))
    inventory = InventoryIndex(lidvids={candidate.lidvid}, listed_by_lid={candidate.lid: candidate.lidvid}, bare_lids={candidate.lid})
    v = classify_product(candidate, TH, by_lid(col), None, True, inventory_for=lambda c: inventory)
    assert v.rule == Rule.REFS_MISSING
