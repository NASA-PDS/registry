#!/usr/bin/env python3
r"""Generate the registry report card: one row per node, graded green, yellow or red.

The card combines the status reports (loading, invalid file paths) with the data fidelity audits and grades each node
on four scores. Three belong to the node; the fourth, Index Health, belongs to EN (and the sweepers team):

  Loading          current bundles and collections not yet loaded, of all current bundles and collections (node)
  File paths       products, collections and bundles with an invalid ``file_ref``, of the node's visible products (node)
  Fidelity         visible products without ancestry that the node has to fix or that need a closer look, of the
                   node's visible products (node)
  Index Health     EN's own problems: products without ancestry that EN's sweepers and repairs left behind (a collection
                   stamped before its products were loaded, products a node overwrote that the sweepers never
                   revisited, a loaded collection the sweepers never processed), products the sweepers team owns,
                   collections stamped without a link to their bundle, and index mapping problems on the fields the
                   API relies on (EN)

Who owns a product without ancestry is computed from the audit's per-rule counts with the current ``ownership``
mapping, so older ``metrics.json`` files are scored by the same rules as new ones. A ``metrics.json`` without rule
counts falls back to its stored ``owners``.

A score is green with no issues, yellow with issues below ``yellow_below_percent`` of the node's items (default 5),
and red from that percentage up. Index mappings count only for the fields the API relies on (``api_mapping_fields``
in the configuration): such a field that is missing from a node's mapping, or mapped with a type other than the
other nodes' (``text`` and ``keyword`` count as the same), is red. Every other mapping difference is ignored.
A node is as good as the worst of its three scores; Index Health is shown beside it, not folded in. A green
score whose data is older than ``stale_after_days`` is shown as stale, since it cannot be trusted.

Inputs (all read-only, local files):

  <status-dir>/burnup_by_node_latest.csv      loaded and target counts per status node
  <status-dir>/counts_history.csv             date of the status reports
  <status-dir>/bad_file_ref_*_in_registry.csv invalid file_ref values per status node
  <fidelity-dir>/<node>/metrics.json          audit metrics per node (from audit_unprocessed_products.py)
  <fidelity-dir>/index-mappings/              mapping_discrepancies.csv and mapping_summary.md
  <fidelity-dir>/node_totals.json             API-visible products per node (from collect_node_totals.py)

Files written to --output-dir:

  report_card.html   the page
  report_card.md     the same table for GitHub
  report_card.json   scores and counts, for other tools

Usage:
    python scripts/generate_report_card.py [--status-dir docs/status] [--fidelity-dir docs/status/fidelity]
                                           [--config conf/status/report_card.json] [--output-dir docs/status]

Options:
    --status-dir DIR    Directory with the status report CSVs (default: docs/status)
    --fidelity-dir DIR  Directory with the fidelity audit outputs (default: <status-dir>/fidelity)
    --config FILE       Rubric and node list (default: conf/status/report_card.json)
    --output-dir DIR    Directory to write the card to (default: <status-dir>)
    --today DATE        Treat DATE (YYYY-MM-DD) as today when checking for stale data (default: today)

Exit codes: 0 on success, 1 on an unreadable input, 2 on invalid arguments.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import logging
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unprocessed_audit import ownership  # noqa: E402

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "conf" / "status" / "report_card.json"


class ReportCardError(Exception):
    """An input of the report card is missing or malformed."""


class Status(Enum):
    """The grade of one score."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    STALE = "stale"
    NO_DATA = "no data"


_SEVERITY = {Status.GREEN: 0, Status.STALE: 1, Status.NO_DATA: 1, Status.YELLOW: 2, Status.RED: 3}
_SYMBOL = {Status.GREEN: "●", Status.YELLOW: "▲", Status.RED: "■", Status.STALE: "◌", Status.NO_DATA: "–"}


def worst(statuses: list[Status]) -> Status:
    """Return the worst of several grades; an empty list has no data."""
    if not statuses:
        return Status.NO_DATA
    return max(statuses, key=lambda s: _SEVERITY[s])


def grade(issues: int, total: int, yellow_below_percent: float) -> Status:
    """Grade a count of issues against the number of items it is counted out of.

    Args:
        issues: Items with a problem.
        total: Items checked.
        yellow_below_percent: Issues below this percentage of ``total`` are yellow; at or above it, red.

    Returns:
        Green for no issues; red for issues with nothing to count them out of.
    """
    if issues <= 0:
        return Status.GREEN
    if total <= 0:
        return Status.RED
    return Status.YELLOW if 100.0 * issues / total < yellow_below_percent else Status.RED


@dataclass(frozen=True)
class Link:
    """A deep-dive page."""

    label: str
    url: str


@dataclass(frozen=True)
class Score:
    """One graded score of a node.

    Attributes:
        status: The grade.
        issues: Items with a problem.
        total: Items checked.
        detail: One line saying what was counted.
        as_of: Date of the data, if known.
        links: Deep-dive pages.
        stale: ``True`` when the data is older than the limit.
    """

    status: Status
    issues: int | None = None
    total: int | None = None
    detail: str = ""
    as_of: date | None = None
    links: list[Link] = field(default_factory=list)
    stale: bool = False

    @property
    def share(self) -> str:
        """The issues as ``n of total (p%)``, or an empty string when there is nothing to count."""
        if not self.issues or not self.total:
            return ""
        percent = 100.0 * self.issues / self.total
        shown = "<0.01" if percent < 0.01 else f"{percent:.2f}"
        return f"{self.issues:,} of {self.total:,} ({shown}%)"

    @property
    def percent(self) -> float | None:
        """Issues as a percentage of the items checked."""
        if self.issues is None or not self.total:
            return None
        return 100.0 * self.issues / self.total


@dataclass(frozen=True)
class NodeCard:
    """The scores of one node."""

    node: str
    label: str
    loading: Score
    file_paths: Score
    fidelity: Score
    health: Score
    shared_note: str = ""

    @property
    def en_issues(self) -> bool:
        """``True`` when EN owns open issues on this node (Index Health is not green); they are not in the node status."""
        return self.health.status in (Status.YELLOW, Status.RED)

    @property
    def overall(self) -> Status:
        """The worst of the node's three scores (Index Health is EN's and is not included)."""
        return worst([self.loading.status, self.file_paths.status, self.fidelity.status])


@dataclass(frozen=True)
class Config:
    """The rubric and the node list."""

    yellow_below_percent: float
    stale_after_days: int
    base_url: str
    latest_report: str
    nodes: list[dict]
    api_mapping_fields: frozenset[str] = frozenset()


def load_config(path: Path) -> Config:
    """Read the rubric file.

    Raises:
        ReportCardError: If the file is missing or malformed.
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return Config(
            float(raw["yellow_below_percent"]),
            int(raw["stale_after_days"]),
            str(raw["base_url"]).rstrip("/"),
            str(raw["latest_report"]).strip("/"),
            list(raw["nodes"]),
            frozenset(raw.get("api_mapping_fields", [])),
        )
    except (OSError, ValueError, KeyError) as exc:
        raise ReportCardError(f"Cannot read the report card configuration {path}: {exc}") from exc


# ── readers ───────────────────────────────────────────────────────────────────


def _rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV file as dictionaries; a missing file has no rows."""
    if not Path(path).exists():
        return []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_loading(status_dir: Path) -> dict[str, tuple[int, int, int]]:
    """Return ``{status node: (not yet loaded, current bundles and collections, current collections)}``.

    The counts come from the latest burnup row of each node.
    """
    latest: dict[str, dict[str, str]] = {}
    for row in _rows(Path(status_dir) / "burnup_by_node_latest.csv"):
        if row["node"] not in latest or row["date"] >= latest[row["node"]]["date"]:
            latest[row["node"]] = row
    result: dict[str, tuple[int, int, int]] = {}
    for node, row in latest.items():
        loaded_b, loaded_c = int(row["cumulative_bundles"]), int(row["cumulative_collections"])
        target_b, target_c = int(row["target_bundles"]), int(row["target_collections"])
        result[node] = (max(target_b - loaded_b, 0) + max(target_c - loaded_c, 0), target_b + target_c, target_c)
    return result


def read_status_date(status_dir: Path) -> date | None:
    """Return the date of the last status report run, from ``counts_history.csv``."""
    rows = _rows(Path(status_dir) / "counts_history.csv")
    return _parse_date(rows[-1]["date"]) if rows else None


def read_bad_file_refs(status_dir: Path) -> dict[str, int]:
    """Return ``{status node: products, collections and bundles with an invalid file_ref}``."""
    counts: dict[str, int] = {}
    for kind in ("bundles", "collections"):
        seen: set[tuple[str, str]] = set()
        for row in _rows(Path(status_dir) / f"bad_file_ref_{kind}_in_registry.csv"):
            seen.add((row["node"], row["lidvid"]))
        for node, _ in seen:
            counts[node] = counts.get(node, 0) + 1
    for row in _rows(Path(status_dir) / "bad_file_ref_products_in_registry.csv"):
        counts[row["node"]] = counts.get(row["node"], 0) + int(row["products"])
    return counts


def read_metrics(fidelity_dir: Path, node: str) -> dict | None:
    """Return a node's audit ``metrics.json``, or ``None`` when the node has no audit."""
    path = Path(fidelity_dir) / node / "metrics.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReportCardError(f"Cannot read {path}: {exc}") from exc


def owner_counts(metrics: Mapping[str, Any]) -> dict[str, int]:
    """Return a node's product count per owner under the current ownership mapping.

    The counts come from the audit's ``rules`` (and ``unverified_refs_missing``), not from the ``owners`` stored in
    ``metrics.json``, so a metrics file written under an earlier ownership is scored like a new one. Without ``rules``
    the stored ``owners`` are used.
    """
    rules = metrics.get("rules")
    if isinstance(rules, dict):
        unverified = int(metrics.get("unverified_refs_missing") or 0)
        return ownership.count_by_owner({str(rule): int(count) for rule, count in rules.items()}, unverified)
    stored = metrics.get("owners")
    return {str(owner): int(count) for owner, count in stored.items()} if isinstance(stored, dict) else {}


def read_totals(fidelity_dir: Path) -> tuple[dict[str, int], date | None]:
    """Return the API-visible products per node and the date they were counted."""
    path = Path(fidelity_dir) / "node_totals.json"
    if not path.exists():
        return {}, None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {k: int(v) for k, v in raw["visible_products"].items()}, _parse_date(raw.get("generated"))
    except (OSError, ValueError, KeyError) as exc:
        raise ReportCardError(f"Cannot read {path}: {exc}") from exc


_TEXT_TYPES = frozenset({"text", "keyword"})


def read_mapping(fidelity_dir: Path, api_fields: frozenset[str]) -> tuple[dict[str, list[str]], date | None]:
    """Return the mapping problems on the fields the API relies on, per node, and the date of the run.

    A field is a problem when it is missing from the node's index, or mapped with a type other than the other
    nodes' one. ``text`` against ``keyword`` is not a problem. Fields the API does not rely on are ignored.

    Returns:
        ``({node: [field, ...]}, run date)`` for the registry indices.
    """
    folder = Path(fidelity_dir) / "index-mappings"
    problems: dict[str, list[str]] = {}
    for row in _rows(folder / "mapping_discrepancies.csv"):
        if row["group"] != "registry" or row["field"] not in api_fields:
            continue
        if row["kind"] == "type_mismatch" and {row["expected"], row["actual"]} <= _TEXT_TYPES:
            continue
        node = row["node"].removeprefix("temp-")  # the ATM products index is temp-atm-registry behind atm-registry
        problems.setdefault(node, []).append(row["field"])
    run_date = None
    summary = folder / "mapping_summary.md"
    if summary.exists():
        match = re.search(r"^Run time: (\S+)", summary.read_text(encoding="utf-8"), re.MULTILINE)
        run_date = _parse_date(match.group(1)) if match else None
    return problems, run_date


def has_mapping(fidelity_dir: Path) -> bool:
    """Return ``True`` when the index mapping audit output is present."""
    return (Path(fidelity_dir) / "index-mappings" / "mapping_discrepancies.csv").exists()


def _parse_date(raw: str | None) -> date | None:
    """Parse an ISO date or timestamp; anything else is unknown."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


# ── scoring ───────────────────────────────────────────────────────────────────


def _link(config: Config, label: str, path: str) -> Link:
    return Link(label, f"{config.base_url}/{path}")


def _apply_stale(score: Score, today: date, stale_after_days: int) -> Score:
    """Mark a score stale when its data is too old; a stale green score is no longer green."""
    if score.as_of is None or (today - score.as_of).days <= stale_after_days:
        return score
    status = Status.STALE if score.status is Status.GREEN else score.status
    return Score(status, score.issues, score.total, score.detail, score.as_of, score.links, True)


def _no_data(detail: str, links: list[Link] | None = None) -> Score:
    return Score(Status.NO_DATA, detail=detail, links=links or [])


@dataclass
class Inputs:
    """Everything the report card reads."""

    loading: dict[str, tuple[int, int, int]]
    status_date: date | None
    bad_refs: dict[str, int]
    totals: dict[str, int]
    totals_date: date | None
    metrics: dict[str, dict | None]
    mapping: dict[str, list[str]]
    mapping_date: date | None
    mapping_present: bool


def load_inputs(status_dir: Path, fidelity_dir: Path, nodes: list[str], api_fields: frozenset[str]) -> Inputs:
    """Read every input of the card.

    Raises:
        ReportCardError: If an input exists but cannot be read.
    """
    totals, totals_date = read_totals(fidelity_dir)
    mapping, mapping_date = read_mapping(fidelity_dir, api_fields)
    return Inputs(
        read_loading(status_dir),
        read_status_date(status_dir),
        read_bad_file_refs(status_dir),
        totals,
        totals_date,
        {node: read_metrics(fidelity_dir, node) for node in nodes},
        mapping,
        mapping_date,
        has_mapping(fidelity_dir),
    )


def score_node(entry: dict, data: Inputs, config: Config, today: date) -> NodeCard:
    """Grade one node.

    Args:
        entry: The node's entry in the configuration.
        data: The inputs.
        config: The rubric.
        today: The date to measure staleness from.

    Returns:
        The node's four scores.
    """
    node, status_node = entry["node"], entry["status_node"]
    group = entry.get("shared_with") or [node]
    shared_note = "Loading and file paths are counted for all of SBN (PSI and UMD)." if len(group) > 1 else ""
    limit = config.yellow_below_percent
    products = sum(data.totals.get(n, 0) for n in group) if all(n in data.totals for n in group) else None

    # Loading
    loading_links = [
        _link(config, "Bundles", "status/missing_bundles_in_registry.csv"),
        _link(config, "Collections", "status/missing_collections_in_registry.csv"),
        _link(config, "Burnup", "status/burnup_chart.html"),
    ]
    if status_node in data.loading:
        missing, current, _ = data.loading[status_node]
        loading = Score(
            grade(missing, current, limit), missing, current,
            f"{missing:,} of {current:,} current bundles and collections not loaded", data.status_date, loading_links,
        )
    else:
        loading = _no_data("No loading data for this node", loading_links)

    # File paths
    path_links = [
        _link(config, "Bundles", "status/bad_file_ref_bundles_in_registry.csv"),
        _link(config, "Collections", "status/bad_file_ref_collections_in_registry.csv"),
        _link(config, "Products", "status/bad_file_ref_products_in_registry.csv"),
    ]
    if products is None:
        file_paths = _no_data("The node's product count is missing (run collect_node_totals.py)", path_links)
    else:
        bad = data.bad_refs.get(status_node, 0)
        file_paths = Score(
            grade(bad, products, limit), bad, products,
            f"{bad:,} of {products:,} products, collections and bundles with an invalid file path",
            data.status_date, path_links,
        )

    # Fidelity and Index Health
    metrics = data.metrics.get(node)
    fidelity_links = [
        _link(config, "Report", f"{config.latest_report}/nodes/{node}.md"),
        _link(config, "Summary", f"status/fidelity/{node}/summary.md"),
    ]
    if metrics is None or products is None:
        why = "No fidelity audit for this node" if metrics is None else "The node's product count is missing"
        fidelity, health = _no_data(why, fidelity_links), _no_data(why, fidelity_links)
    else:
        visible = data.totals[node]
        run = _parse_date(metrics.get("run_time"))
        owners = owner_counts(metrics)
        node_issues = int(owners.get("node", 0)) + int(owners.get("needs_check", 0))
        fidelity = Score(
            grade(node_issues, visible, limit), node_issues, visible,
            f"{node_issues:,} of {visible:,} visible products without ancestry that the node or a closer look must resolve",
            run, fidelity_links,
        )
        collections = data.loading.get(status_node, (0, 0, 0))[2]
        health = _score_health(node, metrics, visible, collections, data, config, run, fidelity_links)

    cards = [
        _apply_stale(loading, today, config.stale_after_days),
        _apply_stale(file_paths, today, config.stale_after_days),
        _apply_stale(fidelity, today, config.stale_after_days),
        _apply_stale(health, today, config.stale_after_days),
    ]
    return NodeCard(node, entry["label"], cards[0], cards[1], cards[2], cards[3], shared_note)


def _score_health(
    node: str, metrics: dict, visible: int, collections: int, data: Inputs, config: Config, run: date | None,
    links: list[Link],
) -> Score:
    """Grade Index Health: EN's products to repair, the sweepers team's, collections without a bundle link, mappings."""
    limit = config.yellow_below_percent
    owners = owner_counts(metrics)
    en_products, sweepers_products = int(owners.get("en", 0)), int(owners.get("sweepers_team", 0))
    unlinked = len(metrics.get("empty_refs_with_bundle", []))
    products_status = grade(en_products + sweepers_products, visible, limit)
    parts = []
    if en_products:
        parts.append(
            (
                products_status,
                f"EN to repair (stamped before loaded, overwritten, never processed): {en_products:,} products",
            )
        )
    if sweepers_products:
        parts.append((products_status, f"Sweepers team: {sweepers_products:,} products"))
    parts.append((grade(unlinked, collections, limit), f"Collections without a bundle link (EN): {unlinked:,}"))
    as_of = run
    if data.mapping_present:
        fields = data.mapping.get(node, [])
        listed = ", ".join(sorted(set(fields)))
        parts.append((Status.RED if fields else Status.GREEN, f"Index mapping problems on API fields (EN): {listed}"))
        as_of = min([d for d in (run, data.mapping_date) if d], default=run)
    links = [links[0], _link(config, "Index mappings", "status/fidelity/index-mappings/mapping_summary.md")]
    status = worst([s for s, _ in parts])
    detail = "; ".join(text for s, text in parts if s is not Status.GREEN) or "No registry-side issues"
    return Score(status, None, None, detail, as_of, links)


# ── rendering ─────────────────────────────────────────────────────────────────

_CSS = """
:root{--bg:#fff;--fg:#1d2430;--muted:#5b6575;--line:#d5dae1;--card:#f6f8fa;--green:#1a7f37;--yellow:#9a6700;--red:#cf222e;--grey:#6e7781;
--green-bg:#dafbe1;--yellow-bg:#fff8c5;--red-bg:#ffebe9;--grey-bg:#eaeef2;--link:#0969da}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--muted:#9aa4b2;--line:#30363d;--card:#161b22;
--green:#56d364;--yellow:#e3b341;--red:#ff7b72;--grey:#9aa4b2;--green-bg:#12261e;--yellow-bg:#2b230b;--red-bg:#2d1315;--grey-bg:#1f2630;--link:#58a6ff}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--muted:#9aa4b2;--line:#30363d;--card:#161b22;--green:#56d364;--yellow:#e3b341;--red:#ff7b72;
--grey:#9aa4b2;--green-bg:#12261e;--yellow-bg:#2b230b;--red-bg:#2d1315;--grey-bg:#1f2630;--link:#58a6ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.1rem;margin:28px 0 8px}
p,li{color:var(--fg)}.muted{color:var(--muted)}a{color:var(--link)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;min-width:1000px;table-layout:fixed}
th:nth-child(1){width:15%}th:nth-child(2){width:11%}
th,td{padding:10px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--card);font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}
tr:last-child td{border-bottom:0}th small{display:block;text-transform:none;letter-spacing:0;font-weight:400}
.node{font-weight:600}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-weight:600;font-size:.85rem;white-space:nowrap}
.green{color:var(--green);background:var(--green-bg)}.yellow{color:var(--yellow);background:var(--yellow-bg)}
.red{color:var(--red);background:var(--red-bg)}.stale,.no-data{color:var(--grey);background:var(--grey-bg)}
.count{display:block;font-size:.85rem;margin-top:4px;overflow-wrap:anywhere}.links{display:block;font-size:.8rem;margin-top:2px}
.links a{margin-right:8px}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:12px 0}
.rubric{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 16px}
@media (max-width:640px){main{padding:16px}}
"""  # noqa: B950


def _chip(status: Status, en: bool = False) -> str:
    css = status.value.replace(" ", "-")
    star = '<abbr title="EN\'s problem, not the node\'s">*</abbr>' if en else ""
    return f'<span class="chip {css}">{_SYMBOL[status]} {html.escape(status.value.capitalize())}{star}</span>'


def _cell(score: Score, en: bool = False) -> str:
    parts = [_chip(score.status, en)]
    if score.share:
        parts.append(f'<span class="count">{html.escape(score.share)}</span>')
    elif score.issues == 0 and score.total is not None:
        parts.append(f'<span class="count">0 of {score.total:,}</span>')
    if score.detail and score.status is not Status.GREEN and score.issues is None:
        for line in score.detail.split("; "):
            parts.append(f'<span class="count muted">{html.escape(line)}</span>')
    if score.stale and score.as_of:
        parts.append(f'<span class="count muted">data from {score.as_of.isoformat()}</span>')
    if score.links:
        links = "".join(f'<a href="{html.escape(link.url)}">{html.escape(link.label)}</a>' for link in score.links)
        parts.append(f'<span class="links">{links}</span>')
    return "<td>" + "".join(parts) + "</td>"


def render_html(cards: list[NodeCard], config: Config, today: date) -> str:
    """Render the report card page."""
    limit = f"{config.yellow_below_percent:g}"
    rows = []
    for card in cards:
        note = f'<span class="count muted">{html.escape(card.shared_note)}</span>' if card.shared_note else ""
        rows.append(
            f'<tr><td class="node">{html.escape(card.label)}{note}</td><td>{_chip(card.overall, card.en_issues)}</td>'
            f"{_cell(card.loading)}{_cell(card.file_paths)}{_cell(card.fidelity)}{_cell(card.health, True)}</tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Registry Report Card</title><style>{_CSS}</style></head>
<body><main>
<h1>Registry Report Card</h1>
<p class="muted">Generated {today.isoformat()}. One row per node. Each score links to the page with the details and the list of what to fix.</p>
<div class="legend">{_chip(Status.GREEN)} no issues {_chip(Status.YELLOW)} issues below {limit}% {_chip(Status.RED)} {limit}% or more
{_chip(Status.STALE)} data older than {config.stale_after_days} days {_chip(Status.NO_DATA)} not measured</div>
<div class="scroll"><table>
<thead><tr><th>Node</th><th>Node status<small>worst of the next three</small></th><th>Loading<small>node</small></th>
<th>File paths<small>node</small></th><th>Fidelity<small>node</small></th><th>Index Health *<small>EN's problems</small></th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<p class="muted">* EN's problem, not the node's. Every Index Health issue is EN's or the sweepers team's to fix: collections the sweepers stamped before their products were loaded, products a node overwrote that the sweepers never revisited, collections without a link to their bundle, loaded collections the sweepers never processed, and index mappings. A node status marked * also has open Index Health issues; they are not counted in the node status.</p>
<h2>How the scores work</h2>
<div class="rubric"><ul>
<li><strong>Loading</strong>: current bundles and collections that are not yet in the registry, of all current ones.</li>
<li><strong>File paths</strong>: products, collections and bundles with an invalid <code>file_ref</code>, of the node's visible products.</li>
<li><strong>Fidelity</strong> (the node's): visible products without ancestry (missing from their collection's and bundle's <code>/members</code>) that the node must fix, or that need a closer look, of the node's visible products. These are a collection that is not loaded, an inventory that lists another version of the product or omits it, and a collection whose inventory lists the product but whose refs do not. Products still within the grace period are not counted.</li>
<li><strong>Index Health</strong> (EN's problems and the sweepers team's, not the node's): collections the sweepers stamped before their products were loaded and never revisited, and products a node overwrote that the sweepers never revisited (EN runs the ancestry orphan repair for both); collections without a link to their bundle (EN runs the bundle-link pass); loaded collections the sweepers never processed; products the sweepers team owns; and index mapping problems. Only the fields the API relies on count (<code>lid</code>, <code>lidvid</code>, <code>vid</code>, the archive status, <code>superseded_by</code> and <code>ancestor_refs</code>): one that is missing from the node's mapping, or mapped with a different type from the other nodes (text and keyword count as the same), makes the score red. Other mapping differences are ignored.</li>
<li>Green is no issues. Yellow is some issues, but below {limit}% of the node's items. Red is {limit}% or more of the items, which is enough to harm users of the registry. A node's status is the worst of Loading, File paths and Fidelity, which are the node's. Index Health is EN's and is shown beside the node status, not in it.</li>
</ul></div>
</main></body></html>
"""  # noqa: B950


def render_markdown(cards: list[NodeCard], config: Config, today: date) -> str:
    """Render the same card as a Markdown table."""
    limit = f"{config.yellow_below_percent:g}"

    def md(score: Score, en: bool = False) -> str:
        text = f"{_SYMBOL[score.status]} {score.status.value.capitalize()}{' \\*' if en else ''}"
        if score.share:
            text += f": {score.share}"
        return text

    lines = [
        "# Registry Report Card",
        "",
        f"Generated {today.isoformat()}. Green: no issues. Yellow: issues below {limit}% of the node's items. "
        f"Red: {limit}% or more. Stale: data older than {config.stale_after_days} days. "
        "Loading, File paths and Fidelity are the node's. \\* Index Health is EN's problem, not the node's: "
        "collections the sweepers stamped before their products were loaded, products a node overwrote that the "
        "sweepers never revisited, collections without a link to their bundle, loaded collections the sweepers "
        "never processed, and index mappings. A node status marked \\* also has open Index Health issues, which are "
        "not counted in the node status.",
        "",
        "| Node | Node status | Loading | File paths | Fidelity | Index Health * |",
        "|---|---|---|---|---|---|",
    ]
    for card in cards:
        lines.append(
            f"| {card.label} | {_SYMBOL[card.overall]} {card.overall.value.capitalize()}{' \\*' if card.en_issues else ''} | "
            f"{md(card.loading)} | {md(card.file_paths)} | {md(card.fidelity)} | {md(card.health, True)} |"
        )
    return "\n".join(lines) + "\n"


def render_json(cards: list[NodeCard]) -> str:
    """Render the scores for other tools."""

    def one(score: Score) -> dict:
        return {
            "status": score.status.value, "issues": score.issues, "total": score.total, "detail": score.detail,
            "as_of": score.as_of.isoformat() if score.as_of else None, "stale": score.stale,
        }

    document = {
        card.node: {
            "overall": card.overall.value,
            "en_issues": card.en_issues,
            "loading": one(card.loading),
            "file_paths": one(card.file_paths),
            "fidelity": one(card.fidelity),
            "index_health": one(card.health),
        }
        for card in cards
    }
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def build_cards(status_dir: Path, fidelity_dir: Path, config: Config, today: date) -> list[NodeCard]:
    """Read the inputs and grade every configured node."""
    data = load_inputs(status_dir, fidelity_dir, [entry["node"] for entry in config.nodes], config.api_mapping_fields)
    return [score_node(entry, data, config, today) for entry in config.nodes]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Generate the registry report card.")
    parser.add_argument("--status-dir", type=Path, default=Path("docs/status"))
    parser.add_argument("--fidelity-dir", type=Path)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--today", type=date.fromisoformat)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 on success, 1 on an unreadable input.
    """
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")
    fidelity_dir = args.fidelity_dir or args.status_dir / "fidelity"
    output_dir = args.output_dir or args.status_dir
    today = args.today or date.today()
    try:
        config = load_config(args.config)
        cards = build_cards(args.status_dir, fidelity_dir, config, today)
    except ReportCardError:
        logger.exception("Cannot build the report card")
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report_card.html").write_text(render_html(cards, config, today), encoding="utf-8")
    (output_dir / "report_card.md").write_text(render_markdown(cards, config, today), encoding="utf-8")
    (output_dir / "report_card.json").write_text(render_json(cards), encoding="utf-8")
    for card in cards:
        logger.info("%s: %s", card.label, card.overall.value)
    print(f"Wrote the report card to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
