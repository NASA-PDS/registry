"""Tests for the unprocessed audit report writers, tally, diff and summary rendering."""

from __future__ import annotations

import csv
import gzip
from dataclasses import replace
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path

import pytest
from unprocessed_audit.model import Candidate
from unprocessed_audit.model import Collection
from unprocessed_audit.model import CollectionState
from unprocessed_audit.model import Population
from unprocessed_audit.model import RefsCoverage
from unprocessed_audit.model import Rule
from unprocessed_audit.model import Severity
from unprocessed_audit.model import Thresholds
from unprocessed_audit.model import Verdict
from unprocessed_audit.report import PRODUCT_COLUMNS
from unprocessed_audit.report import DiffCounts
from unprocessed_audit.report import ProductCsvWriter
from unprocessed_audit.report import Tally
from unprocessed_audit.report import age_bucket
from unprocessed_audit.report import compute_diff
from unprocessed_audit.report import coverage_note
from unprocessed_audit.report import load_previous_keys
from unprocessed_audit.report import record_key
from unprocessed_audit.report import render_summary
from unprocessed_audit.report import write_anomalous_collections
from unprocessed_audit.report import write_collections_csv

NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
TH = Thresholds(now=NOW)
COLL_LID = "urn:nasa:pds:bundle1:data"
COLL = COLL_LID + "::1.0"


def make_candidate(
    suffix: str = "p1",
    node: str = "atm",
    harvest_days_ago: float | None = 3.0,
    product_class: str = "Product_Observational",
    stamp: str | None = None,
) -> Candidate:
    lid = f"{COLL_LID}:{suffix}"
    harvest = None if harvest_days_ago is None else NOW - timedelta(days=harvest_days_ago)
    return Candidate(
        lidvid=lid + "::1.0",
        lid=lid,
        product_class=product_class,
        node=node,
        stamp=stamp,
        has_ancestor_refs=False,
        harvest=harvest,
    )


def make_verdict(
    rule: Rule = Rule.SWEEPER_MISS,
    severity: Severity = Severity.ANOMALOUS,
    collection_lidvid: str | None = COLL,
    in_refs: bool | None = True,
    state: CollectionState | None = CollectionState.PROCESSED,
) -> Verdict:
    return Verdict(
        population=Population.NO_STAMP,
        rule=rule,
        severity=severity,
        rationale="because, reasons",
        bundle_lid="urn:nasa:pds:bundle1",
        collection_lidvid=collection_lidvid,
        collection_state=state,
        collection_harvest=NOW - timedelta(days=10),
        in_refs=in_refs,
    )


def make_collection(
    lidvid: str = COLL,
    state: CollectionState = CollectionState.PROCESSED,
    node: str = "atm",
    bundles: list[str] | None = None,
    refs: list[str] | None = None,
) -> Collection:
    return Collection(
        lidvid=lidvid,
        lid=lidvid.split("::")[0],
        node=node,
        stamp="7",
        ancestor_refs=refs or [],
        harvest=NOW - timedelta(days=10),
        state=state,
        bundle_lidvids=bundles or [],
    )


# ── products CSV ──────────────────────────────────────────────────────────────


def test_product_csv_columns_and_row(tmp_path: Path) -> None:
    path = tmp_path / "unprocessed_products.csv"
    with ProductCsvWriter(path) as writer:
        writer.write(make_candidate(), make_verdict(), NOW)
        writer.write(
            make_candidate("p2", harvest_days_ago=None),
            make_verdict(Rule.COLLECTION_PENDING, Severity.EXPECTED, None, None, None),
            NOW,
        )
    assert writer.rows_written == 2
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys()) == PRODUCT_COLUMNS
    first = rows[0]
    assert first["node"] == "atm"
    assert first["lidvid"] == f"{COLL_LID}:p1::1.0"
    assert first["population"] == "A"
    assert first["has_ancestor_refs"] == "false"
    assert first["harvest_age_days"] == "3.00"
    assert first["collection_lidvid"] == COLL
    assert first["collection_state"] == "processed"
    assert first["in_refs"] == "true"
    assert first["rule"] == "sweeper_miss"
    assert first["severity"] == "anomalous"
    second = rows[1]
    assert second["harvest_date_time"] == ""
    assert second["harvest_age_days"] == ""
    assert second["in_refs"] == ""
    assert second["collection_lidvid"] == ""


def test_product_csv_gzip(tmp_path: Path) -> None:
    path = tmp_path / "out" / "unprocessed_products.csv.gz"
    with ProductCsvWriter(path) as writer:
        writer.write(make_candidate(), make_verdict(), NOW)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["rule"] == "sweeper_miss"


def test_product_csv_flushed_on_error(tmp_path: Path) -> None:
    path = tmp_path / "p.csv"
    with pytest.raises(ValueError):
        with ProductCsvWriter(path) as writer:
            writer.write(make_candidate(), make_verdict(), NOW)
            raise ValueError("boom")
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_write_outside_context_manager_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ProductCsvWriter(tmp_path / "x.csv").write(make_candidate(), make_verdict(), NOW)


# ── tally ─────────────────────────────────────────────────────────────────────


def test_age_bucket_boundaries() -> None:
    assert age_bucket(None) == "unknown"
    assert age_bucket(0.5) == "<=1d"
    assert age_bucket(1) == "<=1d"
    assert age_bucket(1.01) == "1-7d"
    assert age_bucket(7) == "1-7d"
    assert age_bucket(7.5) == "7-30d"
    assert age_bucket(30) == "7-30d"
    assert age_bucket(31) == ">30d"


def build_tally(collect_keys: bool = True) -> Tally:
    tally = Tally(collect_keys=collect_keys)
    # two sweeper misses and one reloaded in the same collection
    tally.add(make_candidate("p1"), make_verdict(), NOW)
    tally.add(make_candidate("p2"), make_verdict(), NOW)
    tally.add(make_candidate("p3"), make_verdict(Rule.RELOADED_AFTER_COLLECTION), NOW)
    # a different node, expected pending collection, old product
    tally.add(
        make_candidate("p4", node="geo", harvest_days_ago=40, product_class="Product_Ancillary"),
        make_verdict(Rule.COLLECTION_PENDING, Severity.EXPECTED, "urn:nasa:pds:b2:c::1.0", None),
        NOW,
    )
    # orphans
    tally.add(
        make_candidate("p5", harvest_days_ago=0.5),
        make_verdict(Rule.COLLECTION_NOT_LOADED_PENDING, Severity.EXPECTED, None, None, None),
        NOW,
    )
    tally.add(
        make_candidate("p6", harvest_days_ago=20),
        make_verdict(Rule.COLLECTION_NOT_LOADED_OVERDUE, Severity.ANOMALOUS, None, None, None),
        NOW,
    )
    # unknown age
    tally.add(
        make_candidate("p7", harvest_days_ago=None),
        make_verdict(Rule.REFS_MISSING_PENDING, Severity.EXPECTED, COLL, False),
        NOW,
    )
    return tally


def test_tally_counts() -> None:
    tally = build_tally()
    assert tally.examined == 7
    assert tally.anomalous == 4
    assert tally.expected == 3
    assert tally.by_rule_node[("anomalous", "sweeper_miss", "atm")] == 2
    assert tally.by_rule_node[("expected", "collection_pending", "geo")] == 1
    assert tally.rule_totals(Severity.ANOMALOUS)["sweeper_miss"] == 2
    assert tally.by_class[("Product_Ancillary", "expected")] == 1
    assert tally.by_class[("Product_Observational", "anomalous")] == 4
    assert tally.by_age[(">30d", "expected")] == 1
    assert tally.by_age[("unknown", "expected")] == 1
    assert tally.by_age[("<=1d", "expected")] == 1
    assert tally.by_age[("7-30d", "anomalous")] == 1


def test_tally_collection_impact_only_for_anomalous() -> None:
    tally = build_tally()
    assert list(tally.collections) == [COLL]
    impact = tally.collections[COLL]
    assert impact.total == 3
    assert impact.rule_counts["sweeper_miss"] == 2
    assert impact.rule_counts["reloaded_after_collection"] == 1
    assert impact.node == "atm"
    assert impact.bundle_lid == "urn:nasa:pds:bundle1"
    assert tally.anomalous_collection_counts() == {COLL: 3}
    assert tally.worst_collections(5) == [COLL]
    assert tally.worst_collections(0) == []


def test_tally_orphans_and_pending() -> None:
    tally = build_tally()
    orphan = tally.orphans[COLL_LID]
    assert (orphan.pending, orphan.overdue, orphan.total) == (1, 1, 2)
    assert tally.pending_by_node["geo"]["collection_pending"] == 1
    assert tally.pending_by_node["atm"]["collection_not_loaded_pending"] == 1
    assert tally.pending_by_node["atm"]["refs_missing_pending"] == 1


def test_tally_keys_optional() -> None:
    assert len(build_tally().keys) == 7
    assert build_tally(collect_keys=False).keys == set()


def test_worst_collections_ordering() -> None:
    tally = Tally()
    for i in range(3):
        tally.add(make_candidate(f"a{i}"), make_verdict(collection_lidvid="urn:x:y:z:a::1.0"), NOW)
    tally.add(make_candidate("b0"), make_verdict(collection_lidvid="urn:x:y:z:b::1.0"), NOW)
    assert tally.worst_collections(1) == ["urn:x:y:z:a::1.0"]


# ── diff ──────────────────────────────────────────────────────────────────────


def test_record_key_is_stable_64_bit() -> None:
    key = record_key("urn:a:b:c:d:e::1.0", Rule.SWEEPER_MISS)
    assert key == record_key("urn:a:b:c:d:e::1.0", "sweeper_miss")
    assert 0 <= key < 2**64
    assert key != record_key("urn:a:b:c:d:e::1.0", Rule.REFS_MISSING)
    assert key != record_key("urn:a:b:c:d:f::1.0", Rule.SWEEPER_MISS)


def test_compute_diff() -> None:
    assert compute_diff({1, 2, 3}, {3, 4}) == DiffCounts(new=1, resolved=2, persisting=1)
    assert compute_diff(set(), set()) == DiffCounts(0, 0, 0)


@pytest.mark.parametrize("name", ["previous.csv", "previous.csv.gz"])
def test_load_previous_keys_round_trip(tmp_path: Path, name: str) -> None:
    tally = build_tally()
    path = tmp_path / name
    with ProductCsvWriter(path) as writer:
        for candidate, verdict in [
            (make_candidate("p1"), make_verdict()),
            (make_candidate("p3"), make_verdict(Rule.RELOADED_AFTER_COLLECTION)),
            (make_candidate("gone"), make_verdict()),
        ]:
            writer.write(candidate, verdict, NOW)
    previous = load_previous_keys(path)
    assert len(previous) == 3
    diff = compute_diff(previous, tally.keys)
    assert diff == DiffCounts(new=5, resolved=1, persisting=2)


# ── collections outputs ───────────────────────────────────────────────────────


def test_coverage_note_cases() -> None:
    assert coverage_note(None) == ""
    assert coverage_note(RefsCoverage(3, 10, 3)) == "refs missing for 7 members (refs never written)"
    assert coverage_note(RefsCoverage(10, 10, 4)) == "refs complete but 6 members not stamped (sweeper skipped them)"
    assert coverage_note(RefsCoverage(12, 10, 4)) == "refs complete but 6 members not stamped (sweeper skipped them)"
    assert coverage_note(RefsCoverage(10, 10, 10)) == "ok"
    assert coverage_note(RefsCoverage(0, 0, 0)) == "ok"


def test_write_collections_csv(tmp_path: Path) -> None:
    bundled = make_collection(COLL, CollectionState.STAMPED_EMPTY_REFS, bundles=["urn:nasa:pds:b1::1.0", "urn:nasa:pds:b2"])
    other = make_collection("urn:nasa:pds:b9:other::2.0", refs=["urn:nasa:pds:b9::2.0"])
    path = tmp_path / "collections.csv"
    count = write_collections_csv(path, [bundled, other], {COLL: RefsCoverage(3, 10, 3)}, {COLL: 42})
    assert count == 2
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys()) == [
        "node",
        "collection_lidvid",
        "state",
        "stamp_version",
        "ancestor_refs_count",
        "harvest_date_time",
        "bundle_lidvids",
        "anomalous_product_count",
        "refs_count",
        "member_count",
        "stamped_member_count",
        "coverage_note",
        "superseded_by",
    ]
    assert rows[0]["superseded_by"] == ""
    assert rows[0]["state"] == "stamped_empty_refs"
    assert rows[0]["bundle_lidvids"] == "urn:nasa:pds:b1::1.0;urn:nasa:pds:b2"
    assert rows[0]["anomalous_product_count"] == "42"
    assert rows[0]["refs_count"] == "3"
    assert rows[0]["coverage_note"] == "refs missing for 7 members (refs never written)"
    assert rows[1]["ancestor_refs_count"] == "1"
    assert rows[1]["anomalous_product_count"] == "0"
    assert rows[1]["refs_count"] == ""
    assert rows[1]["coverage_note"] == ""


def test_write_anomalous_collections(tmp_path: Path) -> None:
    path = tmp_path / "anomalous_collections.txt"
    assert write_anomalous_collections(path, ["urn:b:b:b:c::1.0", "urn:a:a:a:c::1.0", "urn:b:b:b:c::1.0"]) == 2
    assert path.read_text(encoding="utf-8") == "urn:a:a:a:c::1.0\nurn:b:b:b:c::1.0\n"


# ── summary ───────────────────────────────────────────────────────────────────


def test_summary_sections_in_order() -> None:
    tally = build_tally()
    empty = make_collection("urn:nasa:pds:b5:empty::1.0", CollectionState.STAMPED_EMPTY_REFS, bundles=["urn:nasa:pds:b5::1.0"])
    quiet = make_collection("urn:nasa:pds:b6:quiet::1.0", CollectionState.STAMPED_EMPTY_REFS)
    anomalous = make_collection(COLL, bundles=["urn:nasa:pds:bundle1::1.0"])
    coverage = {COLL: RefsCoverage(1, 5, 1)}
    text = render_summary(
        tally,
        [anomalous, empty, quiet],
        coverage,
        TH,
        {"Node filter": "atm"},
        DiffCounts(new=2, resolved=1, persisting=5),
    )
    headings = [
        "# Unprocessed product audit",
        "## Anomalies by rule",
        "## Anomalous collections",
        "## Stamped collections with empty refs",
        "## Expected pending, by node",
        "## Orphans",
        "## Breakdown",
        "## Change since previous run",
        "## What each rule means",
    ]
    positions = [text.index(h) for h in headings]
    assert positions == sorted(positions)
    assert "Candidates examined: **7**" in text
    assert "Anomalous (need attention): **4**" in text
    assert "Node filter: atm" in text
    assert "Ancestry version: 7" in text
    # anomalous collection table content
    assert "urn:nasa:pds:bundle1::1.0" in text
    assert "refs missing for 4 members (refs never written)" in text
    # empty-refs section: one with bundle, one without
    assert "2 collections are stamped" in text
    assert "1 of them have a bundle" in text
    # diff
    assert "New: 2" in text and "Resolved: 1" in text and "Persisting: 5" in text
    # guidance for each rule seen
    for rule in ("sweeper_miss", "collection_pending", "refs_missing_pending"):
        assert f"**{rule}**" in text
    assert text.endswith("\n")


def test_summary_empty_tally_is_healthy_and_has_no_problem_sections() -> None:
    text = render_summary(Tally(), [], {}, TH, {}, None)
    assert text.startswith("# Unprocessed product audit")
    assert "No candidate products were found" in text
    assert "**Healthy: nothing needs doing.**" in text
    assert "| Who |" not in text
    assert "## Anomalies by rule" not in text


def test_summary_leads_with_what_needs_to_happen_grouped_by_owner() -> None:
    tally = build_tally()
    tally.add(make_candidate("p9"), make_verdict(Rule.COLLECTION_OVERDUE, Severity.ANOMALOUS, COLL, None), NOW)
    text = render_summary(tally, [], {}, TH, {}, None)
    assert text.index("## What needs to happen") < text.index("## Anomalies by rule")
    assert "| Who | What is wrong | Products | Collections | What to do |" in text
    assert text.index("| Node |") < text.index("| EN |") < text.index("| Sweepers team |")
    assert "Who fixes what:" in text


def test_summary_asks_for_a_closer_look_at_refs_missing_products_the_inventory_did_not_verify() -> None:
    verified = build_tally()
    verified.add(make_candidate("p8"), make_verdict(Rule.REFS_MISSING, Severity.ANOMALOUS, COLL, False), NOW)
    unverified = build_tally()
    unverified.add(
        make_candidate("p8"),
        replace(make_verdict(Rule.REFS_MISSING, Severity.ANOMALOUS, COLL, False), inventory_verified=False),
        NOW,
    )
    assert "| Needs a closer look |" not in render_summary(verified, [], {}, TH, {}, None)
    text = render_summary(unverified, [], {}, TH, {}, None)
    assert "| Needs a closer look |" in text
    assert "1 products were not checked against the collection inventory" in text


def test_summary_defines_orphaned_and_not_processed_and_prefixes_each_problem_with_its_kind() -> None:
    text = render_summary(build_tally(), [], {}, TH, {}, None)
    assert "Kinds of problem:" in text
    assert "**Not processed**: the registry's refs list the product" in text
    assert "best guess from its identifier" in text
    assert "**Orphaned**: No collection with the identifier" in text


def test_summary_skips_diff_without_previous() -> None:
    text = render_summary(build_tally(), [], {}, TH, {}, None)
    assert "Change since previous run" not in text


def test_summary_caps_long_tables() -> None:
    tally = Tally()
    for i in range(12):
        lidvid = f"urn:nasa:pds:bundle1:coll{i:02d}::1.0"
        for j in range(i + 1):
            cand = make_candidate(f"x{i}_{j}")
            tally.add(cand, make_verdict(collection_lidvid=lidvid), NOW)
    text = render_summary(tally, [], {}, TH, {}, None, max_rows=5)
    assert "7 more collections omitted; the CSV files hold everything." in text
    assert "coll11" in text
    assert "coll00" not in text
    assert "not queried" in text


def test_summary_bundle_fallbacks() -> None:
    tally = Tally()
    cand = make_candidate()
    tally.add(cand, make_verdict(), NOW)
    # bundle_lidvids empty: falls back to a bundle-looking ancestor ref, ignoring collection-like refs
    coll = make_collection(refs=["urn:nasa:pds:bundle1::1.0", "urn:nasa:pds:bundle1:data::1.0"])
    with_ref = render_summary(tally, [coll], {}, TH, {}, None)
    assert "| atm | urn:nasa:pds:bundle1::1.0 |" in with_ref
    # no refs either: falls back to the bundle LID derived from the product
    without = render_summary(tally, [make_collection()], {}, TH, {}, None)
    assert "| atm | urn:nasa:pds:bundle1 |" in without
    # collection unknown: still renders from the verdict
    unknown = render_summary(tally, [], {}, TH, {}, None)
    assert "| atm | urn:nasa:pds:bundle1 |" in unknown
