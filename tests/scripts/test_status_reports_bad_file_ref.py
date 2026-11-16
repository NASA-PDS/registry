"""Tests for the invalid ``file_ref`` reports of ``generate_registry_status_reports`` (no registry access)."""
from __future__ import annotations

import json
from pathlib import Path

import generate_registry_status_reports as reports
import pytest

NODE = "ops:Harvest_Info/ops:node_name"
STATUS = "ops:Tracking_Meta/ops:archive_status"
LABEL = "ops:Label_File_Info/ops:file_ref"
DATA = "ops:Data_File_Info/ops:file_ref"
CONF = Path(__file__).resolve().parents[2] / "conf" / "status"


def hit(lidvid: str, status: str = "archived", node: str = "PDS_X", **refs: object) -> dict:
    source = {"lidvid": lidvid, NODE: [node], STATUS: status, "product_class": "Product_Observational"}
    source.update({LABEL if k == "label" else DATA: v for k, v in refs.items()})
    return {"_source": source}


def response(*hits: dict) -> dict:
    return {"hits": {"hits": list(hits)}}


# ── extraction ────────────────────────────────────────────────────────────────


def test_extract_reports_each_offending_value_and_skips_https_null_and_empty():
    rows = reports.extract_bad_file_ref_rows(
        response(hit("urn:a:b:c:p::1.0", label="/tmp/p.xml", data=["https://ok/p.tab", "file:///x.tab", "null", ""]))
    )
    assert [(r[4], r[5]) for r in rows] == [("Label_File_Info", "/tmp/p.xml"), ("Data_File_Info", "file:///x.tab")]


@pytest.mark.parametrize("status", ["staged", "archived"])
def test_extract_reports_s3_values_whatever_the_archive_status(status: str):
    rows = reports.extract_bad_file_ref_rows(
        response(hit("urn:a:b:c:p::1.0", status, label="s3://bucket/p.xml", data="/local/p.tab"))
    )
    assert [r[5] for r in rows] == ["s3://bucket/p.xml", "/local/p.tab"]


# ── grouping ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "lidvid, expected",
    [
        ("urn:nasa:pds:bundle:coll:prod::1.0", ("urn:nasa:pds:bundle", "urn:nasa:pds:bundle:coll")),
        ("urn:nasa:pds:bundle:coll:prod:more::2.0", ("urn:nasa:pds:bundle", "urn:nasa:pds:bundle:coll")),
        (
            "urn:nasa:pds-ama:sample_bundle:document:file::1.0",
            ("urn:nasa:pds-ama:sample_bundle", "urn:nasa:pds-ama:sample_bundle:document"),
        ),
        ("urn:nasa:pds:bundle:product::1.0", ("urn:nasa:pds:bundle", "")),
        ("tbd:xml_schema:img-xml_schema::1.0", ("tbd", "tbd:xml_schema")),
        ("urn:nasa:pds::1.0", ("(unknown)", "(unknown)")),
        ("loner::1.0", ("(unknown)", "(unknown)")),
    ],
)
def test_derive_bundle_and_collection(lidvid, expected):
    assert reports.derive_bundle_and_collection(lidvid) == expected


@pytest.mark.parametrize(
    "value, kind",
    [
        ("s3://b/k", "s3://"),
        ("http://h/p", "http://"),
        ("/data/p.xml", "local path"),
        ("C:\\data\\p.xml", "local path"),
        ("C:/data/p.xml", "local path"),
        ("data/p.xml", "relative path"),
    ],
)
def test_file_ref_kind(value, kind):
    assert reports.file_ref_kind(value) == kind


def test_group_summarises_products_per_bundle_collection_and_status():
    rows = reports.extract_bad_file_ref_rows(
        response(
            hit("urn:nasa:pds:b1:c1:p1::1.0", label="/l/p1.xml", data="/l/p1.tab"),
            hit("urn:nasa:pds:b1:c1:p2::1.0", label="/l/p2.xml"),
            hit("urn:nasa:pds:b1:c1:p3::1.0", "staged", label="/l/p3.xml"),
            hit("urn:nasa:pds:b1:c2:q1::1.0", "archived", node="PDS_Y", label="s3://k/q1.xml"),
        )
    )
    grouped = reports.group_bad_file_ref_rows(rows)
    assert [r[:6] for r in grouped] == [
        ("PDS_X", "urn:nasa:pds:b1", "urn:nasa:pds:b1:c1", "archived", 2, 3),  # largest first: 2 products, 3 values
        ("PDS_X", "urn:nasa:pds:b1", "urn:nasa:pds:b1:c1", "staged", 1, 1),
        ("PDS_Y", "urn:nasa:pds:b1", "urn:nasa:pds:b1:c2", "archived", 1, 1),
    ]
    first = grouped[0]
    assert first[6] == "local path"
    assert first[7] == "Data_File_Info; Label_File_Info"
    assert first[8:] == ("urn:nasa:pds:b1:c1:p1::1.0", ".../p1.xml")  # the lowest LIDVID is the example, masked
    assert grouped[2][6] == "s3://"


@pytest.mark.parametrize(
    "value, masked",
    [
        ("/home/someone/PDS/tmp/sample/doc/collection.xml", ".../collection.xml"),
        ("/Users/someone/test/harvest/p.xml", ".../p.xml"),
        ("C:\\data\\run\\p.xml", ".../p.xml"),
        ("s3://some-bucket/path/to/p.xml", "s3://.../p.xml"),
        ("file:///mnt/data/p.xml", "file://.../p.xml"),
        ("relative/dir/p.xml", ".../p.xml"),
        ("p.xml", ".../p.xml"),
        ("/trailing/slash/", ".../slash"),
    ],
)
def test_mask_file_ref_keeps_only_the_scheme_and_file_name(value, masked):
    assert reports.mask_file_ref(value) == masked


def test_masked_rows_expose_no_directories():
    rows = reports.extract_bad_file_ref_rows(
        response(hit("urn:a:b:c:p::1.0", label="/home/someone/secret/dir/p.xml", data="s3://bucket/dir/p.tab"))
    )
    masked = reports.mask_bad_file_ref_rows(rows)
    assert [r[5] for r in masked] == [".../p.xml", "s3://.../p.tab"]
    assert masked[0][:5] == rows[0][:5]
    for row in masked + reports.group_bad_file_ref_rows(rows):
        assert not any("someone" in str(cell) or "secret" in str(cell) or "bucket" in str(cell) for cell in row)


def test_group_of_nothing_is_empty():
    assert reports.group_bad_file_ref_rows([]) == []


def test_grouped_counts_sum_the_products_column_per_node(tmp_path: Path):
    path = tmp_path / "products.csv"
    rows = [
        ("PDS_X", "b", "c1", "archived", 5, 7, "local path", "Label_File_Info", "l", "v"),
        ("PDS_X", "b", "c2", "staged", 3, 3, "local path", "Label_File_Info", "l", "v"),
        ("PDS_Y", "b", "c3", "archived", 2, 2, "s3://", "Data_File_Info", "l", "v"),
    ]
    reports.write_rows_to_csv(rows, path, header=reports.BAD_FILE_REF_GROUP_HEADER)
    assert reports._count_grouped_products_by_node(path) == {"PDS_X": 8, "PDS_Y": 2}
    assert reports._count_grouped_products_by_node(tmp_path / "missing.csv") == {}


def test_per_value_counts_count_each_lidvid_once_per_node(tmp_path: Path):
    path = tmp_path / "bundles.csv"
    rows = [("PDS_X", "urn:a:b::1.0", "Product_Bundle", "archived", "Label_File_Info", "/a")] * 2
    reports.write_rows_to_csv(rows, path, header=reports.BAD_FILE_REF_HEADER)
    assert reports._count_distinct_lidvids_by_node(path) == {"PDS_X": 1}


# ── query files ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ["bundles", "collections", "products"])
def test_query_files_accept_only_https_on_both_file_ref_fields(name: str):
    query = json.loads((CONF / f"bad_file_ref_{name}_per_node.json").read_text(encoding="utf-8"))
    should = next(f["bool"]["should"] for f in query["query"]["bool"]["filter"] if "should" in f.get("bool", {}))
    assert {field: spec["value"] for clause in should for field, spec in clause["regexp"].items()} == {
        LABEL: "~(https://.*)",
        DATA: "~(https://.*)",
    }
    assert "staged" not in json.dumps(query)
