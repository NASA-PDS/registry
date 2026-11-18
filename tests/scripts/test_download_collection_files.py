# flake8: noqa: D101,D102,D103,D107
"""Tests for scripts/download_collection_files.py (no network)."""

import gzip
import hashlib
from pathlib import Path

import download_collection_files as dcf
import pytest
import requests

LIDVID = "urn:nasa:pds:bundle:coll::1.0"
LABEL_URL = "https://data.example.invalid/PDS/data/bundle/coll/coll.xml"
INVENTORY_URL = "https://data.example.invalid/PDS/data/bundle/coll/coll_inventory.csv"
INVENTORY = b"P,urn:nasa:pds:bundle:coll:a::1.0\nP,urn:nasa:pds:bundle:coll:b::1.0\n"
LABEL = b"<Product_Collection><Inventory><records>2</records></Inventory></Product_Collection>"
LABEL_WITH_14_RECORDS = LABEL.replace(b"<records>2<", b"<records>14<")


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


class FakeResponse:
    def __init__(self, body=b"", json_data=None, status=200):
        self._body = body
        self._json = json_data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json

    def iter_content(self, chunk_size=1):
        yield self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    """Serves the API product record and the two files; anything else is a 404."""

    def __init__(self, api_properties=None, files=None, copies=None):
        self.api_properties = api_properties
        self.copies = copies
        self.files = files if files is not None else {LABEL_URL: LABEL, INVENTORY_URL: INVENTORY}
        self.requested = []
        self.params = []

    def get(self, url, params=None, stream=False, timeout=None):
        self.requested.append(url)
        if url.endswith("/products"):
            self.params.append(params)
            if self.api_properties is None:
                return FakeResponse(status=404)
            copies = self.copies if self.copies is not None else [self.api_properties]
            data = [{"id": LIDVID, "metadata": {}, "properties": props} for props in copies]
            return FakeResponse(json_data={"data": data})
        if url in self.files:
            return FakeResponse(body=self.files[url])
        return FakeResponse(status=404)


def api_props(label_md5=None, inventory_md5=None, records="2"):
    return {
        dcf._LABEL_REF: [LABEL_URL],
        dcf._LABEL_MD5: [label_md5 or md5(LABEL)],
        dcf._INVENTORY_REF: [INVENTORY_URL],
        dcf._INVENTORY_MD5: [inventory_md5 or md5(INVENTORY)],
        dcf._RECORDS: [records],
        dcf._HARVEST_TIME: ["2025-04-08T20:36:50.494165Z"],
        dcf._NODE_NAME: ["PDS_ATM"],
    }


def psa_copy():
    """The same collection as registered under another node, with its files on another host."""
    props = api_props()
    props[dcf._NODE_NAME] = ["PSA"]
    props[dcf._LABEL_REF] = ["https://archive.example.invalid/psa/coll/collection.xml"]
    props[dcf._INVENTORY_REF] = ["https://archive.example.invalid/psa/coll/collection_inventory.csv"]
    return props


# ── URL helpers ───────────────────────────────────────────────────────────────


def test_url_helpers():
    assert dcf.url_directory(LABEL_URL) == "https://data.example.invalid/PDS/data/bundle/coll/"
    assert dcf.url_origin(LABEL_URL) == "https://data.example.invalid"
    assert dcf.host_directory("https://host.example.invalid:8443/x/y.xml") == "host.example.invalid_8443"


def test_common_url_prefix():
    urls = [
        "https://h.example.invalid/PDS/data/a/x/one.xml",
        "https://h.example.invalid/PDS/data/a/y/two.xml",
        "https://h.example.invalid/PDS/data/b/three.xml",
    ]
    assert dcf.common_url_prefix(urls) == "https://h.example.invalid/PDS/data/"


def test_mirror_path_maps_host_and_path(tmp_path):
    assert dcf.mirror_path(tmp_path, LABEL_URL) == tmp_path / "files" / "data.example.invalid" / "PDS/data/bundle/coll/coll.xml"


@pytest.mark.parametrize("url", ["https://h.example.invalid/", "https://h.example.invalid/a/../../etc/x", "/just/a/path"])
def test_mirror_path_rejects_unmappable_urls(tmp_path, url):
    with pytest.raises(dcf.CollectionFilesError):
        dcf.mirror_path(tmp_path, url)


# ── inventory and checksums ───────────────────────────────────────────────────


def test_count_inventory_rows_without_and_with_header(tmp_path):
    plain = tmp_path / "plain.csv"
    plain.write_bytes(INVENTORY)
    headed = tmp_path / "headed.csv"
    headed.write_bytes(b"member_status,lidvid\n" + INVENTORY + b"\n")
    assert dcf.count_inventory_rows(plain) == 2
    assert dcf.count_inventory_rows(headed) == 2


def test_download_file_writes_and_returns_md5(tmp_path):
    dest = tmp_path / "a" / "b" / "coll.xml"
    assert dcf.download_file(FakeSession(), LABEL_URL, dest, 5) == md5(LABEL)
    assert dest.read_bytes() == LABEL
    assert not dest.with_name("coll.xml.part").exists()


def test_download_file_failure_leaves_no_partial_file(tmp_path):
    dest = tmp_path / "missing.xml"
    with pytest.raises(dcf.CollectionFilesError):
        dcf.download_file(FakeSession(files={}), LABEL_URL, dest, 5)
    assert not dest.exists()
    assert not dest.with_name("missing.xml.part").exists()


# ── API lookup ────────────────────────────────────────────────────────────────


def test_fetch_collection_files_parses_properties():
    files = dcf.fetch_collection_files(FakeSession(api_props()), "https://api.example.invalid", LIDVID, 5)
    assert files.label_url == LABEL_URL
    assert files.inventory_url == INVENTORY_URL
    assert files.label_records == 2
    assert files.harvest_time == "2025-04-08T20:36:50.494165Z"


def test_fetch_uses_the_search_endpoint_with_a_lidvid_query():
    session = FakeSession(api_props())
    dcf.fetch_collection_files(session, "https://api.example.invalid", LIDVID, 5)
    assert session.requested == ["https://api.example.invalid/products"]
    assert session.params[0]["q"] == f'lidvid eq "{LIDVID}"'


def test_collection_registered_under_two_nodes_requires_a_choice():
    session = FakeSession(api_props(), copies=[psa_copy(), api_props()])
    with pytest.raises(dcf.CollectionFilesError, match="several nodes"):
        dcf.fetch_collection_files(session, "https://api.example.invalid", LIDVID, 5)


def test_node_name_selects_that_nodes_copy_even_when_it_is_not_first():
    session = FakeSession(api_props(), copies=[psa_copy(), api_props()])
    files = dcf.fetch_collection_files(session, "https://api.example.invalid", LIDVID, 5, "PDS_ATM")
    assert files.node_name == "PDS_ATM"
    assert files.label_url == LABEL_URL
    other = dcf.fetch_collection_files(session, "https://api.example.invalid", LIDVID, 5, "PSA")
    assert other.label_url == "https://archive.example.invalid/psa/coll/collection.xml"


def test_node_name_that_is_not_registered_fails():
    with pytest.raises(dcf.CollectionFilesError, match="not registered under node PDS_GEO"):
        dcf.fetch_collection_files(FakeSession(api_props()), "https://api.example.invalid", LIDVID, 5, "PDS_GEO")


def test_process_collection_downloads_the_chosen_nodes_files(tmp_path):
    session = FakeSession(api_props(), copies=[psa_copy(), api_props()])
    row, _ = run(tmp_path, session, node_name="PDS_ATM")
    assert row["status"] == "downloaded"
    assert row["node_name"] == "PDS_ATM"
    assert row["label_url"] == LABEL_URL
    assert not any("archive.example.invalid" in url for url in session.requested)


def test_ambiguous_collection_is_recorded_as_failed_without_downloading(tmp_path):
    session = FakeSession(api_props(), copies=[psa_copy(), api_props()])
    row, _ = run(tmp_path, session)
    assert row["status"] == "failed"
    assert "--node-name" in row["error"]
    assert not (tmp_path / "files").exists()


def test_fetch_collection_files_without_label_url_fails():
    with pytest.raises(dcf.CollectionFilesError):
        dcf.fetch_collection_files(FakeSession({}), "https://api.example.invalid", LIDVID, 5)


def test_fetch_collection_files_http_error_fails():
    with pytest.raises(dcf.CollectionFilesError):
        dcf.fetch_collection_files(FakeSession(None), "https://api.example.invalid", LIDVID, 5)


# ── process_collection ────────────────────────────────────────────────────────


def run(tmp_path, session, **kwargs):
    options = dict(list_only=False, skip_existing=False)
    options.update(kwargs)
    return dcf.process_collection(session, "https://api.example.invalid", LIDVID, tmp_path, 5, **options)


def test_download_matching_registry_checksums(tmp_path):
    row, _ = run(tmp_path, FakeSession(api_props()))
    assert row["status"] == "downloaded"
    assert row["md5_changed_since_harvest"] is False
    assert row["records_match"] is True
    assert row["inventory_rows"] == 2
    assert row["url_base"] == "https://data.example.invalid/PDS/data/bundle/coll/"
    assert row["label_and_inventory_same_dir"] is True
    assert Path(row["local_label"]).read_bytes() == LABEL
    assert Path(row["local_inventory"]).read_bytes() == INVENTORY


def test_changed_provider_file_is_flagged(tmp_path):
    row, _ = run(tmp_path, FakeSession(api_props(inventory_md5="0" * 32)))
    assert row["md5_changed_since_harvest"] is True


def test_record_count_mismatch_uses_the_downloaded_label(tmp_path):
    session = FakeSession(
        api_props(label_md5=md5(LABEL_WITH_14_RECORDS)),
        files={LABEL_URL: LABEL_WITH_14_RECORDS, INVENTORY_URL: INVENTORY},
    )
    row, _ = run(tmp_path, session)
    assert row["label_records_local"] == 14
    assert row["inventory_rows"] == 2
    assert row["records_match"] is False


def test_registry_record_count_is_not_what_is_compared(tmp_path):
    # The registry holds an old count of 14, but the label the provider serves now says 2.
    row, _ = run(tmp_path, FakeSession(api_props(records="14")))
    assert row["label_records_registry"] == 14
    assert row["label_records_local"] == 2
    assert row["records_match"] is True


def test_label_record_count_reads_namespaced_label(tmp_path):
    path = tmp_path / "label.xml"
    path.write_text("<pds:Product_Collection><pds:Inventory><pds:records>7</pds:records></pds:Inventory></pds:Product_Collection>")
    assert dcf.label_record_count(path) == 7
    path.write_text("<Product_Collection/>")
    assert dcf.label_record_count(path) is None


def test_list_only_downloads_nothing(tmp_path):
    session = FakeSession(api_props())
    row, files = run(tmp_path, session, list_only=True)
    assert row["status"] == "listed"
    assert files is not None
    assert not (tmp_path / "files").exists()
    assert all(url.endswith("/products") for url in session.requested)


def test_failed_lookup_is_recorded_not_raised(tmp_path):
    row, files = run(tmp_path, FakeSession(None))
    assert row["status"] == "failed"
    assert "API request" in row["error"]
    assert files is None


def test_skip_existing_reuses_files(tmp_path):
    run(tmp_path, FakeSession(api_props()))
    session = FakeSession(api_props())
    row, _ = run(tmp_path, session, skip_existing=True)
    assert row["status"] == "downloaded"
    assert all(url.endswith("/products") for url in session.requested)


# ── inputs and outputs ────────────────────────────────────────────────────────


def test_read_lidvids_from_file_skips_comments(tmp_path):
    path = tmp_path / "list.txt"
    path.write_text("# header\n\nurn:a:b:c:d::1.0\n  urn:a:b:c:e::2.0  \n", encoding="utf-8")
    assert dcf.read_lidvids_from_file(path) == ["urn:a:b:c:d::1.0", "urn:a:b:c:e::2.0"]


def test_read_lidvids_from_audit_csv_filters_by_rule(tmp_path):
    text = (
        "rule,collection_lidvid\n"
        "refs_missing,urn:a:b:c:one::1.0\n"
        "refs_missing,urn:a:b:c:one::1.0\n"
        "collection_pending,urn:a:b:c:two::1.0\n"
        "stale_stamp,urn:a:b:c:three::1.0\n"
        "refs_missing,\n"
    )
    plain = tmp_path / "audit.csv"
    plain.write_text(text, encoding="utf-8")
    zipped = tmp_path / "audit.csv.gz"
    with gzip.open(zipped, "wt", encoding="utf-8") as f:
        f.write(text)
    expected = ["urn:a:b:c:one::1.0", "urn:a:b:c:three::1.0"]
    rules = {"refs_missing", "stale_stamp"}
    assert dcf.read_lidvids_from_audit_csv(plain, rules) == expected
    assert dcf.read_lidvids_from_audit_csv(zipped, rules) == expected


def test_summary_separates_non_url_file_refs(tmp_path, capsys):
    bad = {field: "" for field in dcf._MANIFEST_FIELDS}
    bad.update(collection_lidvid=LIDVID, status="failed", label_url="/home/user/data/coll.xml")
    dcf.print_summary([bad], {}, tmp_path)
    out = capsys.readouterr().out
    assert "not a URL" in out
    assert '="://"' not in out


def test_manifest_and_harvest_snippet(tmp_path):
    row, _ = run(tmp_path, FakeSession(api_props()))
    failed = {field: "" for field in dcf._MANIFEST_FIELDS}
    failed.update(collection_lidvid="urn:x:y:z:w::1.0", status="failed")

    dcf.write_manifest([row, failed], tmp_path / "manifest.csv")
    assert (tmp_path / "manifest.csv").read_text(encoding="utf-8").splitlines()[0].startswith("collection_lidvid,status")

    snippet = dcf.build_harvest_snippet(tmp_path, [row, failed])
    root = tmp_path.resolve()
    assert f"<path>{root / 'files' / 'data.example.invalid' / 'PDS/data/bundle/coll'}</path>" in snippet
    assert f'replacePrefix="{root / "files" / "data.example.invalid"}" with="https://data.example.invalid"' in snippet
    assert "urn:x:y:z:w" not in snippet
