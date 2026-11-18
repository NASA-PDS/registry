"""Tests for ``unprocessed_audit.inventory`` (no network)."""

from __future__ import annotations

import pytest
import requests
from unprocessed_audit import inventory
from unprocessed_audit.inventory import InventoryCache
from unprocessed_audit.inventory import InventoryError
from unprocessed_audit.inventory import InventoryIndex
from unprocessed_audit.inventory import fetch_inventory
from unprocessed_audit.inventory import parse_inventory
from unprocessed_audit.model import Collection

URL = "https://data.example.invalid/c/inventory.csv"


class FakeResponse:
    def __init__(self, text: str = "", status: int = 200) -> None:
        self.text = text
        self.status = status
        self.encoding = None

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status}")

    def iter_lines(self, chunk_size: int = 512, decode_unicode: bool = False):
        assert decode_unicode is True
        assert chunk_size >= 1024 * 1024
        yield from self.text.splitlines()

    def iter_content(self, chunk_size: int = 1):
        yield self.text.encode("utf-8")

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


class FakeSession:
    def __init__(self, bodies: dict[str, str] | None = None) -> None:
        self.bodies = bodies if bodies is not None else {URL: "P,urn:a:b:c:one::1.0\nS,urn:a:b:c:two::2.0\n"}
        self.requested: list[str] = []

    def get(self, url: str, stream: bool = False, timeout: int | None = None) -> FakeResponse:
        self.requested.append(url)
        if url not in self.bodies:
            return FakeResponse(status=404)
        return FakeResponse(self.bodies[url])


def collection(lidvid: str, url: str | None = URL) -> Collection:
    return Collection(
        lidvid=lidvid, lid=lidvid.split("::")[0], node="atm", stamp="7", ancestor_refs=["x"], harvest=None,
        inventory_url=url,
    )  # fmt: skip


def test_parse_without_header():
    index = parse_inventory(["P,urn:a:b:c:one::1.0", "S,urn:a:b:c:two::2.0"])
    assert index.lidvids == {"urn:a:b:c:one::1.0", "urn:a:b:c:two::2.0"}
    assert index.listed_by_lid == {"urn:a:b:c:one": "urn:a:b:c:one::1.0", "urn:a:b:c:two": "urn:a:b:c:two::2.0"}


def test_parse_skips_header_blank_lines_and_short_rows():
    index = parse_inventory(["member_status,lidvid", "", "P,urn:a:b:c:one::1.0", "P", " , "])
    assert index.lidvids == {"urn:a:b:c:one::1.0"}


def test_parse_bare_lids_stand_for_every_version():
    index = parse_inventory(["P,urn:a:b:c:one"])
    assert index.bare_lids == {"urn:a:b:c:one"}
    assert index.lists("urn:a:b:c:one::7.0", "urn:a:b:c:one")
    assert not index.lists("urn:a:b:c:other::1.0", "urn:a:b:c:other")


def test_lists_and_other_version():
    index = parse_inventory(["P,urn:a:b:c:one::14.0"])
    assert index.lists("urn:a:b:c:one::14.0", "urn:a:b:c:one")
    assert not index.lists("urn:a:b:c:one::13.1", "urn:a:b:c:one")
    assert index.other_version("urn:a:b:c:one", "urn:a:b:c:one::13.1") == "urn:a:b:c:one::14.0"
    assert index.other_version("urn:a:b:c:one", "urn:a:b:c:one::14.0") is None
    assert index.other_version("urn:a:b:c:missing", "urn:a:b:c:missing::1.0") is None


def test_fetch_inventory_streams_and_indexes():
    session = FakeSession()
    index = fetch_inventory(session, URL, 5)  # type: ignore[arg-type]
    assert isinstance(index, InventoryIndex)
    assert "urn:a:b:c:one::1.0" in index.lidvids


def test_fetch_inventory_failure_raises_inventory_error():
    with pytest.raises(InventoryError, match="Could not read the inventory"):
        fetch_inventory(FakeSession({}), URL, 5)  # type: ignore[arg-type]


def test_cache_downloads_once_per_collection():
    session = FakeSession()
    cache = InventoryCache(session, 5)  # type: ignore[arg-type]
    coll = collection("urn:a:b:c::1.0")
    first = cache(coll)
    assert first is not None
    assert cache(coll) is first
    assert session.requested == [URL]
    assert cache.downloads == 1


def test_cache_keeps_only_the_most_recent_inventories():
    session = FakeSession()
    cache = InventoryCache(session, 5, max_size=2)  # type: ignore[arg-type]
    a, b, c = (collection(f"urn:a:b:c{n}::1.0") for n in "abc")
    cache(a)
    cache(b)
    cache(a)  # a is now the most recently used
    cache(c)  # evicts b
    cache(a)
    cache(b)
    assert cache.downloads == 4  # a, b, c, then b again


def test_cache_returns_none_without_a_url_or_after_a_failed_download(caplog):
    cache = InventoryCache(FakeSession(), 5)  # type: ignore[arg-type]
    assert cache(collection("urn:a:b:c::1.0", url=None)) is None
    assert cache(collection("urn:a:b:d::1.0", url="https://data.example.invalid/missing.csv")) is None
    assert "no inventory URL" in caplog.text
    assert "Could not read the inventory" in caplog.text


def test_disk_cache_keeps_the_download_and_a_new_cache_reuses_it(tmp_path):
    session = FakeSession()
    first = InventoryCache(session, 5, cache_dir=tmp_path)  # type: ignore[arg-type]
    index = first(collection("urn:a:b:c::1.0"))
    assert index is not None and "urn:a:b:c:one::1.0" in index.lidvids
    assert session.requested == [URL]
    assert [p.name for p in tmp_path.iterdir()] == [inventory.cached_inventory_path(tmp_path, URL).name]

    second_session = FakeSession()
    second = InventoryCache(second_session, 5, cache_dir=tmp_path)  # type: ignore[arg-type]
    again = second(collection("urn:a:b:c::1.0"))
    assert again is not None and again.lidvids == index.lidvids
    assert second_session.requested == []
    assert second.downloads == 0


def test_disk_cache_failed_download_leaves_no_file(tmp_path):
    cache = InventoryCache(FakeSession({}), 5, cache_dir=tmp_path / "kept")  # type: ignore[arg-type]
    assert cache(collection("urn:a:b:c::1.0")) is None
    kept = tmp_path / "kept"
    assert not kept.exists() or list(kept.iterdir()) == []


def test_cached_inventory_path_is_stable_and_distinct(tmp_path):
    a = inventory.cached_inventory_path(tmp_path, URL)
    assert a == inventory.cached_inventory_path(tmp_path, URL)
    assert a != inventory.cached_inventory_path(tmp_path, URL + "x")
    assert a.parent == tmp_path and a.suffix == ".csv"


def test_make_session_sets_a_user_agent():
    assert inventory.make_session().headers["User-Agent"] == "pds-registry-audit/1.0"
