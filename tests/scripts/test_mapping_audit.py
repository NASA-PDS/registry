"""Tests for ``unprocessed_audit.mapping_audit`` and ``audit_index_mappings`` (no network)."""

from __future__ import annotations

import csv
from pathlib import Path

import audit_index_mappings as cli
import pytest
from unprocessed_audit import mapping_audit as ma
from unprocessed_audit.model import RegistryQueryError

SUPERSEDED = "ops:Provenance/ops:superseded_by"
HARVEST = "ops:Harvest_Info/ops:harvest_date_time"


def response(properties: dict, dynamic: str | None = "false", concrete: str = "i-000001") -> dict:
    mappings: dict = {"properties": properties}
    if dynamic is not None:
        mappings["dynamic"] = dynamic
    return {concrete: {"mappings": mappings}}


def props(**types: str) -> dict:
    """Build mapping properties; keyword arguments use ``__`` for ``/`` and ``_`` stays literal."""
    return {name.replace("__", "/"): {"type": type_} for name, type_ in types.items()}


def index(name: str, fields: dict[str, str], dynamic: str = "false", group: str = ma.GROUP_REGISTRY) -> ma.IndexMapping:
    return ma.IndexMapping(name=name, node=name.split("-")[0], group=group, fields=fields, dynamic=dynamic)


# ── flatten ───────────────────────────────────────────────────────────────────


def test_flatten_keeps_registry_field_names_whole_and_walks_nested_properties():
    body = response(
        {
            SUPERSEDED: {"type": "keyword"},
            "nested": {"properties": {"inner": {"type": "long"}}},
            "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        }
    )
    mapping = ma.flatten_mapping(body, "atm-registry", "atm", "registry")
    assert mapping.fields == {
        SUPERSEDED: "keyword",
        "nested": "object",
        "nested.inner": "long",
        "title": "text",
        "title.keyword": "keyword",
    }
    assert mapping.dynamic == "false"


def test_flatten_defaults_dynamic_to_true_and_merges_concrete_indices():
    body = {**response({"a": {"type": "keyword"}}, dynamic=None), **response({"a": {"type": "long"}, "b": {"type": "date"}}, concrete="i-2")}
    mapping = ma.flatten_mapping(body, "x-registry", "x", "registry")
    assert mapping.fields == {"a": "keyword", "b": "date"}
    assert mapping.dynamic == "true"


def test_flatten_ignores_malformed_entries():
    mapping = ma.flatten_mapping({"i": "oops", "j": {"mappings": {"properties": {"a": "oops", "b": {"type": "keyword"}}}}}, "x", "x", "registry")
    assert mapping.fields == {"b": "keyword"}


# ── analyze ───────────────────────────────────────────────────────────────────


def group(missing_in: str | None = None, **overrides: dict[str, str]) -> list[ma.IndexMapping]:
    base = {SUPERSEDED: "keyword", HARVEST: "date", "pds:Thing/pds:a": "keyword", "lid": "keyword"}
    mappings = []
    for name in ("a-registry", "b-registry", "c-registry", "d-registry", "e-registry"):
        fields = dict(base)
        fields.update(overrides.get(name, {}))
        if name == missing_in:
            fields.pop(SUPERSEDED)
        mappings.append(index(name, fields))
    return mappings


def test_identical_indices_have_no_discrepancies():
    assert ma.analyze(group()) == []


def test_a_missing_ops_field_is_an_error():
    found = ma.analyze(group(missing_in="c-registry"))
    assert len(found) == 1
    d = found[0]
    assert (d.index, d.field, d.kind, d.severity) == ("c-registry", SUPERSEDED, ma.Kind.MISSING_FIELD, ma.Severity.ERROR)
    assert (d.expected, d.actual, d.present_in, d.total) == ("keyword", ma.NO_TYPE, 4, 5)


def test_a_missing_data_dictionary_field_is_a_warning_and_a_core_top_level_field_an_error():
    mappings = group()
    del mappings[1].fields["pds:Thing/pds:a"]
    del mappings[2].fields["lid"]
    by_field = {d.field: d for d in ma.analyze(mappings)}
    assert by_field["pds:Thing/pds:a"].severity is ma.Severity.WARNING
    assert by_field["lid"].severity is ma.Severity.ERROR


def test_a_field_on_few_indices_is_node_specific_and_not_reported():
    mappings = group()
    mappings[0].fields["nh:Only/nh:here"] = "keyword"
    assert ma.analyze(mappings) == []


def test_the_presence_threshold_decides_what_is_expected_everywhere():
    mappings = group()
    for m in mappings[:3]:
        m.fields["x:Some/x:field"] = "keyword"  # 3 of 5 = 60 %
    assert ma.analyze(mappings, presence_threshold=0.8) == []
    assert {d.index for d in ma.analyze(mappings, presence_threshold=0.5)} == {"d-registry", "e-registry"}


def test_a_type_conflict_is_an_error_on_the_minority_index():
    found = ma.analyze(group(**{"e-registry": {HARVEST: "keyword"}}))
    assert len(found) == 1
    assert (found[0].index, found[0].kind, found[0].severity) == ("e-registry", ma.Kind.TYPE_MISMATCH, ma.Severity.ERROR)
    assert (found[0].expected, found[0].actual) == ("date", "keyword")


def test_a_type_tie_goes_to_the_alphabetically_first_type_deterministically():
    mappings = [index("a-registry", {"f": "long"}), index("b-registry", {"f": "keyword"})]
    found = ma.analyze(mappings)
    assert [(d.index, d.expected) for d in found] == [("a-registry", "keyword")]


def test_a_different_dynamic_setting_is_a_warning():
    mappings = group()
    mappings[3].dynamic = "true"
    found = ma.analyze(mappings)
    assert [(d.index, d.kind, d.severity, d.expected, d.actual) for d in found] == [
        ("d-registry", ma.Kind.DYNAMIC_MISMATCH, ma.Severity.WARNING, "false", "true")
    ]


def test_a_missing_index_is_reported_and_left_out_of_the_comparison():
    mappings = group()
    mappings.append(ma.IndexMapping("f-registry-refs", "f", ma.GROUP_REFS, present=False))
    found = ma.analyze(mappings)
    assert [(d.index, d.kind) for d in found] == [("f-registry-refs", ma.Kind.INDEX_MISSING)]


def test_a_group_with_one_index_has_nothing_to_compare():
    assert ma.analyze([index("a-registry", {"x": "keyword"})]) == []


def test_groups_are_compared_separately():
    refs = [index(f"{n}-registry-refs", {"collection_lidvid": "keyword"}, group=ma.GROUP_REFS) for n in "ab"]
    assert ma.analyze(group() + refs) == []


# ── reading ───────────────────────────────────────────────────────────────────


class FakeClient:
    def __init__(self, responses: dict[str, dict | Exception]) -> None:
        self.responses = responses
        self.requested: list[str] = []
        self.documents: dict[str, int] = {}

    def get_mapping(self, name: str) -> dict:
        self.requested.append(name)
        result = self.responses[name]
        if isinstance(result, Exception):
            raise result
        return result

    def count(self, name: str, body: dict) -> int:
        return self.documents[name]


def test_read_mappings_requests_every_node_and_group():
    client = FakeClient({
        "a-registry": response(props(lid="keyword")),
        "a-registry-refs": response(props(collection_lidvid="keyword")),
    })  # fmt: skip
    mappings = ma.read_mappings(client, ["a"], [ma.GROUP_REGISTRY, ma.GROUP_REFS])  # type: ignore[arg-type]
    assert [(m.name, m.group) for m in mappings] == [("a-registry", "registry"), ("a-registry-refs", "registry-refs")]


def test_the_refs_index_of_a_concrete_products_index_is_named_after_the_tenant():
    client = FakeClient({
        "temp-atm-registry": response(props(lid="keyword")),
        "atm-registry-refs": response(props(collection_lidvid="keyword")),
    })  # fmt: skip
    mappings = ma.read_mappings(client, ["temp-atm"], [ma.GROUP_REGISTRY, ma.GROUP_REFS])  # type: ignore[arg-type]
    assert client.requested == ["temp-atm-registry", "atm-registry-refs"]
    assert all(m.present for m in mappings)


def test_a_missing_refs_index_is_tolerated_but_a_missing_registry_index_is_not():
    not_found = RegistryQueryError("Registry request to x/_mapping failed: HTTP 404: index_not_found_exception")
    client = FakeClient({"a-registry": response(props(lid="keyword")), "a-registry-refs": not_found})
    mappings = ma.read_mappings(client, ["a"], [ma.GROUP_REGISTRY, ma.GROUP_REFS])  # type: ignore[arg-type]
    assert mappings[1].present is False
    with pytest.raises(RegistryQueryError):
        ma.read_mappings(FakeClient({"a-registry": not_found}), ["a"], [ma.GROUP_REGISTRY])  # type: ignore[arg-type]


def test_other_refs_errors_are_not_swallowed_and_an_empty_mapping_is_rejected():
    boom = RegistryQueryError("Registry request failed: HTTP 500")
    with pytest.raises(RegistryQueryError, match="HTTP 500"):
        ma.read_mappings(FakeClient({"a-registry-refs": boom}), ["a"], [ma.GROUP_REFS])  # type: ignore[arg-type]
    with pytest.raises(RegistryQueryError, match="came back empty"):
        ma.read_mappings(FakeClient({"a-registry": {}}), ["a"], [ma.GROUP_REGISTRY])  # type: ignore[arg-type]


# ── output ────────────────────────────────────────────────────────────────────


def test_csv_outputs(tmp_path: Path):
    mappings = group(missing_in="c-registry")
    found = ma.analyze(mappings)
    assert ma.write_discrepancies_csv(tmp_path / "d.csv", found) == 1
    with (tmp_path / "d.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["index"] == "c-registry" and rows[0]["kind"] == "missing_field" and rows[0]["severity"] == "error"

    assert ma.write_matrix_csv(tmp_path / "m.csv", mappings) == 4
    with (tmp_path / "m.csv").open(encoding="utf-8", newline="") as handle:
        matrix = {r["field"]: r for r in csv.DictReader(handle)}
    assert matrix[SUPERSEDED]["c-registry"] == ma.NO_TYPE
    assert matrix[SUPERSEDED]["a-registry"] == "keyword"


def test_summary_names_the_field_and_the_indices_missing_it():
    mappings = group(missing_in="c-registry")
    text = ma.render_summary(mappings, ma.analyze(mappings), 0.8)
    assert "1 errors, 0 warnings" in text
    assert f"| error | registry | `{SUPERSEDED}` | keyword | c-registry |" in text
    assert "| registry | c-registry | 3 | false | 1 | 0 | 0 |" in text


def test_summary_of_a_clean_run_has_no_discrepancy_sections():
    text = ma.render_summary(group(), [], 0.8)
    assert "**0** (0 errors, 0 warnings)" in text
    assert "Fields missing" not in text


# ── CLI ───────────────────────────────────────────────────────────────────────


def install(monkeypatch: pytest.MonkeyPatch, responses: dict[str, dict | Exception]) -> FakeClient:
    client = FakeClient(responses)
    monkeypatch.setattr(cli, "make_registry_auth", lambda: object())
    monkeypatch.setattr(cli, "registry_endpoint_from_env", lambda: "https://example.invalid")
    monkeypatch.setattr(cli, "RegistryClient", lambda *a, **k: client)
    monkeypatch.setattr(cli, "discover_nodes", lambda c: ["a", "b"])
    return client


def mappings_for(missing: bool) -> dict[str, dict]:
    full = response({SUPERSEDED: {"type": "keyword"}, "lid": {"type": "keyword"}})
    partial = response({"lid": {"type": "keyword"}})
    return {f"{n}-registry": partial if missing and n == "b" else full for n in NODES}


NODES = ["a", "b", "c", "d", "e"]
NODE_ARGS = [arg for node in NODES for arg in ("--node", node)]


def test_main_writes_the_outputs_and_exits_zero_without_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    install(monkeypatch, mappings_for(missing=True))
    assert cli.main(["--output-dir", str(tmp_path / "out"), *NODE_ARGS]) == 0
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [
        "mapping_discrepancies.csv", "mapping_matrix.csv", "mapping_summary.md"
    ]  # fmt: skip
    assert "1 error-level discrepancies" in capsys.readouterr().out


def test_main_check_exits_two_on_an_error_and_zero_when_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    install(monkeypatch, mappings_for(missing=True))
    assert cli.main(["--output-dir", str(tmp_path / "bad"), *NODE_ARGS, "--check"]) == 2
    install(monkeypatch, mappings_for(missing=False))
    assert cli.main(["--output-dir", str(tmp_path / "good"), *NODE_ARGS, "--check"]) == 0


KNOWN = ["--known-node", "a", "--known-node", "b"]


def test_main_discovers_nodes_when_none_are_given(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    full = mappings_for(False)["a-registry"]
    client = install(monkeypatch, {"a-registry": full, "b-registry": full})
    assert cli.main(["--output-dir", str(tmp_path / "out"), *KNOWN]) == 0
    assert client.requested == ["a-registry", "b-registry"]


def test_main_include_refs_reads_the_refs_indices(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    refs = response({"collection_lidvid": {"type": "keyword"}})
    client = install(monkeypatch, {**mappings_for(False), "a-registry-refs": refs, "b-registry-refs": refs})
    assert cli.main(["--output-dir", str(tmp_path / "out"), "--include-refs", *KNOWN]) == 0
    assert "a-registry-refs" in client.requested


def test_main_returns_one_on_a_registry_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    install(monkeypatch, {"a-registry": RegistryQueryError("HTTP 500"), "b-registry": {}})
    assert cli.main(["--output-dir", str(tmp_path / "out"), *KNOWN]) == 1


# ── possibly stale indices ────────────────────────────────────────────────────


def test_describe_possibly_stale_gathers_documents_fields_and_refs_presence():
    not_found = RegistryQueryError("HTTP 404: index_not_found_exception")
    client = FakeClient({"scratch-registry": response(props(lidvid="keyword", vid="float")), "scratch-registry-refs": not_found})
    client.documents["scratch-registry"] = 5_000_000
    found = ma.describe_possibly_stale(client, ["scratch"])  # type: ignore[arg-type]
    assert found == [ma.StaleIndex("scratch-registry", "scratch", 5_000_000, 2, False)]


def test_discovered_non_tenant_indices_are_reported_not_compared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    full = mappings_for(False)["a-registry"]
    client = install(monkeypatch, {
        "a-registry": full, "b-registry": full,
        "scratch-registry": response(props(lidvid="keyword")),
        "scratch-registry-refs": RegistryQueryError("HTTP 404: index_not_found_exception"),
    })  # fmt: skip
    client.documents["scratch-registry"] = 1234
    monkeypatch.setattr(cli, "discover_nodes", lambda c: ["a", "b", "scratch"])

    assert cli.main(["--output-dir", str(tmp_path / "out"), "--check", *KNOWN]) == 0  # no discrepancy from scratch

    out = tmp_path / "out"
    summary = (out / "mapping_summary.md").read_text(encoding="utf-8")
    assert "## Possibly stale or test indices" in summary
    assert "| scratch-registry | 1,234 | 1 | no |" in summary
    assert "scratch-registry |" not in summary.split("## Per index")[1]  # left out of the comparison
    with (out / "mapping_possibly_stale.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [{"index": "scratch-registry", "node": "scratch", "documents": "1234", "mapped_fields": "1", "has_refs_index": "false"}]
    assert "candidates for cleanup" in capsys.readouterr().out


def test_explicitly_named_nodes_are_compared_even_when_not_tenants(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    full = mappings_for(False)["a-registry"]
    install(monkeypatch, {"scratch-registry": full, "a-registry": full})
    assert cli.main(["--output-dir", str(tmp_path / "out"), "--node", "scratch", "--node", "a"]) == 0
    assert not (tmp_path / "out" / "mapping_possibly_stale.csv").exists()


def test_a_run_without_stale_indices_writes_no_stale_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    full = mappings_for(False)["a-registry"]
    install(monkeypatch, {"a-registry": full, "b-registry": full})
    assert cli.main(["--output-dir", str(tmp_path / "out"), *KNOWN]) == 0
    assert not (tmp_path / "out" / "mapping_possibly_stale.csv").exists()
    assert "Possibly stale" not in (tmp_path / "out" / "mapping_summary.md").read_text(encoding="utf-8")


def test_presence_threshold_must_be_in_range(tmp_path: Path):
    with pytest.raises(SystemExit):
        cli.parse_args(["--output-dir", str(tmp_path), "--presence-threshold", "0"])
    with pytest.raises(SystemExit):
        cli.parse_args(["--output-dir", str(tmp_path), "--presence-threshold", "1.5"])
