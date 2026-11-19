"""Tests for ``generate_report_card`` and ``collect_node_totals`` (local files and a fake client only)."""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import collect_node_totals as totals
import generate_report_card as rc
import pytest

TODAY = date(2026, 11, 17)
CONFIG = rc.Config(
    5.0,
    14,
    "https://example.test/docs",
    "audits/latest",
    [
        {"node": "atm", "label": "ATM", "status_node": "PDS_ATM"},
        {"node": "sbnpsi", "label": "SBN PSI", "status_node": "PDS_SBN", "shared_with": ["sbnpsi", "sbnumd"]},
        {"node": "sbnumd", "label": "SBN UMD", "status_node": "PDS_SBN", "shared_with": ["sbnpsi", "sbnumd"]},
    ],
    frozenset({"lid", "ops:Provenance/ops:superseded_by"}),
)


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def metrics(**overrides: object) -> dict:
    values: dict = {
        "run_time": "2026-11-16T12:00:00+00:00",
        "owners": {"node": 0, "en": 0, "sweepers_team": 0, "needs_check": 0, "no_action": 0},
        "empty_refs_with_bundle": [],
    }
    values.update(overrides)
    return values


def build_tree(tmp_path: Path, *, atm_owners: dict | None = None, discrepancies: list[list[object]] | None = None) -> tuple[Path, Path]:
    status, fidelity = tmp_path / "status", tmp_path / "status" / "fidelity"
    write_csv(
        status / "burnup_by_node_latest.csv",
        ["node", "date", "cumulative_bundles", "cumulative_collections", "target_bundles", "target_collections"],
        [
            ["PDS_ATM", "2025-01-01", 1, 1, 10, 10],
            ["PDS_ATM", "2026-11-10", 10, 90, 10, 100],
            ["PDS_SBN", "2026-11-10", 20, 80, 20, 80],
        ],
    )
    write_csv(status / "counts_history.csv", ["date"], [["2026-11-01"], ["2026-11-16"]])
    write_csv(status / "bad_file_ref_bundles_in_registry.csv", ["node", "lidvid"], [["PDS_ATM", "a"], ["PDS_ATM", "a"]])
    write_csv(status / "bad_file_ref_collections_in_registry.csv", ["node", "lidvid"], [["PDS_ATM", "c1"], ["PDS_ATM", "c2"]])
    write_csv(status / "bad_file_ref_products_in_registry.csv", ["node", "products"], [["PDS_ATM", 7]])
    (fidelity / "node_totals.json").parent.mkdir(parents=True, exist_ok=True)
    (fidelity / "node_totals.json").write_text(
        json.dumps({"generated": "2026-11-16", "visible_products": {"atm": 1000, "sbnpsi": 500, "sbnumd": 500}}), encoding="utf-8"
    )
    for node, owners in (("atm", atm_owners or {"node": 10}), ("sbnpsi", {}), ("sbnumd", {})):
        folder = fidelity / node
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "metrics.json").write_text(json.dumps(metrics(owners=owners)), encoding="utf-8")
    write_csv(
        fidelity / "index-mappings" / "mapping_discrepancies.csv",
        ["group", "index", "node", "field", "kind", "severity", "expected", "actual"],
        discrepancies or [],
    )
    (fidelity / "index-mappings" / "mapping_summary.md").write_text("# Index mapping audit\n\nRun time: 2026-11-16\n", encoding="utf-8")
    return status, fidelity


@pytest.mark.parametrize(
    "issues, total, expected",
    [
        (0, 100, rc.Status.GREEN),
        (0, 0, rc.Status.GREEN),
        (1, 1_000_000, rc.Status.YELLOW),
        (4, 100, rc.Status.YELLOW),
        (5, 100, rc.Status.RED),
        (50, 100, rc.Status.RED),
        (1, 0, rc.Status.RED),
    ],
)
def test_grade_is_green_with_no_issues_yellow_below_the_limit_and_red_from_it(issues, total, expected):
    assert rc.grade(issues, total, 5.0) is expected


def test_worst_of_several_scores():
    assert rc.worst([rc.Status.GREEN, rc.Status.YELLOW, rc.Status.RED]) is rc.Status.RED
    assert rc.worst([rc.Status.GREEN, rc.Status.STALE]) is rc.Status.STALE
    assert rc.worst([rc.Status.YELLOW, rc.Status.STALE]) is rc.Status.YELLOW
    assert rc.worst([]) is rc.Status.NO_DATA


def test_loading_uses_the_latest_burnup_row_per_node(tmp_path: Path):
    status, _ = build_tree(tmp_path)
    assert rc.read_loading(status)["PDS_ATM"] == (10, 110, 100)


def test_bad_file_refs_count_distinct_bundles_and_collections_plus_product_groups(tmp_path: Path):
    status, _ = build_tree(tmp_path)
    assert rc.read_bad_file_refs(status) == {"PDS_ATM": 1 + 2 + 7}


def test_node_scores_follow_the_rubric(tmp_path: Path):
    status, fidelity = build_tree(tmp_path, atm_owners={"node": 30, "needs_check": 30})
    atm = rc.build_cards(status, fidelity, CONFIG, TODAY)[0]
    assert (atm.loading.issues, atm.loading.total, atm.loading.status) == (10, 110, rc.Status.RED)  # 9.1 percent
    assert (atm.file_paths.issues, atm.file_paths.status) == (10, rc.Status.YELLOW)  # 1 percent
    assert (atm.fidelity.issues, atm.fidelity.status) == (60, rc.Status.RED)  # 6 percent
    assert atm.overall is rc.Status.RED


def test_fidelity_is_red_from_five_percent(tmp_path: Path):
    status, fidelity = build_tree(tmp_path, atm_owners={"node": 50})
    assert rc.build_cards(status, fidelity, CONFIG, TODAY)[0].fidelity.status is rc.Status.RED


def test_index_health_is_separate_from_the_node_status(tmp_path: Path):
    status, fidelity = build_tree(tmp_path, atm_owners={"en": 5, "sweepers_team": 1})
    atm = rc.build_cards(status, fidelity, CONFIG, TODAY)[0]
    assert atm.fidelity.status is rc.Status.GREEN
    assert atm.health.status is rc.Status.YELLOW  # 6 of 1000 products
    assert atm.overall is rc.Status.RED  # loading is red; health is not part of it
    assert atm.en_issues  # EN-owned issues are flagged beside the node status


def test_owners_are_computed_from_the_rule_counts_not_the_stored_owners(tmp_path: Path):
    status, fidelity = build_tree(tmp_path)
    # Stored under the earlier ownership: the reloaded products were the node's.
    stale = metrics(
        owners={"node": 60, "en": 0, "sweepers_team": 0, "needs_check": 0, "no_action": 0},
        rules={"reloaded_after_collection": 50, "stale_stamp": 4, "inventory_version_mismatch": 6, "bare_lid_in_inventory": 2},
    )
    (fidelity / "atm" / "metrics.json").write_text(json.dumps(stale), encoding="utf-8")
    atm = rc.build_cards(status, fidelity, CONFIG, TODAY)[0]
    assert (atm.fidelity.issues, atm.fidelity.status) == (6, rc.Status.YELLOW)  # only the node's 6 products
    assert atm.health.status is rc.Status.RED  # 54 EN products and 2 sweepers team products of 1000
    assert "EN to repair (stamped before loaded, overwritten, never processed): 54 products" in atm.health.detail
    assert "Sweepers team: 2 products" in atm.health.detail
    assert rc._products(1) == "1 product" and rc._products(1234) == "1,234 products"


def test_owner_counts_use_the_rules_and_the_unverified_refs_and_fall_back_to_stored_owners():
    split = rc.owner_counts({"rules": {"refs_missing": 5, "collection_overdue": 3}, "unverified_refs_missing": 2, "owners": {"node": 99}})
    assert (split["node"], split["needs_check"], split["en"]) == (3, 2, 3)
    assert rc.owner_counts({"owners": {"node": 7, "en": 1}}) == {"node": 7, "en": 1}
    assert rc.owner_counts({}) == {}


def test_index_health_labels_the_lines_as_ens(tmp_path: Path):
    status, fidelity = build_tree(tmp_path)
    (fidelity / "atm" / "metrics.json").write_text(
        json.dumps(metrics(rules={"stale_stamp": 5}, empty_refs_with_bundle=["c1"])), encoding="utf-8"
    )
    detail = rc.build_cards(status, fidelity, CONFIG, TODAY)[0].health.detail
    assert "EN to repair (stamped before loaded, overwritten, never processed): 5 products" in detail
    assert "Collections without a bundle link (EN): 1" in detail
    assert "Sweepers team" not in detail  # nothing is the sweepers team's here


def test_only_missing_or_mismatched_api_fields_make_the_index_health_red(tmp_path: Path):
    missing = ["registry", "temp-atm-registry", "temp-atm", "ops:Provenance/ops:superseded_by", "missing_field", "error", "keyword", "(absent)"]
    status, fidelity = build_tree(tmp_path, discrepancies=[missing])
    atm = rc.build_cards(status, fidelity, CONFIG, TODAY)[0]
    assert atm.health.status is rc.Status.RED and "superseded_by" in atm.health.detail

    mismatch = ["registry", "x-registry", "sbnumd", "lid", "type_mismatch", "error", "keyword", "long"]
    status, fidelity = build_tree(tmp_path / "b", discrepancies=[mismatch])
    cards = {c.node: c for c in rc.build_cards(status, fidelity, CONFIG, TODAY)}
    assert cards["sbnumd"].health.status is rc.Status.RED
    assert cards["atm"].health.status is rc.Status.GREEN


def test_other_mapping_differences_and_text_against_keyword_are_green(tmp_path: Path):
    rows = [
        ["registry", "x", "sbnumd", "sb:Exposure/sb:exposure_duration", "type_mismatch", "error", "double", "keyword"],
        ["registry", "x", "sbnumd", "pds:Person/pds:given_name", "missing_field", "warning", "text", "(absent)"],
        ["registry", "x", "sbnpsi", "ops:Provenance/ops:registry_sweepers_provenance_version", "type_mismatch", "error", "integer", "keyword"],
        ["registry", "x", "atm", "lid", "type_mismatch", "error", "keyword", "text"],
        ["registry", "x", "atm", "ops:Provenance/ops:superseded_by", "type_mismatch", "error", "text", "keyword"],
    ]
    status, fidelity = build_tree(tmp_path, discrepancies=rows)
    for card in rc.build_cards(status, fidelity, CONFIG, TODAY):
        assert card.health.status is rc.Status.GREEN, card.node


def test_collections_without_a_bundle_link_are_graded_against_the_node_collections(tmp_path: Path):
    status, fidelity = build_tree(tmp_path)
    (fidelity / "sbnumd" / "metrics.json").write_text(
        json.dumps(metrics(empty_refs_with_bundle=[f"c{i}" for i in range(4)])), encoding="utf-8"
    )
    cards = {c.node: c for c in rc.build_cards(status, fidelity, CONFIG, TODAY)}
    assert cards["sbnumd"].health.status is rc.Status.RED  # 4 of 80 collections is 5 percent
    (fidelity / "sbnumd" / "metrics.json").write_text(
        json.dumps(metrics(empty_refs_with_bundle=["c"])), encoding="utf-8"
    )
    cards = {c.node: c for c in rc.build_cards(status, fidelity, CONFIG, TODAY)}
    assert cards["sbnumd"].health.status is rc.Status.YELLOW


def test_shared_sbn_status_node_is_counted_for_both_indices(tmp_path: Path):
    status, fidelity = build_tree(tmp_path)
    cards = {c.node: c for c in rc.build_cards(status, fidelity, CONFIG, TODAY)}
    assert cards["sbnpsi"].loading.total == cards["sbnumd"].loading.total == 100
    assert cards["sbnpsi"].file_paths.total == 1000
    assert "SBN" in cards["sbnpsi"].shared_note


def test_old_data_makes_a_green_score_stale_but_keeps_a_red_one(tmp_path: Path):
    status, fidelity = build_tree(tmp_path, atm_owners={"node": 500})
    cards = rc.build_cards(status, fidelity, CONFIG, date(2026, 12, 31))
    atm, psi = cards[0], cards[1]
    assert atm.fidelity.status is rc.Status.RED and atm.fidelity.stale
    assert psi.fidelity.status is rc.Status.STALE


def test_a_missing_audit_or_total_is_no_data_not_green(tmp_path: Path):
    status, fidelity = build_tree(tmp_path)
    (fidelity / "atm" / "metrics.json").unlink()
    atm = rc.build_cards(status, fidelity, CONFIG, TODAY)[0]
    assert atm.fidelity.status is rc.Status.NO_DATA
    (fidelity / "node_totals.json").unlink()
    atm = rc.build_cards(status, fidelity, CONFIG, TODAY)[0]
    assert atm.file_paths.status is rc.Status.NO_DATA


def test_outputs_are_written_with_a_row_per_node_and_links(tmp_path: Path):
    status, fidelity = build_tree(tmp_path)
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "yellow_below_percent": 5,
                "stale_after_days": 14,
                "base_url": "https://example.test/docs",
                "latest_report": "audits/latest",
                "nodes": CONFIG.nodes,
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    code = rc.main(["--status-dir", str(status), "--config", str(config_file), "--output-dir", str(out), "--today", "2026-11-17"])
    assert code == 0
    page = (out / "report_card.html").read_text(encoding="utf-8")
    assert page.count("<tr>") == 4  # header and three nodes
    assert "https://example.test/docs/audits/latest/nodes/atm.md" in page
    assert "Index Health *" in page and '<abbr title="EN' in page and "&lt;" not in page.split("<style>")[0]
    rubric = page.split("How the scores work")[1]
    for case in ("stamped before their products were loaded", "overwrote", "link to their bundle", "never processed",
                 "ancestry orphan repair", "bundle-link pass"):  # fmt: skip
        assert case in rubric
    assert "Fidelity</strong> (the node's)" in rubric
    assert "EN's problem, not the node's" in page
    markdown = (out / "report_card.md").read_text(encoding="utf-8")
    assert "| ATM |" in markdown
    assert "Loading, File paths and Fidelity are the node's" in markdown and "overwrote" in markdown
    assert json.loads((out / "report_card.json").read_text(encoding="utf-8"))["atm"]["overall"] == "red"


def test_an_unreadable_configuration_exits_with_1(tmp_path: Path):
    assert rc.main(["--status-dir", str(tmp_path), "--config", str(tmp_path / "missing.json")]) == 1


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def count(self, index: str, body: dict) -> int:
        self.calls.append((index, body))
        return 42


def test_node_totals_count_visible_products_per_index_and_are_written(tmp_path: Path):
    client = FakeClient()
    result = totals.count_visible_products(client, ["atm", "en"])  # type: ignore[arg-type]
    assert result == {"atm": 42, "en": 42}
    assert [call[0] for call in client.calls] == ["atm-registry", "en-registry"]
    assert "must_not" in client.calls[0][1]["query"]["bool"]
    path = tmp_path / "t" / "node_totals.json"
    totals.write_totals(path, result, TODAY)
    assert json.loads(path.read_text(encoding="utf-8")) == {"generated": "2026-11-17", "visible_products": {"atm": 42, "en": 42}}
