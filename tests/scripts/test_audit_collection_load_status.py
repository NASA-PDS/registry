# flake8: noqa: D101,D102,D103,D107
"""Tests for the load-status check in scripts/audit_collection.py (no network)."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import audit_collection as ac
import pytest

NOW = datetime(2026, 11, 14, 12, 0, 0, tzinfo=timezone.utc)


def ts(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S.000000000Z")


def lv(name: str, version: str) -> str:
    return f"urn:nasa:pds:b:c:{name}::{version}"


def test_complete_when_every_inventory_product_is_loaded():
    inventory = {lv("a", "1.0"), lv("b", "1.0")}
    harvests = {lv("a", "1.0"): ts(30), lv("b", "1.0"): ts(20), lv("extra", "1.0"): ts(1)}
    status = ac.compute_load_status(inventory, harvests, NOW, 3)
    assert status.verdict == "complete"
    assert (status.loaded, status.not_loaded, status.registry_not_in_inventory) == (2, 0, 1)


def test_not_started_when_no_inventory_product_is_in_the_registry():
    inventory = {lv("a", "14.0"), lv("b", "14.0")}
    harvests = {lv("a", "13.1"): ts(1), lv("b", "13.1"): ts(1)}
    status = ac.compute_load_status(inventory, harvests, NOW, 3)
    assert status.verdict == "not_started"
    assert status.loaded == 0
    assert status.not_loaded == 2
    assert status.registry_not_in_inventory == 2
    assert status.latest_member_harvest is None


def test_loading_when_the_newest_loaded_member_is_recent():
    inventory = {lv("a", "14.0"), lv("b", "14.0"), lv("c", "14.0")}
    harvests = {lv("a", "14.0"): ts(10), lv("b", "14.0"): ts(0.5)}
    status = ac.compute_load_status(inventory, harvests, NOW, 3)
    assert status.verdict == "loading"
    assert status.latest_member_lidvid == lv("b", "14.0")
    assert status.latest_member_age_days == pytest.approx(0.5)
    assert status.not_loaded == 1


def test_stalled_when_the_newest_loaded_member_is_old():
    inventory = {lv("a", "14.0"), lv("b", "14.0"), lv("c", "14.0")}
    harvests = {lv("a", "14.0"): ts(40), lv("b", "14.0"): ts(12)}
    status = ac.compute_load_status(inventory, harvests, NOW, 3)
    assert status.verdict == "stalled"
    assert status.latest_member_age_days == pytest.approx(12)


def test_active_days_boundary_is_inclusive():
    inventory = {lv("a", "14.0"), lv("b", "14.0")}
    harvests = {lv("a", "14.0"): ts(3.0)}
    assert ac.compute_load_status(inventory, harvests, NOW, 3).verdict == "loading"
    harvests = {lv("a", "14.0"): ts(3.01)}
    assert ac.compute_load_status(inventory, harvests, NOW, 3).verdict == "stalled"


def test_recent_loads_of_products_outside_the_inventory_do_not_count_as_activity():
    # The registry's old 13.1 versions were harvested yesterday, but the 14.0 members stopped loading weeks ago.
    inventory = {lv("a", "14.0"), lv("b", "14.0"), lv("c", "14.0")}
    harvests = {lv("a", "14.0"): ts(30), lv("a", "13.1"): ts(0.1), lv("b", "13.1"): ts(0.1)}
    status = ac.compute_load_status(inventory, harvests, NOW, 3)
    assert status.verdict == "stalled"
    assert status.latest_member_age_days == pytest.approx(30)
    assert (NOW - status.latest_other_harvest).total_seconds() / 86400 == pytest.approx(0.1)


def test_unknown_when_loaded_members_have_no_harvest_time():
    inventory = {lv("a", "14.0"), lv("b", "14.0")}
    status = ac.compute_load_status(inventory, {lv("a", "14.0"): None}, NOW, 3)
    assert status.verdict == "unknown"
    assert status.latest_member_harvest is None


def test_nine_digit_fractional_seconds_are_parsed():
    inventory = {lv("a", "14.0"), lv("b", "14.0")}
    status = ac.compute_load_status(inventory, {lv("a", "14.0"): "2026-11-14T01:02:20.539048556Z"}, NOW, 3)
    assert status.latest_member_harvest == datetime(2026, 11, 14, 1, 2, 20, 539048, tzinfo=timezone.utc)


def test_report_states_the_verdict_and_the_remaining_count(capsys):
    inventory = {lv("a", "14.0"), lv("b", "14.0")}
    stalled = ac.compute_load_status(inventory, {lv("a", "14.0"): ts(30)}, NOW, 3)
    ac.print_load_status_report(stalled, 3)
    out = capsys.readouterr().out
    assert "not currently loading" in out
    assert "remaining 1 products" in out
    loading = ac.compute_load_status(inventory, {lv("a", "14.0"): ts(1)}, NOW, 3)
    ac.print_load_status_report(loading, 3)
    assert "still loading" in capsys.readouterr().out


def test_registry_harvests_pages_and_the_lidvid_wrapper_keeps_working(monkeypatch):
    pages = [
        {
            "hits": {
                "hits": [
                    {"_id": "1", "_source": {"lidvid": lv("a", "1.0"), ac._REGISTRY_HARVEST_FIELD: ["2026-01-01T00:00:00Z"]}, "sort": ["1"]},
                    {"_id": "2", "_source": {"lidvid": lv("b", "1.0")}, "sort": ["2"]},
                ]
            }
        }
    ]
    monkeypatch.setattr(ac, "run_registry_query", lambda query, index, auth, timeout: pages[0])
    harvests = ac.get_registry_harvests("urn:nasa:pds:b:c", None, "/*-registry/_count", object(), 5)
    assert harvests == {lv("a", "1.0"): "2026-01-01T00:00:00Z", lv("b", "1.0"): None}
    assert ac.get_all_registry_lidvids("urn:nasa:pds:b:c", None, "/*-registry/_count", object(), 5) == set(harvests)


def test_registry_harvests_skip_superseded_products_client_side(monkeypatch):
    # The query cannot exclude superseded products on every index, so they are dropped from the hits.
    superseded = "ops:Provenance/ops:superseded_by"
    page = {
        "hits": {
            "hits": [
                {"_id": "1", "_source": {"lidvid": lv("a", "2.0"), superseded: None}, "sort": ["1"]},
                {"_id": "2", "_source": {"lidvid": lv("a", "1.0"), superseded: lv("a", "2.0")}, "sort": ["2"]},
                {"_id": "3", "_source": {"lidvid": lv("b", "1.0"), superseded: [lv("b", "2.0")]}, "sort": ["3"]},
            ]
        }
    }
    seen = {}

    def fake_query(query, index, auth, timeout):
        seen["source"] = query["_source"]
        return page

    monkeypatch.setattr(ac, "run_registry_query", fake_query)
    harvests = ac.get_registry_harvests("urn:nasa:pds:b:c", None, "/*-registry/_count", object(), 5)
    assert set(harvests) == {lv("a", "2.0")}
    assert superseded in seen["source"]


def test_registry_harvests_returns_none_when_a_page_fails(monkeypatch):
    monkeypatch.setattr(ac, "run_registry_query", lambda query, index, auth, timeout: None)
    assert ac.get_registry_harvests("urn:nasa:pds:b:c", None, "/*-registry/_count", object(), 5) is None
    assert ac.get_all_registry_lidvids("urn:nasa:pds:b:c", None, "/*-registry/_count", object(), 5) is None
