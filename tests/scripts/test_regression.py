"""Tests for ``unprocessed_audit.regression`` and the ``--check`` mode of the audit CLI (no network)."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from datetime import timezone
from pathlib import Path

import audit_unprocessed_products as cli
import pytest
from test_cli import C_EMPTY
from test_cli import FakeRegistry
from test_cli import make_args
from unprocessed_audit import regression
from unprocessed_audit.model import SUPERSEDED_FIELD
from unprocessed_audit.model import RegistryQueryError
from unprocessed_audit.model import Rule
from unprocessed_audit.regression import BaselineError
from unprocessed_audit.regression import HistoryFormatError
from unprocessed_audit.regression import Metrics

NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def metrics(**overrides: object) -> Metrics:
    values: dict[str, object] = {
        "run_time": "2026-01-01T00:00:00+00:00",
        "ancestry_version": 7,
        "nodes": ["atm"],
        "examined": 100,
        "expected": 10,
        "anomalous": 0,
        "rules": {rule.value: 0 for rule in Rule},
        "anomalous_collections": [],
        "superseded_anomalous_collections": [],
        "empty_refs_with_bundle": [],
        "unmapped_superseded": None,
    }
    values.update(overrides)
    return Metrics(**values)  # type: ignore[arg-type]


def with_rules(**counts: int) -> dict[str, int]:
    rules = {rule.value: 0 for rule in Rule}
    rules.update(counts)
    return rules


class FakeMappingClient:
    def __init__(self, mappings: dict[str, dict]) -> None:
        self.mappings = mappings
        self.requested: list[str] = []

    def get_mapping(self, index: str) -> dict:
        self.requested.append(index)
        return self.mappings[index]


# ── mapping canary ────────────────────────────────────────────────────────────


def test_mapping_has_field_finds_the_field_at_any_depth():
    mapping = {"atm-registry-000001": {"mappings": {"properties": {SUPERSEDED_FIELD: {"type": "keyword"}}}}}
    assert regression.mapping_has_field(mapping, SUPERSEDED_FIELD)
    assert not regression.mapping_has_field({"x": {"mappings": {"properties": {"other": {"type": "keyword"}}}}}, SUPERSEDED_FIELD)
    assert not regression.mapping_has_field({"x": {SUPERSEDED_FIELD: "not a definition"}}, SUPERSEDED_FIELD)


def test_find_unmapped_superseded_names_the_indices_without_the_field():
    mapped = {"i": {"mappings": {"properties": {SUPERSEDED_FIELD: {"type": "keyword"}}}}}
    unmapped = {"i": {"mappings": {"properties": {"vid": {"type": "keyword"}}}}}
    client = FakeMappingClient({"geo-registry": mapped, "atm-registry": unmapped})
    assert regression.find_unmapped_superseded(client, ["atm", "geo"]) == ["atm-registry"]  # type: ignore[arg-type]
    assert client.requested == ["atm-registry", "geo-registry"]


def test_find_unmapped_superseded_rejects_an_empty_mapping():
    with pytest.raises(RegistryQueryError, match="came back empty"):
        regression.find_unmapped_superseded(FakeMappingClient({"atm-registry": {}}), ["atm"])  # type: ignore[arg-type]


# ── metrics file ──────────────────────────────────────────────────────────────


def test_metrics_round_trip(tmp_path: Path):
    original = metrics(anomalous=3, rules=with_rules(refs_missing=3), anomalous_collections=["urn:a:b:c::1.0"])
    path = tmp_path / "metrics.json"
    path.write_text(original.to_json(), encoding="utf-8")
    assert regression.load_metrics(path) == original


def test_load_metrics_rejects_bad_files(tmp_path: Path):
    with pytest.raises(BaselineError, match="Could not read"):
        regression.load_metrics(tmp_path / "missing.json")
    wrong_schema = tmp_path / "old.json"
    wrong_schema.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    with pytest.raises(BaselineError, match="schema version"):
        regression.load_metrics(wrong_schema)
    incomplete = tmp_path / "incomplete.json"
    incomplete.write_text(json.dumps({"schema_version": 1, "run_time": "x"}), encoding="utf-8")
    with pytest.raises(BaselineError, match="malformed"):
        regression.load_metrics(incomplete)


def test_check_comparable_requires_the_same_nodes_and_version():
    baseline = metrics()
    regression.check_comparable(["atm"], 7, baseline)
    with pytest.raises(BaselineError, match="nodes"):
        regression.check_comparable(["atm", "geo"], 7, baseline)
    with pytest.raises(BaselineError, match="ancestry version"):
        regression.check_comparable(["atm"], 8, baseline)


# ── invariants ────────────────────────────────────────────────────────────────


def test_a_clean_run_passes_with_and_without_a_baseline():
    assert regression.evaluate(metrics()) == []
    assert regression.evaluate(metrics(), metrics()) == []


def test_without_a_baseline_any_anomaly_fails():
    violations = regression.evaluate(metrics(anomalous=5, rules=with_rules(refs_missing=5)))
    assert [v.invariant for v in violations] == [regression.NO_ANOMALOUS_PRODUCTS]
    assert violations[0].details == ["refs_missing: 5"]


def test_without_a_baseline_an_empty_refs_collection_with_a_bundle_fails():
    violations = regression.evaluate(metrics(empty_refs_with_bundle=[C_EMPTY]))
    assert [v.invariant for v in violations] == [regression.NO_EMPTY_REFS_WITH_BUNDLE]
    assert violations[0].details == [C_EMPTY]


def test_a_known_backlog_does_not_fail_against_a_baseline():
    backlog = metrics(
        anomalous=9, rules=with_rules(inventory_version_mismatch=9), anomalous_collections=["urn:a:b:c::1.0"],
        empty_refs_with_bundle=[C_EMPTY],
    )  # fmt: skip
    assert regression.evaluate(backlog, backlog) == []


def test_an_improvement_does_not_fail_against_a_baseline():
    before = metrics(anomalous=9, rules=with_rules(refs_missing=9), anomalous_collections=["urn:a:b:c::1.0"])
    assert regression.evaluate(metrics(), before) == []


def test_a_new_anomalous_collection_fails_against_a_baseline():
    before = metrics(anomalous=2, rules=with_rules(refs_missing=2), anomalous_collections=["urn:a:b:c::1.0"])
    now = metrics(
        anomalous=4, rules=with_rules(refs_missing=2, sweeper_miss=2),
        anomalous_collections=["urn:a:b:c::1.0", "urn:a:b:d::1.0"],
    )  # fmt: skip
    violations = regression.evaluate(now, before)
    assert [v.invariant for v in violations] == [regression.NO_NEW_ANOMALIES]
    assert "urn:a:b:d::1.0" in violations[0].details
    assert "sweeper_miss: 0 -> 2" in violations[0].details


def test_growth_of_a_rule_without_a_new_collection_fails_against_a_baseline():
    before = metrics(anomalous=1, rules=with_rules(collection_not_loaded_overdue=1))
    now = metrics(anomalous=3, rules=with_rules(collection_not_loaded_overdue=3))
    violations = regression.evaluate(now, before)
    assert violations[0].details == ["collection_not_loaded_overdue: 1 -> 3"]


def test_a_new_superseded_anomalous_collection_fails_against_a_baseline():
    now = metrics(anomalous=1, rules=with_rules(refs_missing=1), superseded_anomalous_collections=["urn:a:b:c::1.0"])
    assert [v.invariant for v in regression.evaluate(now, metrics())] == [regression.NO_NEW_ANOMALIES]


def test_a_new_empty_refs_collection_fails_against_a_baseline():
    violations = regression.evaluate(metrics(empty_refs_with_bundle=[C_EMPTY]), metrics())
    assert [v.invariant for v in violations] == [regression.NO_EMPTY_REFS_WITH_BUNDLE]


def test_an_unmapped_superseded_field_always_fails():
    now = metrics(unmapped_superseded=["atm-registry"])
    for baseline in (None, now):
        violations = regression.evaluate(now, baseline)
        assert [v.invariant for v in violations] == [regression.SUPERSEDED_BY_MAPPED]
        assert violations[0].details == ["atm-registry"]


def test_render_check_section_states_the_outcome():
    assert "**PASS**" in regression.render_check_section([], None, True)
    text = regression.render_check_section(
        [regression.Violation("x", "bad", [f"item{n}" for n in range(25)])], metrics(), False
    )
    assert "**FAIL**" in text
    assert "baseline of 2026-01-01T00:00:00+00:00" in text
    assert "item19" in text and "item20" not in text
    assert "... and 5 more" in text
    assert "superseded_by_mapped" in text  # says the mapping invariant was not evaluated


# ── history ───────────────────────────────────────────────────────────────────


def test_history_appends_rows_under_one_header(tmp_path: Path):
    path = tmp_path / "history" / "runs.csv"
    regression.append_history(path, metrics(anomalous=2, rules=with_rules(refs_missing=2), anomalous_collections=["a"]))
    regression.append_history(path, metrics())
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["anomalous"] for r in rows] == ["2", "0"]
    assert rows[0]["refs_missing"] == "2"
    assert rows[0]["anomalous_collections"] == "1"
    assert rows[0]["nodes"] == "atm"
    assert list(rows[0]) == regression.HISTORY_COLUMNS


def test_history_with_other_columns_is_rejected(tmp_path: Path):
    path = tmp_path / "runs.csv"
    path.write_text("when,count\n", encoding="utf-8")
    with pytest.raises(HistoryFormatError, match="expected"):
        regression.append_history(path, metrics())
    assert path.read_text(encoding="utf-8") == "when,count\n"


# ── CLI ───────────────────────────────────────────────────────────────────────


@pytest.fixture()
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeRegistry:
    registry = FakeRegistry()
    registry.install(monkeypatch)
    monkeypatch.setattr(cli, "find_unmapped_superseded", lambda client, nodes: [])
    return registry


def test_baseline_needs_check(tmp_path: Path):
    with pytest.raises(SystemExit):
        make_args(tmp_path, "--baseline", str(tmp_path / "metrics.json"))


def test_check_is_not_allowed_on_a_partial_run(tmp_path: Path):
    with pytest.raises(SystemExit):
        make_args(tmp_path, "--check", "--max-products", "10")


def test_run_audit_writes_metrics_without_checking(tmp_path: Path, fake: FakeRegistry):
    result = cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    written = json.loads((tmp_path / "out" / "metrics.json").read_text(encoding="utf-8"))
    assert written["schema_version"] == 1
    assert written["examined"] == 6
    assert written["anomalous"] == result.tally.anomalous
    assert written["rules"]["refs_missing"] == 1
    assert written["unmapped_superseded"] is None
    assert written["empty_refs_with_bundle"] == [C_EMPTY]
    assert result.violations == [] and result.checked is False
    assert "Regression check" not in result.summary


def test_check_without_a_baseline_fails_on_anomalies(tmp_path: Path, fake: FakeRegistry):
    result = cli.run_audit(make_args(tmp_path, "--check"), client=object(), now=NOW)  # type: ignore[arg-type]
    assert result.checked is True
    assert {v.invariant for v in result.violations} == {
        regression.NO_ANOMALOUS_PRODUCTS,
        regression.NO_EMPTY_REFS_WITH_BUNDLE,
    }
    assert result.metrics.unmapped_superseded == []
    assert "**FAIL**" in result.summary
    assert "**FAIL**" in (tmp_path / "out" / "summary.md").read_text(encoding="utf-8")


def test_check_against_the_run_that_made_the_baseline_passes(tmp_path: Path, fake: FakeRegistry):
    first = cli.run_audit(make_args(tmp_path / "first"), client=object(), now=NOW)  # type: ignore[arg-type]
    baseline = first.paths["metrics"]
    second = cli.run_audit(
        make_args(tmp_path / "second", "--check", "--baseline", str(baseline)), client=object(), now=NOW  # type: ignore[arg-type]
    )
    assert second.violations == []
    assert "**PASS**" in second.summary


def test_check_against_a_cleaner_baseline_fails_on_what_is_new(tmp_path: Path, fake: FakeRegistry):
    first = cli.run_audit(make_args(tmp_path / "first"), client=object(), now=NOW)  # type: ignore[arg-type]
    clean = metrics(nodes=["atm"], examined=first.metrics.examined)
    baseline = tmp_path / "baseline.json"
    baseline.write_text(clean.to_json(), encoding="utf-8")
    second = cli.run_audit(
        make_args(tmp_path / "second", "--check", "--baseline", str(baseline)), client=object(), now=NOW  # type: ignore[arg-type]
    )
    assert [v.invariant for v in second.violations][0] == regression.NO_NEW_ANOMALIES


def test_check_reports_an_unmapped_superseded_field(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cli, "find_unmapped_superseded", lambda client, nodes: ["atm-registry"])
    first = cli.run_audit(make_args(tmp_path / "first"), client=object(), now=NOW)  # type: ignore[arg-type]
    second = cli.run_audit(
        make_args(tmp_path / "second", "--check", "--baseline", str(first.paths["metrics"])), client=object(), now=NOW  # type: ignore[arg-type]
    )
    assert [v.invariant for v in second.violations] == [regression.SUPERSEDED_BY_MAPPED]


def test_no_mapping_check_skips_the_mapping_read(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
):
    def boom(client: object, nodes: object) -> list[str]:
        raise AssertionError("the mapping must not be read")

    monkeypatch.setattr(cli, "find_unmapped_superseded", boom)
    result = cli.run_audit(make_args(tmp_path, "--check", "--no-mapping-check"), client=object(), now=NOW)  # type: ignore[arg-type]
    assert result.metrics.unmapped_superseded is None
    assert "invariant was not evaluated" in result.summary


def test_baseline_for_other_nodes_stops_the_run_before_the_scan(tmp_path: Path, fake: FakeRegistry):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(metrics(nodes=["geo"]).to_json(), encoding="utf-8")
    with pytest.raises(BaselineError, match="nodes"):
        cli.run_audit(make_args(tmp_path, "--check", "--baseline", str(baseline)), client=object(), now=NOW)  # type: ignore[arg-type]
    assert fake.lookup_calls == []


def test_a_bad_history_file_stops_the_run_before_the_scan(tmp_path: Path, fake: FakeRegistry):
    history = tmp_path / "runs.csv"
    history.write_text("when,count\n", encoding="utf-8")
    with pytest.raises(HistoryFormatError):
        cli.run_audit(make_args(tmp_path, "--history-csv", str(history)), client=object(), now=NOW)  # type: ignore[arg-type]
    assert fake.lookup_calls == []


def test_history_row_is_appended_per_run(tmp_path: Path, fake: FakeRegistry):
    history = tmp_path / "runs.csv"
    for name in ("one", "two"):
        cli.run_audit(make_args(tmp_path / name, "--history-csv", str(history)), client=object(), now=NOW)  # type: ignore[arg-type]
    assert len(list(csv.DictReader(history.open(encoding="utf-8")))) == 2


def test_main_exits_two_when_an_invariant_is_violated(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(cli, "make_registry_auth", lambda: object())
    monkeypatch.setattr(cli, "registry_endpoint_from_env", lambda: "https://example.invalid")
    assert cli.main(["--output-dir", str(tmp_path / "out"), "--node", "atm", "--check"]) == 2
    assert "invariants violated" in capsys.readouterr().out


def test_main_exits_zero_when_the_baseline_matches(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(cli, "make_registry_auth", lambda: object())
    monkeypatch.setattr(cli, "registry_endpoint_from_env", lambda: "https://example.invalid")
    assert cli.main(["--output-dir", str(tmp_path / "first"), "--node", "atm"]) == 0
    baseline = tmp_path / "first" / "metrics.json"
    args = ["--output-dir", str(tmp_path / "second"), "--node", "atm", "--check", "--baseline", str(baseline)]
    assert cli.main(args) == 0
    assert "Regression check: passed" in capsys.readouterr().out


def test_main_exits_one_for_an_unusable_baseline(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cli, "make_registry_auth", lambda: object())
    monkeypatch.setattr(cli, "registry_endpoint_from_env", lambda: "https://example.invalid")
    missing = tmp_path / "missing.json"
    assert cli.main(["--output-dir", str(tmp_path / "out"), "--node", "atm", "--check", "--baseline", str(missing)]) == 1


def test_metrics_count_anomalous_products_by_owner(tmp_path: Path, fake: FakeRegistry):
    with_inventory = cli.run_audit(make_args(tmp_path / "checked"), client=object(), now=NOW)  # type: ignore[arg-type]
    assert sum(with_inventory.metrics.owners.values()) == with_inventory.metrics.anomalous
    without = cli.run_audit(make_args(tmp_path / "unchecked", "--no-inventory"), client=object(), now=NOW)  # type: ignore[arg-type]
    # no inventory was read in either run (the fake collections have no inventory URL), so refs_missing is unverified
    refs_missing = without.metrics.rules["refs_missing"]
    assert without.metrics.unverified_refs_missing == refs_missing >= 1
    assert without.metrics.owners["needs_check"] == refs_missing
    assert "| Needs a closer look |" in without.summary


def test_metrics_owners_survive_a_round_trip(tmp_path: Path):
    original = metrics(owners={"node": 5}, unverified_refs_missing=3)
    path = tmp_path / "metrics.json"
    path.write_text(original.to_json(), encoding="utf-8")
    assert regression.load_metrics(path) == original
    legacy = json.loads(original.to_json())
    del legacy["owners"], legacy["unverified_refs_missing"]
    path.write_text(json.dumps(legacy), encoding="utf-8")
    assert regression.load_metrics(path).owners == {} and regression.load_metrics(path).unverified_refs_missing == 0
