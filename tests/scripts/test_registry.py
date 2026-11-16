"""Tests for ``unprocessed_audit.registry``; no network access."""
# flake8: noqa: D101,D102,D103,D107

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from datetime import timezone

import pytest
import requests
from unprocessed_audit import registry
from unprocessed_audit.model import HARVEST_FIELD
from unprocessed_audit.model import REFS_FIELD
from unprocessed_audit.model import STAMP_FIELD
from unprocessed_audit.model import Collection
from unprocessed_audit.model import RefsCoverage
from unprocessed_audit.model import RegistryQueryError
from unprocessed_audit.registry import RegistryClient

Responder = Callable[[str, dict], dict]


class FakeClient(RegistryClient):
    """Registry client whose ``search`` and ``count`` are scripted; records every call."""

    def __init__(self, responder: Responder | None = None, counts: list[int] | None = None) -> None:
        super().__init__(auth=None, endpoint="https://example.invalid")  # type: ignore[arg-type]
        self.responder = responder
        self.counts = list(counts or [])
        self.searches: list[tuple[str, dict]] = []
        self.counted: list[tuple[str, dict]] = []

    def search(self, index: str, body: dict) -> dict:
        self.searches.append((index, body))
        assert self.responder is not None
        return self.responder(index, body)

    def count(self, index: str, body: dict) -> int:
        self.counted.append((index, body))
        return self.counts.pop(0)


def hits_response(hits: list[dict]) -> dict:
    return {"hits": {"hits": hits}}


def product_hit(index: str, n: int, **source: object) -> dict:
    src = {"lidvid": f"urn:nasa:pds:b:c:p{n}::1.0", "lid": f"urn:nasa:pds:b:c:p{n}", "product_class": "Product_Observational"}
    src.update(source)
    return {"_index": index, "_id": f"{index}-{n}", "_source": src, "sort": [f"{index}-{n}"]}


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: object = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text or json.dumps(payload)

    def json(self) -> object:
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


# ── index helpers ─────────────────────────────────────────────────────────────


def test_registry_index() -> None:
    assert registry.registry_index(None) == "*-registry"
    assert registry.registry_index(["atm", "geo"]) == "atm-registry,geo-registry"


def test_refs_index() -> None:
    assert registry.refs_index(None) == "*-registry-refs"
    assert registry.refs_index(["atm", "geo"]) == "atm-registry-refs,geo-registry-refs"


def test_node_of_index() -> None:
    assert registry.node_of_index("atm-registry") == "atm"
    assert registry.node_of_index("atm") == "atm"
    assert registry.node_of_index("en-legacy-registry") == "en-legacy"


_AOSS_PREFIX = "<account-id>::<collection-id>::SEARCH::"


def test_node_of_index_parses_aoss_index_form() -> None:
    assert registry.index_name_of(f"{_AOSS_PREFIX}geo-registry:0") == "geo-registry"
    assert registry.node_of_index(f"{_AOSS_PREFIX}geo-registry:0") == "geo"
    assert registry.node_of_index(f"{_AOSS_PREFIX}temp-atm-registry:0") == "temp-atm"


def test_discover_nodes_parses_aoss_index_form_and_skips_legacy() -> None:
    buckets = [
        {"key": f"{_AOSS_PREFIX}en-legacy-registry:0"},
        {"key": f"{_AOSS_PREFIX}geo-registry:0"},
        {"key": f"{_AOSS_PREFIX}img-registry:0"},
    ]
    fake = FakeClient(lambda index, body: {"aggregations": {"indices": {"buckets": buckets}}})
    assert registry.discover_nodes(fake) == ["geo", "img"]


def test_registry_endpoint_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REQUEST_SIGNER_AOSS_ENDPOINT", raising=False)
    with pytest.raises(RegistryQueryError):
        registry.registry_endpoint_from_env()
    monkeypatch.setenv("REQUEST_SIGNER_AOSS_ENDPOINT", "https://example.invalid")
    assert registry.registry_endpoint_from_env() == "https://example.invalid"


def test_make_registry_auth_lists_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("opensearchpy")
    pytest.importorskip("pds.aossrequestsigner")
    for name in registry._REGISTRY_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RegistryQueryError, match="REQUEST_SIGNER_AWS_REGION"):
        registry.make_registry_auth()


# ── query builders ────────────────────────────────────────────────────────────


def test_api_visible_clauses() -> None:
    clauses = registry.api_visible_clauses()
    assert {"terms": {"ops:Tracking_Meta/ops:archive_status": ["archived", "certified"]}} in clauses["filter"]
    assert {"exists": {"field": "ops:Provenance/ops:superseded_by"}} in clauses["must_not"]


def test_api_visible_clauses_returns_fresh_lists() -> None:
    registry.api_visible_clauses()["filter"].append("junk")
    assert "junk" not in registry.api_visible_clauses()["filter"]


def test_collections_query() -> None:
    bool_ = registry.collections_query()["query"]["bool"]
    assert {"term": {"product_class": "Product_Collection"}} in bool_["filter"]
    # Superseded collection versions are included: their products stay API-visible.
    assert "must_not" not in bool_
    assert {"terms": {"ops:Tracking_Meta/ops:archive_status": ["archived", "certified"]}} in bool_["filter"]


def test_candidate_query_shape() -> None:
    bool_ = registry.candidate_query(7)["query"]["bool"]
    assert {"terms": {"product_class": ["Product_Bundle", "Product_Collection"]}} in bool_["must_not"]
    assert {"exists": {"field": "ops:Provenance/ops:superseded_by"}} in bool_["must_not"]
    assert bool_["minimum_should_match"] == 1
    a, b, c = bool_["should"]
    assert a == {"bool": {"must_not": [{"exists": {"field": STAMP_FIELD}}]}}
    assert b == {"bool": {"must_not": [{"exists": {"field": REFS_FIELD}}]}}
    assert c == {
        "bool": {
            "filter": [{"exists": {"field": STAMP_FIELD}}],
            "must_not": [{"term": {STAMP_FIELD: "7"}}],
        }
    }


def test_candidate_query_never_uses_range() -> None:
    assert "range" not in json.dumps(registry.candidate_query(7))


# ── RegistryClient ────────────────────────────────────────────────────────────


@pytest.fixture
def client() -> RegistryClient:
    c = RegistryClient(auth=None, endpoint="https://example.invalid/", timeout=5)  # type: ignore[arg-type]
    c.backoff_seconds = 0
    return c


def test_search_url_keeps_commas_and_dashes(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    calls: list[dict] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        calls.append(kwargs)
        return FakeResponse(payload={"hits": {"hits": []}})

    monkeypatch.setattr(registry.requests, "post", fake_post)
    client.search("*-registry", {"query": {"match_all": {}}})
    assert calls[0]["url"] == "https://example.invalid/*-registry/_search"
    assert json.loads(calls[0]["data"]) == {"query": {"match_all": {}}}
    assert calls[0]["timeout"] == 5


def test_get_mapping_issues_a_get_without_a_body(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    calls: list[dict] = []

    def fake_get(**kwargs: object) -> FakeResponse:
        calls.append(kwargs)
        return FakeResponse(payload={"atm-registry": {"mappings": {}}})

    def fail_post(**kwargs: object) -> FakeResponse:
        raise AssertionError("a mapping read must not POST")

    monkeypatch.setattr(registry.requests, "get", fake_get)
    monkeypatch.setattr(registry.requests, "post", fail_post)
    assert client.get_mapping("atm-registry") == {"atm-registry": {"mappings": {}}}
    assert calls[0]["url"] == "https://example.invalid/atm-registry/_mapping"
    assert calls[0]["data"] is None


def test_count_returns_int(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    urls: list[str] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        urls.append(str(kwargs["url"]))
        return FakeResponse(payload={"count": 42})

    monkeypatch.setattr(registry.requests, "post", fake_post)
    assert client.count("atm-registry", {"query": {}}) == 42
    assert urls == ["https://example.invalid/atm-registry/_count"]


def test_count_without_count_raises(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    monkeypatch.setattr(registry.requests, "post", lambda **kw: FakeResponse(payload={"oops": 1}))
    with pytest.raises(RegistryQueryError):
        client.count("atm-registry", {})


def test_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    responses = [FakeResponse(429, text="slow down"), FakeResponse(503, text="busy"), FakeResponse(payload={"ok": 1})]
    attempts: list[int] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        attempts.append(1)
        return responses.pop(0)

    monkeypatch.setattr(registry.requests, "post", fake_post)
    assert client.search("atm-registry", {}) == {"ok": 1}
    assert len(attempts) == 3


def test_retries_then_raises(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    attempts: list[int] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        attempts.append(1)
        return FakeResponse(500, text="boom")

    monkeypatch.setattr(registry.requests, "post", fake_post)
    with pytest.raises(RegistryQueryError, match="boom"):
        client.search("atm-registry", {})
    assert len(attempts) == 1 + registry.MAX_RETRIES


def test_connection_error_retried_then_raises(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    attempts: list[int] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        attempts.append(1)
        raise requests.exceptions.ConnectionError("down")

    monkeypatch.setattr(registry.requests, "post", fake_post)
    with pytest.raises(RegistryQueryError, match="down"):
        client.search("atm-registry", {})
    assert len(attempts) == 1 + registry.MAX_RETRIES


def test_client_error_not_retried(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    attempts: list[int] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        attempts.append(1)
        return FakeResponse(400, text="bad query")

    monkeypatch.setattr(registry.requests, "post", fake_post)
    with pytest.raises(RegistryQueryError, match="bad query"):
        client.search("atm-registry", {})
    assert len(attempts) == 1


# ── credential renewal ───────────────────────────────────────────────────────


def renewing_client(auths: list[object], **kwargs: object) -> tuple[RegistryClient, list[str]]:
    """A client whose ``refresh_auth`` hands out ``auths`` in turn and records each renewal."""
    renewed: list[str] = []

    def refresh() -> object:
        renewed.append("renewed")
        return auths.pop(0)

    c = RegistryClient(
        auth="login-credentials",  # type: ignore[arg-type]
        endpoint="https://example.invalid/",
        timeout=5,
        refresh_auth=refresh,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )
    c.backoff_seconds = 0
    return c, renewed


def test_expired_credentials_are_renewed_once_and_the_request_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    c, renewed = renewing_client(["fresh-credentials"])
    seen_auth: list[object] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        seen_auth.append(kwargs["auth"])
        if kwargs["auth"] == "login-credentials":
            return FakeResponse(403, text="403 Forbidden")
        return FakeResponse(payload={"ok": 1})

    monkeypatch.setattr(registry.requests, "post", fake_post)
    assert c.search("atm-registry-refs", {}) == {"ok": 1}
    assert seen_auth == ["login-credentials", "fresh-credentials"]
    assert renewed == ["renewed"]


def test_a_genuine_403_is_renewed_only_once_then_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    c, renewed = renewing_client(["fresh-1", "fresh-2"])
    attempts: list[int] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        attempts.append(1)
        return FakeResponse(403, text="403 Forbidden")

    monkeypatch.setattr(registry.requests, "post", fake_post)
    with pytest.raises(RegistryQueryError, match="HTTP 403"):
        c.search("atm-registry-refs", {})
    assert len(attempts) == 2
    assert renewed == ["renewed"]


def test_old_credentials_are_renewed_before_the_next_request(monkeypatch: pytest.MonkeyPatch) -> None:
    c, renewed = renewing_client(["fresh-credentials"], auth_max_age_seconds=0)
    seen_auth: list[object] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        seen_auth.append(kwargs["auth"])
        return FakeResponse(payload={"ok": 1})

    monkeypatch.setattr(registry.requests, "post", fake_post)
    c.search("atm-registry", {})
    assert seen_auth == ["fresh-credentials"]
    assert renewed == ["renewed"]


def test_young_credentials_are_not_renewed(monkeypatch: pytest.MonkeyPatch) -> None:
    c, renewed = renewing_client(["unused"])
    monkeypatch.setattr(registry.requests, "post", lambda **kw: FakeResponse(payload={"ok": 1}))
    c.search("atm-registry", {})
    assert renewed == []


def test_without_a_refresh_function_a_403_fails_immediately(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    attempts: list[int] = []

    def fake_post(**kwargs: object) -> FakeResponse:
        attempts.append(1)
        return FakeResponse(403, text="403 Forbidden")

    monkeypatch.setattr(registry.requests, "post", fake_post)
    with pytest.raises(RegistryQueryError, match="HTTP 403"):
        client.search("atm-registry", {})
    assert len(attempts) == 1


def test_invalid_json_raises(monkeypatch: pytest.MonkeyPatch, client: RegistryClient) -> None:
    monkeypatch.setattr(registry.requests, "post", lambda **kw: FakeResponse(200, payload=None, text="<html>"))
    with pytest.raises(RegistryQueryError, match="invalid JSON"):
        client.search("atm-registry", {})


# ── discover_nodes ────────────────────────────────────────────────────────────


def test_discover_nodes() -> None:
    buckets = [{"key": "geo-registry"}, {"key": "atm-registry"}, {"key": "atm-registry"}]
    fake = FakeClient(lambda index, body: {"aggregations": {"indices": {"buckets": buckets}}})
    assert registry.discover_nodes(fake) == ["atm", "geo"]
    index, body = fake.searches[0]
    assert index == "*-registry"
    assert body["size"] == 0
    assert body["aggs"]["indices"]["terms"]["field"] == "_index"


def test_discover_nodes_ignores_legacy_index() -> None:
    buckets = [{"key": "en-legacy-registry"}, {"key": "atm-registry"}]
    fake = FakeClient(lambda index, body: {"aggregations": {"indices": {"buckets": buckets}}})
    assert registry.discover_nodes(fake) == ["atm"]


def test_discover_nodes_failure_mentions_node_option() -> None:
    def boom(index: str, body: dict) -> dict:
        raise RegistryQueryError("HTTP 400")

    with pytest.raises(RegistryQueryError, match="--node"):
        registry.discover_nodes(FakeClient(boom))


def test_discover_nodes_empty_mentions_node_option() -> None:
    fake = FakeClient(lambda index, body: {"aggregations": {"indices": {"buckets": []}}})
    with pytest.raises(RegistryQueryError, match="--node"):
        registry.discover_nodes(fake)


# ── iter_collections ──────────────────────────────────────────────────────────


def test_iter_collections_parses_scalar_list_and_missing() -> None:
    hits = [
        {
            "_index": "atm-registry",
            "_id": "1",
            "_source": {
                "lidvid": "urn:nasa:pds:b:c::1.0",
                "lid": "urn:nasa:pds:b:c",
                STAMP_FIELD: ["7"],
                REFS_FIELD: ["urn:nasa:pds:b::1.0", "urn:nasa:pds:b"],
                HARVEST_FIELD: "2025-03-01T12:00:00.5Z",
                "ops:Provenance/ops:superseded_by": "urn:nasa:pds:b:c::2.0",
                "ops:Data_File_Info/ops:file_ref": ["https://data.example.invalid/b/c/inventory.csv"],
            },
        },
        {
            "_index": "geo-registry",
            "_id": "2",
            "_source": {
                "lidvid": ["urn:nasa:pds:b2:c2::2.0"],
                STAMP_FIELD: 6,
                REFS_FIELD: [],
                HARVEST_FIELD: "2025-03-01T12:00:00",
            },
        },
        {"_index": "geo-registry", "_id": "3", "_source": {"lidvid": "urn:nasa:pds:b3:c3::1.0", REFS_FIELD: "urn:x"}},
        {
            "_index": "geo-registry",
            "_id": "4",
            "_source": {"lidvid": "urn:nasa:pds:b4:c4::1.0", HARVEST_FIELD: "junk", STAMP_FIELD: ""},
        },
        {"_index": "geo-registry", "_id": "5", "_source": {}},
    ]
    fake = FakeClient(lambda index, body: hits_response(hits))
    colls = list(registry.iter_collections(fake, None))

    assert [c.lidvid for c in colls] == [
        "urn:nasa:pds:b:c::1.0",
        "urn:nasa:pds:b2:c2::2.0",
        "urn:nasa:pds:b3:c3::1.0",
        "urn:nasa:pds:b4:c4::1.0",
    ]
    first, second, third, fourth = colls
    assert (first.node, first.lid, first.stamp) == ("atm", "urn:nasa:pds:b:c", "7")
    assert first.ancestor_refs == ["urn:nasa:pds:b::1.0", "urn:nasa:pds:b"]
    assert first.harvest == datetime(2025, 3, 1, 12, 0, 0, 500000, tzinfo=timezone.utc)
    assert (second.node, second.lid, second.stamp, second.ancestor_refs) == ("geo", "urn:nasa:pds:b2:c2", "6", [])
    assert second.harvest == datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert (third.stamp, third.ancestor_refs, third.harvest) == (None, ["urn:x"], None)
    assert (fourth.stamp, fourth.harvest) == (None, None)

    index, body = fake.searches[0]
    assert index == "*-registry"
    assert body["size"] == 10000
    assert body["sort"] == [{"_id": "asc"}]
    assert "search_after" not in body
    assert body["query"] == registry.collections_query()["query"]
    assert set(body["_source"]) == {
        "lidvid",
        "lid",
        STAMP_FIELD,
        REFS_FIELD,
        HARVEST_FIELD,
        "ops:Provenance/ops:superseded_by",
        "ops:Data_File_Info/ops:file_ref",
    }
    assert (first.superseded_by, second.superseded_by) == ("urn:nasa:pds:b:c::2.0", None)
    assert (first.inventory_url, second.inventory_url) == ("https://data.example.invalid/b/c/inventory.csv", None)


def test_iter_collections_pages_with_search_after(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry, "MAX_PAGE_SIZE", 2)
    pages = [
        [product_hit("atm-registry", 1), product_hit("atm-registry", 2)],
        [product_hit("atm-registry", 3)],
    ]
    fake = FakeClient(lambda index, body: hits_response(pages.pop(0)))
    colls = list(registry.iter_collections(fake, ["atm"]))
    assert len(colls) == 3
    assert fake.searches[0][0] == "atm-registry"
    assert fake.searches[1][1]["search_after"] == ["atm-registry-2"]


# ── iter_candidate_pages ──────────────────────────────────────────────────────


def paged_responder(data: dict[str, list[list[dict]]]) -> Responder:
    """Return a responder serving scripted pages per index."""

    def respond(index: str, body: dict) -> dict:
        return hits_response(data[index].pop(0) if data[index] else [])

    return respond


def test_candidate_pages_across_two_nodes_with_search_after() -> None:
    data = {
        "atm-registry": [
            [product_hit("atm-registry", 1), product_hit("atm-registry", 2)],
            [product_hit("atm-registry", 3)],
        ],
        "geo-registry": [[product_hit("geo-registry", 1), product_hit("geo-registry", 2)]],
    }
    fake = FakeClient(paged_responder(data))
    pages = list(registry.iter_candidate_pages(fake, ["atm", "geo"], 7, page_size=2))

    assert [[c.node for c in page] for page in pages] == [["atm", "atm"], ["atm"], ["geo", "geo"]]
    assert [len(p) for p in pages] == [2, 1, 2]
    assert [i for i, _ in fake.searches] == ["atm-registry", "atm-registry", "geo-registry", "geo-registry"]
    assert "search_after" not in fake.searches[0][1]
    assert fake.searches[1][1]["search_after"] == ["atm-registry-2"]
    assert "search_after" not in fake.searches[2][1]
    assert fake.searches[3][1]["search_after"] == ["geo-registry-2"]
    assert all(body["size"] == 2 for _, body in fake.searches)
    assert fake.searches[0][1]["query"] == registry.candidate_query(7)["query"]


def test_candidate_pages_skip_superseded_products_client_side() -> None:
    # On the ATM index ``superseded_by`` is returned in ``_source`` but cannot be searched, so the query cannot
    # exclude superseded products and they are dropped from the hits instead.
    superseded = "ops:Provenance/ops:superseded_by"
    data = {
        "atm-registry": [
            [
                product_hit("atm-registry", 1),
                product_hit("atm-registry", 2, **{superseded: "urn:nasa:pds:b:c:p2::2.0"}),
                product_hit("atm-registry", 3, **{superseded: None}),
                product_hit("atm-registry", 4, **{superseded: ["urn:nasa:pds:b:c:p4::2.0"]}),
            ]
        ]
    }
    fake = FakeClient(paged_responder(data))
    (page,) = list(registry.iter_candidate_pages(fake, ["atm"], 7, page_size=10))
    assert [c.lidvid for c in page] == ["urn:nasa:pds:b:c:p1::1.0", "urn:nasa:pds:b:c:p3::1.0"]
    assert superseded in fake.searches[0][1]["_source"]


def test_candidate_pages_max_products_counts_only_kept_products() -> None:
    superseded = "ops:Provenance/ops:superseded_by"
    hits = [product_hit("atm-registry", n, **({superseded: "x::1.0"} if n % 2 else {})) for n in range(1, 7)]
    fake = FakeClient(paged_responder({"atm-registry": [hits]}))
    (page,) = list(registry.iter_candidate_pages(fake, ["atm"], 7, page_size=10, max_products=2))
    assert [c.lidvid for c in page] == ["urn:nasa:pds:b:c:p2::1.0", "urn:nasa:pds:b:c:p4::1.0"]


def test_candidate_pages_max_products_truncates() -> None:
    data = {
        "atm-registry": [[product_hit("atm-registry", n) for n in range(1, 4)]],
        "geo-registry": [[product_hit("geo-registry", n) for n in range(1, 4)]],
    }
    fake = FakeClient(paged_responder(data))
    pages = list(registry.iter_candidate_pages(fake, ["atm", "geo"], 7, page_size=3, max_products=4))
    assert [len(p) for p in pages] == [3, 1]
    assert pages[1][0].node == "geo"
    # a full atm page is followed by an empty continuation page before moving on to geo
    assert [i for i, _ in fake.searches] == ["atm-registry", "atm-registry", "geo-registry"]


def test_candidate_pages_max_products_stops_before_next_node() -> None:
    data = {"atm-registry": [[product_hit("atm-registry", n) for n in range(1, 4)]], "geo-registry": [[]]}
    fake = FakeClient(paged_responder(data))
    pages = list(registry.iter_candidate_pages(fake, ["atm", "geo"], 7, page_size=3, max_products=3))
    assert [len(p) for p in pages] == [3]
    assert [i for i, _ in fake.searches] == ["atm-registry"]


def test_candidate_pages_discovers_nodes_when_none() -> None:
    def respond(index: str, body: dict) -> dict:
        if body.get("size") == 0:
            return {"aggregations": {"indices": {"buckets": [{"key": "atm-registry"}]}}}
        return hits_response([product_hit("atm-registry", 1)])

    fake = FakeClient(respond)
    pages = list(registry.iter_candidate_pages(fake, None, 7))
    assert [len(p) for p in pages] == [1]
    assert fake.searches[1][0] == "atm-registry"


@pytest.mark.parametrize("size", [0, -1, 10001, 50000])
def test_candidate_pages_page_size_guard(size: int) -> None:
    fake = FakeClient(lambda index, body: hits_response([]))
    with pytest.raises(ValueError):
        registry.iter_candidate_pages(fake, ["atm"], 7, page_size=size)
    assert not fake.searches


def test_candidate_fields_scalar_list_and_missing() -> None:
    hits = [
        product_hit(
            "atm-registry",
            1,
            **{STAMP_FIELD: ["7"], REFS_FIELD: ["urn:nasa:pds:b::1.0"], HARVEST_FIELD: ["2025-01-02T03:04:05Z"]},
        ),
        product_hit("atm-registry", 2, **{REFS_FIELD: []}),
        product_hit("atm-registry", 3, **{STAMP_FIELD: 6, REFS_FIELD: "urn:nasa:pds:b::1.0"}),
        {"_index": "atm-registry", "_id": "x", "_source": {}},
    ]
    fake = FakeClient(lambda index, body: hits_response(hits))
    (page,) = list(registry.iter_candidate_pages(fake, ["atm"], 7))
    assert len(page) == 3
    one, two, three = page
    assert (one.stamp, one.has_ancestor_refs) == ("7", True)
    assert one.harvest == datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert one.product_class == "Product_Observational"
    assert (two.stamp, two.has_ancestor_refs, two.harvest) == (None, False, None)
    assert (three.stamp, three.has_ancestor_refs) == ("6", True)
    assert three.node == "atm"


# ── lookup_refs ───────────────────────────────────────────────────────────────


def test_lookup_refs_empty_makes_no_request() -> None:
    fake = FakeClient(lambda index, body: hits_response([]))
    assert registry.lookup_refs(fake, [], None) == {}
    assert not fake.searches


def test_lookup_refs_batches_of_1000() -> None:
    ids = [f"urn:nasa:pds:b:c:p{n}::1.0" for n in range(2500)]
    fake = FakeClient(lambda index, body: hits_response([]))
    assert registry.lookup_refs(fake, ids, ["atm"]) == {}
    assert len(fake.searches) == 3
    sizes = [len(body["query"]["bool"]["filter"][0]["terms"]["product_lidvid"]) for _, body in fake.searches]
    assert sizes == [1000, 1000, 500]
    assert all(index == "atm-registry-refs" for index, _ in fake.searches)
    assert fake.searches[0][1]["_source"] == ["collection_lidvid", "product_lidvid"]
    assert all(body["size"] <= 10000 for _, body in fake.searches)


def test_lookup_refs_filters_to_requested_and_keeps_first() -> None:
    hits = [
        {
            "_id": "1",
            "_source": {
                "collection_lidvid": "urn:nasa:pds:b:c::1.0",
                "product_lidvid": ["urn:nasa:pds:b:c:p1::1.0", "urn:nasa:pds:b:c:other::1.0"],
            },
            "sort": ["1"],
        },
        {
            "_id": "2",
            "_source": {"collection_lidvid": "urn:nasa:pds:b:c2::1.0", "product_lidvid": "urn:nasa:pds:b:c:p1::1.0"},
            "sort": ["2"],
        },
        {
            "_id": "3",
            "_source": {"collection_lidvid": "urn:nasa:pds:b:c3::1.0", "product_lidvid": ["urn:nasa:pds:b:c:p2::1.0"]},
            "sort": ["3"],
        },
    ]
    fake = FakeClient(lambda index, body: hits_response(hits))
    result = registry.lookup_refs(fake, ["urn:nasa:pds:b:c:p1::1.0", "urn:nasa:pds:b:c:p2::1.0", "urn:missing::1.0"], None)
    assert result == {
        "urn:nasa:pds:b:c:p1::1.0": "urn:nasa:pds:b:c::1.0",
        "urn:nasa:pds:b:c:p2::1.0": "urn:nasa:pds:b:c3::1.0",
    }
    assert fake.searches[0][0] == "*-registry-refs"


def test_lookup_refs_pages_within_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry, "MAX_PAGE_SIZE", 1)
    docs = [
        {"_id": "1", "_source": {"collection_lidvid": "c1", "product_lidvid": ["p1"]}, "sort": ["1"]},
        {"_id": "2", "_source": {"collection_lidvid": "c2", "product_lidvid": ["p2"]}, "sort": ["2"]},
    ]
    pages = [[docs[0]], [docs[1]], []]
    fake = FakeClient(lambda index, body: hits_response(pages.pop(0)))
    assert registry.lookup_refs(fake, ["p1", "p2"], None) == {"p1": "c1", "p2": "c2"}
    assert fake.searches[1][1]["search_after"] == ["1"]
    assert fake.searches[2][1]["search_after"] == ["2"]


# ── lookup_refs_by_lid ────────────────────────────────────────────────────────


def test_lookup_refs_by_lid_empty_makes_no_request() -> None:
    fake = FakeClient(lambda index, body: hits_response([]))
    assert registry.lookup_refs_by_lid(fake, [], None) == {}
    assert not fake.searches


def test_lookup_refs_by_lid_batches_and_queries_product_lid() -> None:
    lids = [f"urn:nasa:pds:b:c:p{n}" for n in range(2500)]
    fake = FakeClient(lambda index, body: hits_response([]))
    assert registry.lookup_refs_by_lid(fake, lids, ["atm"]) == {}
    sizes = [len(body["query"]["bool"]["filter"][0]["terms"]["product_lid"]) for _, body in fake.searches]
    assert sizes == [1000, 1000, 500]
    assert all(index == "atm-registry-refs" for index, _ in fake.searches)
    assert fake.searches[0][1]["_source"] == ["product_lidvid"]


def test_lookup_refs_by_lid_returns_the_listed_version_for_requested_lids_only() -> None:
    hits = [
        {
            "_id": "1",
            "_source": {
                "product_lidvid": [
                    "urn:nasa:pds:b:c:p1::14.0",
                    "urn:nasa:pds:b:c:unrelated::1.0",
                    "urn:nasa:pds:b:c:p2::3.0",
                ]
            },
            "sort": ["1"],
        },
        {"_id": "2", "_source": {"product_lidvid": "urn:nasa:pds:b:c:p1::15.0"}, "sort": ["2"]},
    ]
    fake = FakeClient(lambda index, body: hits_response(hits))
    result = registry.lookup_refs_by_lid(fake, ["urn:nasa:pds:b:c:p1", "urn:nasa:pds:b:c:p2", "urn:nasa:pds:b:c:p3"], None)
    assert result == {
        "urn:nasa:pds:b:c:p1": "urn:nasa:pds:b:c:p1::14.0",
        "urn:nasa:pds:b:c:p2": "urn:nasa:pds:b:c:p2::3.0",
    }
    assert fake.searches[0][0] == "*-registry-refs"


# ── find_bundles ──────────────────────────────────────────────────────────────


def test_find_bundles_empty_makes_no_request() -> None:
    fake = FakeClient(lambda index, body: hits_response([]))
    assert registry.find_bundles(fake, [], None) == {}
    assert not fake.searches


def test_find_bundles_batches_of_500_and_maps_results() -> None:
    lids = [f"urn:nasa:pds:b:c{n}" for n in range(1100)]
    hits = [
        {
            "_id": "1",
            "_source": {"lidvid": "urn:nasa:pds:b::1.0", "ref_lid_collection": ["urn:nasa:pds:b:c0", "urn:unrelated"]},
            "sort": ["1"],
        },
        {"_id": "2", "_source": {"lidvid": "urn:nasa:pds:b::2.0", "ref_lid_collection": "urn:nasa:pds:b:c0"}, "sort": ["2"]},
    ]
    responses = [hits_response(hits), hits_response([]), hits_response([])]
    fake = FakeClient(lambda index, body: responses.pop(0))
    result = registry.find_bundles(fake, lids, ["atm"])
    assert result == {"urn:nasa:pds:b:c0": ["urn:nasa:pds:b::1.0", "urn:nasa:pds:b::2.0"]}
    assert len(fake.searches) == 3
    sizes = [len(body["query"]["bool"]["filter"][-1]["terms"][registry.BUNDLE_COLLECTION_REF_FIELD]) for _, body in fake.searches]
    assert sizes == [500, 500, 100]
    index, body = fake.searches[0]
    assert index == "atm-registry"
    assert {"term": {"product_class": "Product_Bundle"}} in body["query"]["bool"]["filter"]


# ── get_refs_coverage ─────────────────────────────────────────────────────────


def test_get_refs_coverage_query_bodies() -> None:
    collection = Collection(
        lidvid="urn:nasa:pds:b:c::1.0", lid="urn:nasa:pds:b:c", node="atm", stamp="7", ancestor_refs=[], harvest=None
    )
    fake = FakeClient(lambda index, body: {"aggregations": {"refs": {"value": 12.0}}}, counts=[10, 9])
    coverage = registry.get_refs_coverage(fake, collection, ["atm"], 7)

    assert coverage == RefsCoverage(refs_count=12, member_count=10, stamped_member_count=9)

    index, body = fake.searches[0]
    assert index == "atm-registry-refs"
    assert body["size"] == 0
    assert body["query"]["bool"]["filter"] == [{"term": {"collection_lidvid": "urn:nasa:pds:b:c::1.0"}}]
    assert body["aggs"]["refs"] == {"value_count": {"field": "product_lidvid"}}

    (members_index, members_body), (stamped_index, stamped_body) = fake.counted
    assert members_index == stamped_index == "atm-registry"
    wildcard = {"wildcard": {"lid": {"value": "urn:nasa:pds:b:c:*", "case_insensitive": True}}}
    members_bool = members_body["query"]["bool"]
    assert wildcard in members_bool["filter"]
    assert {"exists": {"field": "ops:Provenance/ops:superseded_by"}} in members_bool["must_not"]
    assert {"term": {STAMP_FIELD: "7"}} not in members_bool["filter"]

    stamped_bool = stamped_body["query"]["bool"]
    assert wildcard in stamped_bool["filter"]
    assert {"term": {STAMP_FIELD: "7"}} in stamped_bool["filter"]
    assert {"exists": {"field": REFS_FIELD}} in stamped_bool["filter"]


def test_get_refs_coverage_bad_aggregation_raises() -> None:
    collection = Collection(lidvid="l::1.0", lid="l", node="atm", stamp=None, ancestor_refs=[], harvest=None)
    fake = FakeClient(lambda index, body: {"hits": {}})
    with pytest.raises(RegistryQueryError):
        registry.get_refs_coverage(fake, collection, None, 7)


# ── tenant nodes ──────────────────────────────────────────────────────────────


def test_split_tenant_nodes_separates_index_prefixes_that_are_not_tenants() -> None:
    tenant, stale = registry.split_tenant_nodes(["atm", "edunn-geo", "geo", "temp-atm", "sandbox"])
    assert tenant == ["atm", "geo", "temp-atm"]  # temp-atm is the concrete index behind the atm alias
    assert stale == ["edunn-geo", "sandbox"]


def test_split_tenant_nodes_accepts_a_custom_tenant_list() -> None:
    assert registry.split_tenant_nodes(["a", "b"], ["a"]) == (["a"], ["b"])
    assert registry.split_tenant_nodes([]) == ([], [])
