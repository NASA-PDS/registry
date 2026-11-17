"""Tests for ``unprocessed_audit.ownership`` (no network)."""

from __future__ import annotations

import pytest
from unprocessed_audit import ownership
from unprocessed_audit.model import Collection
from unprocessed_audit.model import CollectionState
from unprocessed_audit.model import Rule
from unprocessed_audit.ownership import Kind
from unprocessed_audit.ownership import Owner


def test_every_rule_has_a_problem_with_an_owner_and_a_plain_description():
    for rule in Rule:
        problem = ownership.RULE_PROBLEMS[rule]
        assert isinstance(problem.owner, Owner) and isinstance(problem.kind, Kind)
        assert problem.title and problem.action
        assert rule.value not in problem.title  # plain language, not rule names


@pytest.mark.parametrize(
    "rule, owner",
    [
        (Rule.COLLECTION_NOT_LOADED_OVERDUE, Owner.NODE),
        (Rule.INVENTORY_VERSION_MISMATCH, Owner.NODE),
        (Rule.NOT_IN_COLLECTION_INVENTORY, Owner.NODE),
        (Rule.RELOADED_AFTER_COLLECTION, Owner.NODE),
        (Rule.REFS_MISSING, Owner.NODE),
        (Rule.COLLECTION_OVERDUE, Owner.EN),
        (Rule.STALE_STAMP, Owner.NODE),
        (Rule.SWEEPER_MISS, Owner.SWEEPERS_TEAM),
        (Rule.BARE_LID_IN_INVENTORY, Owner.SWEEPERS_TEAM),
        (Rule.REFS_MISSING_PENDING, Owner.NO_ACTION),
        (Rule.COLLECTION_PENDING, Owner.NO_ACTION),
        (Rule.COLLECTION_NOT_LOADED_PENDING, Owner.NO_ACTION),
        (Rule.NO_PARENT_BY_DESIGN, Owner.NO_ACTION),
    ],
)
def test_owner_of_each_rule(rule, owner):
    assert ownership.owner_of(rule) is owner
    assert ownership.owner_of(rule.value) is owner  # accepts the string value too


def test_refs_missing_needs_a_closer_look_when_the_inventory_was_not_used():
    assert ownership.owner_of(Rule.REFS_MISSING, verified=False) is Owner.NEEDS_CHECK
    assert ownership.owner_of(Rule.INVENTORY_VERSION_MISMATCH, verified=False) is Owner.NODE


def test_orphaned_and_not_processed_kinds():
    orphaned = {Rule.COLLECTION_NOT_LOADED_OVERDUE, Rule.INVENTORY_VERSION_MISMATCH, Rule.NOT_IN_COLLECTION_INVENTORY,
                Rule.REFS_MISSING, Rule.BARE_LID_IN_INVENTORY}  # fmt: skip
    for rule in Rule:
        kind = ownership.RULE_PROBLEMS[rule].kind
        if rule in orphaned:
            assert kind is Kind.ORPHANED
        elif ownership.RULE_PROBLEMS[rule].owner is Owner.NO_ACTION:
            assert kind is Kind.WAITING
        else:
            assert kind is Kind.NOT_PROCESSED  # the refs confirm the parent; the sweepers did not process it


def test_count_by_owner_has_every_owner_and_sums_products():
    totals = ownership.count_by_owner(
        {"inventory_version_mismatch": 10, "not_in_collection_inventory": 5, "refs_missing": 3, "sweeper_miss": 1}
    )
    assert totals == {"node": 18, "en": 0, "sweepers_team": 1, "needs_check": 0, "no_action": 0}
    split = ownership.count_by_owner({"refs_missing": 5}, unverified_refs_missing=3)
    assert (split["needs_check"], split["node"]) == (3, 2)


def make_collection(state: CollectionState, bundles: list[str], superseded_by: str | None = None) -> Collection:
    return Collection(
        lidvid="urn:a:b:c::1.0", lid="urn:a:b:c", node="atm", stamp="7", ancestor_refs=[], harvest=None,
        state=state, bundle_lidvids=bundles, superseded_by=superseded_by,
    )  # fmt: skip


def test_empty_refs_collections_need_a_bundle_and_must_be_current():
    kept = make_collection(CollectionState.STAMPED_EMPTY_REFS, ["urn:a:b::1.0"])
    found = ownership.empty_refs_collections(
        [
            kept,
            make_collection(CollectionState.STAMPED_EMPTY_REFS, []),
            make_collection(CollectionState.STAMPED_EMPTY_REFS, ["urn:a:b::1.0"], superseded_by="urn:a:b:c::2.0"),
            make_collection(CollectionState.PROCESSED, ["urn:a:b::1.0"]),
        ]
    )
    assert found == [kept]


def test_collections_per_rule_counts_each_collection_once_per_rule():
    totals = ownership.collections_per_rule(
        [{"refs_missing": 4, "stale_stamp": 0}, {"refs_missing": 1}, {"sweeper_miss": 2}]
    )
    assert totals == {"refs_missing": 2, "sweeper_miss": 1}


def test_rows_are_ordered_by_owner_then_size_and_include_the_empty_refs_row():
    rows = ownership.build_rows(
        anomalous_counts={"sweeper_miss": 2, "refs_missing": 5, "inventory_version_mismatch": 100, "stale_stamp": 7},
        expected_counts={"refs_missing_pending": 9},
        collections_per_rule={"inventory_version_mismatch": 3, "refs_missing": 2},
        empty_refs_count=4,
    )
    assert [(r.owner, r.rule) for r in rows] == [
        (Owner.NODE, Rule.INVENTORY_VERSION_MISMATCH),
        (Owner.NODE, Rule.STALE_STAMP),
        (Owner.NODE, Rule.REFS_MISSING),
        (Owner.NODE, None),
        (Owner.SWEEPERS_TEAM, Rule.SWEEPER_MISS),
        (Owner.NO_ACTION, Rule.REFS_MISSING_PENDING),
    ]
    assert rows[0].collections == 3 and rows[0].products == 100
    assert rows[3].products is None and rows[3].collections == 4


def test_unverified_refs_missing_gets_its_own_row_apart_from_the_verified_ones():
    rows = ownership.build_rows({"refs_missing": 5}, {}, {"refs_missing": 2}, 0, unverified_refs_missing=3)
    assert [(r.owner, r.products) for r in rows] == [(Owner.NODE, 2), (Owner.NEEDS_CHECK, 3)]
    only_unverified = ownership.build_rows({"refs_missing": 3}, {}, {}, 0, unverified_refs_missing=3)
    assert [(r.owner, r.products) for r in only_unverified] == [(Owner.NEEDS_CHECK, 3)]


def test_rows_skip_zero_counts():
    assert ownership.build_rows({"refs_missing": 0}, {"collection_pending": 0}, {}, 0) == []


def test_verdict_names_the_owners_that_have_work_and_ignores_waiting():
    rows = ownership.build_rows(
        {"inventory_version_mismatch": 1200, "collection_overdue": 30}, {"refs_missing_pending": 9}, {}, 0
    )
    assert ownership.verdict(rows) == "Needs attention: 1,200 products for the node; 30 products for EN."
    assert ownership.verdict(ownership.build_rows({}, {"refs_missing_pending": 9}, {}, 0)) == (
        "Healthy: nothing needs doing."
    )
    assert ownership.verdict([]) == "Healthy: nothing needs doing."


def test_verdict_counts_products_and_collections_apart():
    rows = ownership.build_rows({"reloaded_after_collection": 36323}, {}, {"reloaded_after_collection": 5}, 6)
    assert ownership.verdict(rows) == "Needs attention: 36,323 products and 6 collections for the node."
    only_collections = ownership.build_rows({}, {}, {}, 2)
    assert ownership.verdict(only_collections) == "Needs attention: 2 collections for the node."
