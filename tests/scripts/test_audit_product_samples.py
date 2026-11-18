"""Tests for ``audit_product_samples`` (local files only)."""

from __future__ import annotations

import csv
import gzip
from pathlib import Path

import audit_product_samples as samples
from unprocessed_audit.report import PRODUCT_COLUMNS


def row(lidvid: str, rule: str, collection: str = "urn:a:b:c::1.0", severity: str = "anomalous", rationale: str = "why") -> dict:
    values = dict.fromkeys(PRODUCT_COLUMNS, "")
    values.update(
        {
            "node": "atm",
            "lidvid": lidvid,
            "product_class": "Product_Observational",
            "harvest_date_time": "2026-01-01T00:00:00+00:00",
            "collection_lidvid": collection,
            "rule": rule,
            "severity": severity,
            "rationale": rationale,
        }
    )
    return values


def write_csv(path: Path, rows: list[dict]) -> None:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt", encoding="utf-8", newline="") as handle:  # type: ignore[operator]
        writer = csv.DictWriter(handle, fieldnames=PRODUCT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def test_each_group_keeps_its_lowest_lidvids_and_its_full_size(tmp_path: Path):
    path = tmp_path / "unprocessed_products.csv.gz"
    write_csv(path, [row(f"urn:a:b:c:p{n:02d}::1.0", "inventory_version_mismatch") for n in (7, 3, 9, 1, 5)])
    sizes, kept = samples.collect_samples(path, 3)
    group = ("inventory_version_mismatch", "urn:a:b:c::1.0")
    assert sizes[group] == 5
    assert [r["lidvid"] for r in kept[group]] == ["urn:a:b:c:p01::1.0", "urn:a:b:c:p03::1.0", "urn:a:b:c:p05::1.0"]


def test_groups_are_split_by_rule_and_collection_and_expected_rows_are_skipped(tmp_path: Path):
    path = tmp_path / "unprocessed_products.csv"
    write_csv(
        path,
        [
            row("urn:a:b:c:p1::1.0", "reloaded_after_collection"),
            row("urn:a:b:c:p2::1.0", "reloaded_after_collection", collection="urn:a:b:d::1.0"),
            row("urn:a:b:c:p3::1.0", "refs_missing_pending", severity="expected"),
            row("urn:a:b:x:p4::1.0", "collection_not_loaded_overdue", collection=""),
        ],
    )
    sizes, _ = samples.collect_samples(path, 5)
    assert sizes == {
        ("reloaded_after_collection", "urn:a:b:c::1.0"): 1,
        ("reloaded_after_collection", "urn:a:b:d::1.0"): 1,
        ("collection_not_loaded_overdue", samples.NO_COLLECTION): 1,
    }


def test_rows_carry_the_owner_and_are_ordered_by_owner_then_group_size(tmp_path: Path):
    path = tmp_path / "unprocessed_products.csv.gz"
    write_csv(
        path,
        [row(f"urn:a:b:c:s{n}::1.0", "sweeper_miss", collection="urn:a:b:s::1.0") for n in range(2)]
        + [row(f"urn:a:b:c:r{n}::1.0", "reloaded_after_collection", collection="urn:a:b:r::1.0") for n in range(3)]
        + [row(f"urn:a:b:c:n{n}::1.0", "inventory_version_mismatch", collection="urn:a:b:n::1.0") for n in range(1)],
    )
    rows = samples.sample_rows("atm", path, 10)
    assert [(r["owner"], r["rule"], r["products_in_group"]) for r in rows] == [
        ("node", "reloaded_after_collection", "3"),
        ("node", "reloaded_after_collection", "3"),
        ("node", "reloaded_after_collection", "3"),
        ("node", "inventory_version_mismatch", "1"),
        ("sweepers_team", "sweeper_miss", "2"),
        ("sweepers_team", "sweeper_miss", "2"),
    ]
    assert set(rows[0]) == set(samples.SAMPLE_COLUMNS)


def test_refs_missing_without_the_inventory_needs_a_closer_look():
    assert samples.owner_for("refs_missing", "stale refs") == "node"
    assert samples.owner_for("refs_missing", "The collection inventory was not used, so the cause is unknown.") == "needs_check"


def test_main_writes_one_file_per_node(tmp_path: Path):
    audits = tmp_path / "audits"
    for node in ("a", "b"):
        (audits / node).mkdir(parents=True)
        write_csv(audits / node / "unprocessed_products.csv.gz", [row(f"urn:{node}:b:c:p::1.0", "stale_stamp")])
    (audits / "empty").mkdir()  # no per-product CSV: skipped
    out = tmp_path / "out"
    assert samples.main(["--audits-dir", str(audits), "--output-dir", str(out), "--per-group", "2"]) == 0
    with (out / "a" / "product_samples.csv").open(encoding="utf-8", newline="") as handle:
        written = list(csv.DictReader(handle))
    assert [r["lidvid"] for r in written] == ["urn:a:b:c:p::1.0"] and written[0]["node"] == "a"
    assert not (out / "empty").exists()


def test_main_fails_without_any_per_product_csv(tmp_path: Path):
    assert samples.main(["--audits-dir", str(tmp_path)]) == 1


def rows_for_report(tmp_path: Path) -> list[dict]:
    path = tmp_path / "unprocessed_products.csv.gz"
    write_csv(
        path,
        [row(f"urn:a:b:c:n{n}::1.0", "inventory_version_mismatch", collection="urn:a:b:n::1.0") for n in range(5)]
        + [row(f"urn:a:b:c:r{n}::1.0", "reloaded_after_collection", collection="urn:a:b:r::1.0") for n in range(2)],
    )
    return samples.sample_rows("atm", path, 10)


def test_the_examples_section_shows_a_few_products_per_group_and_links_the_full_file(tmp_path: Path):
    section = samples.render_examples_section("atm", rows_for_report(tmp_path), examples=2, max_groups=10)
    assert section.startswith(samples.REPORT_START) and section.rstrip().endswith(samples.REPORT_END)
    assert "[`product_samples.csv`](../audit-output/atm/product_samples.csv)" in section
    assert "| Node | `inventory_version_mismatch` | `urn:a:b:n::1.0` | 5 | `urn:a:b:c:n0::1.0`<br>`urn:a:b:c:n1::1.0` |" in section
    assert "| Node | `reloaded_after_collection` | `urn:a:b:r::1.0` | 2 |" in section
    assert "n2::1.0" not in section  # only two examples per group


def test_the_examples_section_limits_the_number_of_groups_and_handles_none(tmp_path: Path):
    rows = rows_for_report(tmp_path)
    one_group = samples.render_examples_section("atm", rows, examples=3, max_groups=1)
    assert "largest problem groups of 2" in one_group and "reloaded_after_collection" not in one_group
    assert "No product needs attention." in samples.render_examples_section("ppi", [])


def test_update_node_report_inserts_before_reproduce_and_then_replaces(tmp_path: Path):
    report = tmp_path / "atm.md"
    report.write_text("# atm\n\n## Details\n\ntext\n\n## Reproduce\n\ncommands\n", encoding="utf-8")
    first = samples.render_examples_section("atm", rows_for_report(tmp_path), examples=1)
    samples.update_node_report(report, first)
    text = report.read_text(encoding="utf-8")
    assert text.index("## Details") < text.index("## Example products") < text.index("## Reproduce")
    second = samples.render_examples_section("atm", rows_for_report(tmp_path), examples=2)
    samples.update_node_report(report, second)
    updated = report.read_text(encoding="utf-8")
    assert updated.count("## Example products") == 1 and "n1::1.0" in updated
    assert updated.endswith("commands\n")


def test_update_node_report_appends_when_there_is_no_reproduce_heading(tmp_path: Path):
    report = tmp_path / "atm.md"
    report.write_text("# atm\n\ntext\n", encoding="utf-8")
    samples.update_node_report(report, samples.render_examples_section("atm", rows_for_report(tmp_path)))
    assert report.read_text(encoding="utf-8").rstrip().endswith(samples.REPORT_END)


def test_main_updates_the_reports_that_exist(tmp_path: Path):
    audits = tmp_path / "audits"
    reports = tmp_path / "reports"
    reports.mkdir()
    for node in ("a", "b"):
        (audits / node).mkdir(parents=True)
        write_csv(audits / node / "unprocessed_products.csv.gz", [row(f"urn:{node}:b:c:p::1.0", "stale_stamp")])
    (reports / "a.md").write_text("# a\n\n## Reproduce\n", encoding="utf-8")  # no b.md: skipped
    args = ["--audits-dir", str(audits), "--output-dir", str(tmp_path / "out"), "--report-dir", str(reports)]
    assert samples.main(args) == 0
    assert "## Example products" in (reports / "a.md").read_text(encoding="utf-8")
    assert not (reports / "b.md").exists()
