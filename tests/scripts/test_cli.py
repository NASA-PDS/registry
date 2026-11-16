"""End-to-end tests for ``audit_unprocessed_products.run_audit`` using a fake registry."""

from __future__ import annotations

import csv
import gzip
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Any

import audit_unprocessed_products as cli
import pytest
from unprocessed_audit.model import Candidate
from unprocessed_audit.model import Collection
from unprocessed_audit.model import RefsCoverage
from unprocessed_audit.model import RegistryQueryError

NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

C_OK = "urn:nasa:pds:b1:ok::1.0"  # processed
C_EMPTY = "urn:nasa:pds:b2:empty::1.0"  # stamped with empty refs, has a bundle
C_LATE = "urn:nasa:pds:b3:late::1.0"  # never stamped, harvested 5 days ago
BUNDLE_EMPTY = "urn:nasa:pds:b2::1.0"


def ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


def collection(lidvid: str, stamp: str | None, refs: list[str], harvest_days_ago: float, node: str = "atm") -> Collection:
    return Collection(
        lidvid=lidvid,
        lid=lidvid.split("::")[0],
        node=node,
        stamp=stamp,
        ancestor_refs=refs,
        harvest=ago(harvest_days_ago),
    )


def product(name: str, collection_lid: str, harvest_days_ago: float, klass: str = "Product_Observational") -> Candidate:
    lid = f"{collection_lid}:{name}"
    return Candidate(
        lidvid=lid + "::1.0",
        lid=lid,
        product_class=klass,
        node="atm",
        stamp=None,
        has_ancestor_refs=False,
        harvest=ago(harvest_days_ago),
    )


class FakeRegistry:
    """Replaces the registry functions that ``run_audit`` calls."""

    def __init__(self) -> None:
        self.collections = [
            collection(C_OK, "7", ["urn:nasa:pds:b1::1.0"], 10),
            collection(C_EMPTY, "7", [], 10),
            collection(C_LATE, None, [], 5),
        ]
        self.pages = [
            [
                product("reloaded", "urn:nasa:pds:b1:ok", 3),  # in refs, collection older
                product("missing", "urn:nasa:pds:b1:ok", 20),  # not in refs, past grace
                product("under_late", "urn:nasa:pds:b3:late", 2),
            ],
            [
                product("orphan_new", "urn:nasa:pds:b9:gone", 1),
                product("orphan_old", "urn:nasa:pds:b9:gone", 30),
                product("svc", "urn:nasa:pds:b4:ctx", 2, klass="Product_Service"),
            ],
        ]
        self.lookup_calls: list[list[str]] = []
        self.lid_lookup_calls: list[list[str]] = []
        self.listed: dict[str, str] = {}  # product LID -> product LIDVID that the refs of C_OK list
        self.coverage_calls: list[str] = []
        self.bundle_calls: list[list[str]] = []

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cli, "discover_nodes", lambda client: ["atm"])
        monkeypatch.setattr(cli, "iter_collections", lambda client, nodes: iter(self.collections))
        monkeypatch.setattr(cli, "find_bundles", self.find_bundles)
        monkeypatch.setattr(cli, "iter_candidate_pages", self.iter_candidate_pages)
        monkeypatch.setattr(cli, "lookup_refs", self.lookup_refs)
        monkeypatch.setattr(cli, "lookup_refs_by_lid", self.lookup_refs_by_lid)
        monkeypatch.setattr(cli, "get_refs_coverage", self.get_refs_coverage)

    def find_bundles(self, client: object, lids: list[str], nodes: list[str]) -> dict[str, list[str]]:
        self.bundle_calls.append(list(lids))
        return {"urn:nasa:pds:b2:empty": [BUNDLE_EMPTY]}

    def iter_candidate_pages(
        self, client: object, nodes: list[str], version: int, page_size: int = 10000, max_products: int | None = None
    ) -> Any:
        self.max_products = max_products
        yield from self.pages

    def lookup_refs(self, client: object, lidvids: list[str], nodes: list[str]) -> dict[str, str]:
        self.lookup_calls.append(list(lidvids))
        return {lv: C_OK for lv in lidvids if "reloaded" in lv}

    def lookup_refs_by_lid(self, client: object, lids: list[str], nodes: list[str]) -> dict[str, list[tuple[str, str]]]:
        self.lid_lookup_calls.append(list(lids))
        return {lid: [(self.listed[lid], C_OK)] for lid in lids if lid in self.listed}

    def get_refs_coverage(self, client: object, coll: Collection, nodes: list[str], version: int) -> RefsCoverage:
        self.coverage_calls.append(coll.lidvid)
        return RefsCoverage(refs_count=1, member_count=4, stamped_member_count=1)


def make_args(tmp_path: Path, *extra: str) -> Any:
    return cli.parse_args(["--output-dir", str(tmp_path / "out"), *extra])


def read_rows(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:  # type: ignore[operator]
        return list(csv.DictReader(handle))


@pytest.fixture()
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeRegistry:
    registry = FakeRegistry()
    registry.install(monkeypatch)
    return registry


def test_parse_args_defaults(tmp_path: Path) -> None:
    args = make_args(tmp_path)
    assert args.collection_grace_days == 1
    assert args.product_grace_days == 7
    assert args.ancestry_version == 7
    assert args.max_coverage_collections == 200
    assert args.timeout == 60
    assert args.node is None
    assert args.gzip is False
    assert make_args(tmp_path, "--node", "atm", "--node", "geo").node == ["atm", "geo"]


def test_output_dir_is_required() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args([])


def test_run_audit_end_to_end(tmp_path: Path, fake: FakeRegistry) -> None:
    result = cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]

    out = tmp_path / "out"
    assert sorted(p.name for p in out.iterdir()) == [
        "anomalous_collections.txt",
        "collections.csv",
        "metrics.json",
        "summary.md",
        "unprocessed_products.csv",
    ]

    rows = read_rows(out / "unprocessed_products.csv")
    assert len(rows) == 6
    by_name = {row["lidvid"].split("::")[0].split(":")[-1]: row for row in rows}
    assert by_name["reloaded"]["rule"] == "reloaded_after_collection"
    assert by_name["reloaded"]["in_refs"] == "true"
    assert by_name["reloaded"]["collection_lidvid"] == C_OK
    assert by_name["missing"]["rule"] == "refs_missing"
    assert by_name["missing"]["in_refs"] == "false"
    assert by_name["missing"]["severity"] == "anomalous"
    assert by_name["under_late"]["rule"] == "collection_overdue"
    assert by_name["under_late"]["collection_lidvid"] == C_LATE
    assert by_name["orphan_new"]["rule"] == "collection_not_loaded_pending"
    assert by_name["orphan_old"]["rule"] == "collection_not_loaded_overdue"
    assert by_name["svc"]["rule"] == "no_parent_by_design"
    assert by_name["svc"]["severity"] == "expected"

    tally = result.tally
    assert tally.examined == 6
    assert tally.anomalous == 4
    assert tally.expected == 2

    # refs were looked up only for products whose collection is processed, once per page
    assert fake.lookup_calls == [["urn:nasa:pds:b1:ok:reloaded::1.0", "urn:nasa:pds:b1:ok:missing::1.0"]]

    # bundles were looked up for stamped-with-empty-refs collections only
    assert fake.bundle_calls == [["urn:nasa:pds:b2:empty"]]

    # anomalous collections: C_OK (2 products) and C_LATE (1); coverage for both
    assert set(tally.collections) == {C_OK, C_LATE}
    assert sorted(fake.coverage_calls) == sorted([C_OK, C_LATE])
    assert fake.coverage_calls[0] == C_OK  # worst first
    # collections rooting anomalies plus the stamped-empty collection that has a bundle (C_EMPTY), sorted
    assert (out / "anomalous_collections.txt").read_text(encoding="utf-8").splitlines() == [C_OK, C_EMPTY, C_LATE]

    coll_rows = {r["collection_lidvid"]: r for r in read_rows(out / "collections.csv")}
    assert set(coll_rows) == {C_OK, C_EMPTY, C_LATE}
    assert coll_rows[C_OK]["state"] == "processed"
    assert coll_rows[C_OK]["anomalous_product_count"] == "2"
    assert coll_rows[C_OK]["coverage_note"] == "refs missing for 3 members (refs never written)"
    assert coll_rows[C_EMPTY]["state"] == "stamped_empty_refs"
    assert coll_rows[C_EMPTY]["bundle_lidvids"] == BUNDLE_EMPTY
    assert coll_rows[C_EMPTY]["anomalous_product_count"] == "0"
    assert coll_rows[C_EMPTY]["refs_count"] == ""
    assert coll_rows[C_LATE]["state"] == "unprocessed_overdue"

    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert summary == result.summary
    assert "Candidates examined: **6**" in summary
    assert "Anomalous (need attention): **4**" in summary
    assert "## Anomalous collections" in summary
    assert "## Stamped collections with empty refs" in summary
    assert BUNDLE_EMPTY in summary
    assert "## Orphans" in summary
    assert "urn:nasa:pds:b9:gone" in summary
    assert "Change since previous run" not in summary
    assert result.diff is None


def test_run_audit_reports_products_the_inventory_does_not_list(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unprocessed_audit.inventory import parse_inventory

    inventories: list[str] = []

    def provider(coll: Collection) -> Any:
        inventories.append(coll.lidvid)
        return parse_inventory(["P,urn:nasa:pds:b1:ok:somebody_else::1.0"])

    monkeypatch.setattr(cli, "make_inventory_session", lambda: object())
    monkeypatch.setattr(cli, "InventoryCache", lambda session, timeout, **kwargs: provider)
    cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    rows = {r["lidvid"].split("::")[0].split(":")[-1]: r for r in read_rows(tmp_path / "out" / "unprocessed_products.csv")}
    assert rows["missing"]["rule"] == "not_in_collection_inventory"
    assert rows["missing"]["severity"] == "anomalous"
    assert rows["reloaded"]["rule"] == "reloaded_after_collection"  # listed in refs: inventory not consulted
    assert set(inventories) == {C_OK}


def test_run_audit_no_inventory_skips_the_downloads(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(session: object, timeout: int) -> Any:
        raise AssertionError("the inventory cache must not be created with --no-inventory")

    monkeypatch.setattr(cli, "InventoryCache", forbidden)
    cli.run_audit(make_args(tmp_path, "--no-inventory"), client=object(), now=NOW)  # type: ignore[arg-type]
    rows = {r["lidvid"].split("::")[0].split(":")[-1]: r for r in read_rows(tmp_path / "out" / "unprocessed_products.csv")}
    assert rows["missing"]["rule"] == "refs_missing"


def test_run_audit_looks_up_unlisted_products_by_lid(tmp_path: Path, fake: FakeRegistry) -> None:
    # Only the product that no refs document lists by LIDVID is looked up by LID, once per page.
    cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    assert fake.lid_lookup_calls == [["urn:nasa:pds:b1:ok:missing"]]


def test_run_audit_flags_inventory_version_mismatch(tmp_path: Path, fake: FakeRegistry) -> None:
    fake.pages = [[product("mismatch", "urn:nasa:pds:b1:ok", 20), product("plain", "urn:nasa:pds:b1:ok", 20)]]
    fake.listed = {"urn:nasa:pds:b1:ok:mismatch": "urn:nasa:pds:b1:ok:mismatch::2.0"}
    cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    rows = {r["lidvid"].split("::")[0].split(":")[-1]: r for r in read_rows(tmp_path / "out" / "unprocessed_products.csv")}
    assert rows["mismatch"]["rule"] == "inventory_version_mismatch"
    assert rows["mismatch"]["severity"] == "anomalous"
    assert rows["mismatch"]["in_refs"] == "false"
    assert "urn:nasa:pds:b1:ok:mismatch::2.0" in rows["mismatch"]["rationale"]
    assert rows["plain"]["rule"] == "refs_missing"


def test_run_audit_attributes_products_to_superseded_collection_versions(tmp_path: Path, fake: FakeRegistry) -> None:
    old = collection("urn:nasa:pds:b5:old::1.0", "7", ["urn:nasa:pds:b5::1.0"], 400)
    old.superseded_by = "urn:nasa:pds:b5:old::2.0"
    new = collection("urn:nasa:pds:b5:old::2.0", "7", ["urn:nasa:pds:b5::1.0"], 1)
    fake.collections += [old, new]
    fake.pages = [[product("legacy", "urn:nasa:pds:b5:old", 20)]]  # product version 1.0 matches the old version
    cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    out = tmp_path / "out"

    row = read_rows(out / "unprocessed_products.csv")[0]
    assert row["rule"] == "refs_missing"
    assert row["collection_lidvid"] == "urn:nasa:pds:b5:old::1.0"
    assert "superseded by urn:nasa:pds:b5:old::2.0" in row["rationale"]

    # A superseded version is not re-harvested, so it is not in the list, but it is in collections.csv.
    assert "urn:nasa:pds:b5:old::1.0" not in (out / "anomalous_collections.txt").read_text(encoding="utf-8")
    coll_rows = {r["collection_lidvid"]: r for r in read_rows(out / "collections.csv")}
    assert coll_rows["urn:nasa:pds:b5:old::1.0"]["superseded_by"] == "urn:nasa:pds:b5:old::2.0"
    assert coll_rows["urn:nasa:pds:b5:old::2.0"]["superseded_by"] == ""
    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert "processed (superseded)" in summary
    assert "superseded collection versions" in summary


def test_stamped_empty_collection_with_a_bundle_is_listed_without_unprocessed_products(
    tmp_path: Path, fake: FakeRegistry
) -> None:
    # C_EMPTY roots no unprocessed product, but its bundle's /members is empty, so it is a re-harvest candidate.
    result = cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    listed = (tmp_path / "out" / "anomalous_collections.txt").read_text(encoding="utf-8").splitlines()
    assert C_EMPTY in listed
    assert C_EMPTY not in result.tally.collections


def test_stamped_empty_collection_without_a_bundle_is_not_listed(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "find_bundles", lambda client, lids, nodes: {})
    cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    assert C_EMPTY not in (tmp_path / "out" / "anomalous_collections.txt").read_text(encoding="utf-8").splitlines()


def test_superseded_collections_are_left_out_of_the_empty_refs_section(tmp_path: Path, fake: FakeRegistry) -> None:
    stale = collection("urn:nasa:pds:b6:stale::1.0", "7", [], 400)
    stale.superseded_by = "urn:nasa:pds:b6:stale::2.0"
    fake.collections.append(stale)
    cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    assert "urn:nasa:pds:b6:stale" not in fake.bundle_calls[0]  # no bundle lookup for it
    summary = (tmp_path / "out" / "summary.md").read_text(encoding="utf-8")
    assert "urn:nasa:pds:b6:stale::1.0" not in summary


def test_run_audit_limits_coverage_queries(tmp_path: Path, fake: FakeRegistry) -> None:
    result = cli.run_audit(make_args(tmp_path, "--max-coverage-collections", "1"), client=object(), now=NOW)  # type: ignore[arg-type]
    assert fake.coverage_calls == [C_OK]
    assert set(result.coverage) == {C_OK}
    assert "not queried" in result.summary


def test_run_audit_gzip_node_and_max_products(tmp_path: Path, fake: FakeRegistry) -> None:
    cli.run_audit(make_args(tmp_path, "--gzip", "--max-products", "10"), client=object(), now=NOW)  # type: ignore[arg-type]
    out = tmp_path / "out"
    assert (out / "unprocessed_products.csv.gz").exists()
    assert not (out / "unprocessed_products.csv").exists()
    assert len(read_rows(out / "unprocessed_products.csv.gz")) == 6
    assert fake.max_products == 10


def test_run_audit_diff_against_previous(tmp_path: Path, fake: FakeRegistry) -> None:
    first = cli.run_audit(make_args(tmp_path / "first"), client=object(), now=NOW)  # type: ignore[arg-type]
    previous = first.paths["products"]
    # drop two products from the previous run and add one that no longer exists
    rows = read_rows(previous)
    kept = [r for r in rows if not r["lidvid"].endswith(("orphan_new::1.0", "svc::1.0"))]
    with open(previous, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(kept)
        gone = dict(rows[0], lidvid="urn:nasa:pds:b1:ok:gone::1.0")
        writer.writerow(gone)

    second = cli.run_audit(make_args(tmp_path / "second", "--previous-csv", str(previous)), client=object(), now=NOW)  # type: ignore[arg-type]
    assert second.diff is not None
    assert (second.diff.new, second.diff.resolved, second.diff.persisting) == (2, 1, 4)
    assert "Change since previous run" in second.summary
    assert "Previous run: unprocessed_products.csv" in second.summary


def test_run_audit_discovers_nodes_when_not_given(tmp_path: Path, fake: FakeRegistry) -> None:
    result = cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    assert "Nodes: atm" in result.summary


def test_run_audit_skips_indices_that_are_not_tenant_nodes(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "discover_nodes", lambda client: ["atm", "scratch"])
    result = cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    assert result.metrics.nodes == ["atm"]
    assert "Possibly stale or test indices (not audited): scratch-registry" in result.summary


def test_run_audit_audits_a_discovered_node_named_by_known_node(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "discover_nodes", lambda client: ["atm", "scratch"])
    result = cli.run_audit(make_args(tmp_path, "--known-node", "atm", "--known-node", "scratch"), client=object(), now=NOW)  # type: ignore[arg-type]
    assert result.metrics.nodes == ["atm", "scratch"]
    assert "Possibly stale" not in result.summary


def test_registry_error_flushes_partial_output(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_pages(*args: object, **kwargs: object) -> Any:
        yield fake.pages[0]
        raise RegistryQueryError("search failed")

    monkeypatch.setattr(cli, "iter_candidate_pages", failing_pages)
    with pytest.raises(RegistryQueryError):
        cli.run_audit(make_args(tmp_path), client=object(), now=NOW)  # type: ignore[arg-type]
    assert len(read_rows(tmp_path / "out" / "unprocessed_products.csv")) == 3


def test_main_returns_one_on_registry_error(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "make_registry_auth", lambda: object())
    monkeypatch.setattr(cli, "registry_endpoint_from_env", lambda: "https://example.invalid")

    def boom(*args: object, **kwargs: object) -> Any:
        raise RegistryQueryError("search failed")

    monkeypatch.setattr(cli, "run_audit", boom)
    assert cli.main(["--output-dir", str(tmp_path / "out")]) == 1


def test_main_success_prints_summary(
    tmp_path: Path, fake: FakeRegistry, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "make_registry_auth", lambda: object())
    monkeypatch.setattr(cli, "registry_endpoint_from_env", lambda: "https://example.invalid")
    assert cli.main(["--output-dir", str(tmp_path / "out"), "--node", "atm"]) == 0
    out = capsys.readouterr().out
    assert "# Unprocessed product audit" in out
    assert " anomalous of 6 candidates" in out


def test_main_rejects_missing_previous_csv(tmp_path: Path) -> None:
    assert cli.main(["--output-dir", str(tmp_path / "out"), "--previous-csv", str(tmp_path / "nope.csv")]) == 1


def test_env_file_does_not_override_shell(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / "creds.env"
    env.write_text('# comment\nexport AUDIT_TEST_ONE="from-file"\nAUDIT_TEST_TWO=file-two\n', encoding="utf-8")
    monkeypatch.setenv("AUDIT_TEST_ONE", "from-shell")
    monkeypatch.delenv("AUDIT_TEST_TWO", raising=False)
    cli.load_credentials(env)
    import os

    assert os.environ["AUDIT_TEST_ONE"] == "from-shell"
    assert os.environ["AUDIT_TEST_TWO"] == "file-two"
    monkeypatch.delenv("AUDIT_TEST_TWO")
