"""Tests for ``audit_rollup`` (local files only)."""

from __future__ import annotations

from pathlib import Path

import audit_rollup as rollup
from unprocessed_audit.model import Rule
from unprocessed_audit.regression import Metrics


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
    }
    values.update(overrides)
    return Metrics(**values)  # type: ignore[arg-type]


def write(audits: Path, node: str, m: Metrics) -> None:
    (audits / node).mkdir(parents=True)
    (audits / node / "metrics.json").write_text(m.to_json(), encoding="utf-8")


def test_table_has_a_row_per_node_a_total_and_counts_by_owner(tmp_path: Path):
    write(tmp_path, "b", metrics(examined=50, expected=2, owners={"node": 30, "registry_operations": 5}))
    write(tmp_path, "a", metrics(examined=10, owners={"sweepers_team": 1}, empty_refs_with_bundle=["x", "y"]))
    table = rollup.render_table(rollup.load_all(tmp_path))
    lines = table.splitlines()
    assert lines[0].startswith("| Node | Products examined | Needs attention: Node |")
    assert lines[2] == "| a | 10 | 0 | 0 | 1 | 0 | 2 | 10 |"  # sorted by node name
    assert lines[3] == "| b | 50 | 30 | 5 | 0 | 0 | 0 | 2 |"
    assert lines[4] == "| **Total** | **60** | **30** | **5** | **1** | **0** | **2** | **12** |"


def test_products_without_an_inventory_check_are_called_out(tmp_path: Path):
    write(tmp_path, "a", metrics(unverified_refs_missing=1234))
    write(tmp_path, "b", metrics())
    assert "a (1,234)" in rollup.render_table(rollup.load_all(tmp_path))
    assert "could not be checked" not in rollup.render_table({"b": metrics()})


def test_main_prints_and_writes_the_table(tmp_path: Path, capsys):
    write(tmp_path / "audits", "a", metrics())
    out = tmp_path / "table.md"
    assert rollup.main(["--audits-dir", str(tmp_path / "audits"), "--output", str(out)]) == 0
    assert "| a | 100 |" in capsys.readouterr().out
    assert out.read_text(encoding="utf-8").startswith("| Node |")


def test_main_fails_without_metrics_or_with_a_bad_file(tmp_path: Path):
    assert rollup.main(["--audits-dir", str(tmp_path)]) == 1
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "metrics.json").write_text("not json", encoding="utf-8")
    assert rollup.main(["--audits-dir", str(tmp_path)]) == 1
