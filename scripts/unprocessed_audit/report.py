"""Output writers, tallies and Markdown rendering for the unprocessed product audit.

Everything here is driven one product at a time so the audit never holds millions of rows in memory:

* ``ProductCsvWriter`` streams ``unprocessed_products.csv`` to disk (optionally gzipped).
* ``Tally`` accumulates bounded counters (per rule, node, class, age bucket and affected collection).
* ``record_key`` / ``load_previous_keys`` / ``compute_diff`` compare two runs using 64-bit hashes
  instead of full strings.
* ``render_summary`` turns the tally into the ``summary.md`` report.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import re
from collections import Counter
from collections.abc import Collection as CollectionABC
from collections.abc import Iterable
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import IO
from typing import Any

from unprocessed_audit import ownership
from unprocessed_audit.classify import RULE_GUIDANCE
from unprocessed_audit.classify import age_days
from unprocessed_audit.classify import derive_collection_lid
from unprocessed_audit.model import Candidate
from unprocessed_audit.model import Collection
from unprocessed_audit.model import CollectionState
from unprocessed_audit.model import RefsCoverage
from unprocessed_audit.model import Rule
from unprocessed_audit.model import Severity
from unprocessed_audit.model import Thresholds
from unprocessed_audit.model import Verdict

PRODUCT_COLUMNS = [
    "node",
    "lidvid",
    "product_class",
    "population",
    "stamp_version",
    "has_ancestor_refs",
    "harvest_date_time",
    "harvest_age_days",
    "bundle_lid",
    "collection_lidvid",
    "collection_state",
    "collection_harvest_date_time",
    "in_refs",
    "rule",
    "severity",
    "rationale",
]
"""Columns of ``unprocessed_products.csv``, in order."""

COLLECTION_COLUMNS = [
    "node",
    "collection_lidvid",
    "state",
    "stamp_version",
    "ancestor_refs_count",
    "harvest_date_time",
    "bundle_lidvids",
    "anomalous_product_count",
    "refs_count",
    "member_count",
    "stamped_member_count",
    "coverage_note",
    "superseded_by",
]
"""Columns of ``collections.csv``, in order."""

AGE_BUCKETS = ("<=1d", "1-7d", "7-30d", ">30d", "unknown")
"""Age buckets for product harvest age, in display order."""

PENDING_RULES = (
    Rule.COLLECTION_NOT_LOADED_PENDING,
    Rule.COLLECTION_PENDING,
    Rule.REFS_MISSING_PENDING,
)
"""Rules that should resolve on their own as the sweeper and loaders catch up."""

NOT_LOADED_RULES = (Rule.COLLECTION_NOT_LOADED_PENDING, Rule.COLLECTION_NOT_LOADED_OVERDUE)
"""Rules for products whose parent collection has no API-visible document (orphans)."""

_BUNDLE_LID_PATTERN = re.compile(r"^urn:[^:]+:[^:]+:[^:]+(?:::[^:]+)?$")
"""A bundle LID(VID) has four URN segments; collection LIDs have five."""

_MAX_BUNDLES_SHOWN = 3
_DEFAULT_MAX_ROWS = 50


# ── helpers ───────────────────────────────────────────────────────────────────


def _fmt_ts(when: datetime | None) -> str:
    """Format a timestamp for CSV and Markdown, or an empty string when absent."""
    return when.isoformat(timespec="seconds") if when is not None else ""


def _fmt_bool(value: bool | None) -> str:
    """Format an optional boolean as ``true``, ``false`` or an empty string."""
    if value is None:
        return ""
    return "true" if value else "false"


def _rule_value(rule: Rule | str) -> str:
    """Return the string value of a rule given either the enum member or its value."""
    return rule.value if isinstance(rule, Rule) else str(rule)


def age_bucket(age: float | None) -> str:
    """Map a harvest age in days to its display bucket.

    Args:
        age: Age in days, or ``None`` when the harvest time is unknown.

    Returns:
        One of ``AGE_BUCKETS``.
    """
    if age is None:
        return "unknown"
    if age <= 1:
        return "<=1d"
    if age <= 7:
        return "1-7d"
    if age <= 30:
        return "7-30d"
    return ">30d"


def coverage_note(coverage: RefsCoverage | None) -> str:
    """Describe in plain text how well refs cover a collection's members.

    Args:
        coverage: Coverage numbers, or ``None`` when they were not computed.

    Returns:
        An empty string when coverage is unknown, otherwise a one-line explanation.
    """
    if coverage is None:
        return ""
    if coverage.refs_count < coverage.member_count:
        missing = coverage.member_count - coverage.refs_count
        return f"refs missing for {missing} members (refs never written)"
    if coverage.stamped_member_count < coverage.member_count:
        unstamped = coverage.member_count - coverage.stamped_member_count
        return f"refs complete but {unstamped} members not stamped (sweeper skipped them)"
    return "ok"


def record_key(lidvid: str, rule: Rule | str) -> int:
    """Hash a (product, rule) pair to a 64-bit integer for run-to-run diffs.

    Args:
        lidvid: Product LIDVID.
        rule: The rule (enum member or its string value).

    Returns:
        A stable 64-bit key.
    """
    digest = hashlib.blake2b(f"{lidvid}\t{_rule_value(rule)}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def _open_text(path: Path, mode: str) -> IO[str]:
    """Open ``path`` as UTF-8 text, transparently gzipped when it ends in ``.gz``."""
    if path.suffix == ".gz":
        return gzip.open(path, mode + "t", encoding="utf-8", newline="")  # type: ignore[return-value]
    return open(path, mode, encoding="utf-8", newline="")


# ── products CSV ──────────────────────────────────────────────────────────────


class ProductCsvWriter:
    """Context manager that streams classified products to ``unprocessed_products.csv``.

    The file is gzip-compressed when the path ends in ``.gz``. Rows are written as they arrive and the
    file is closed (flushing what was written) even if the audit fails part-way through.
    """

    def __init__(self, path: Path) -> None:
        """Remember the destination.

        Args:
            path: File to write; parent directories are created on entry.
        """
        self.path = Path(path)
        self.rows_written = 0
        self._handle: IO[str] | None = None
        self._writer: Any = None

    def __enter__(self) -> ProductCsvWriter:
        """Open the file and write the header row."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = _open_text(self.path, "w")
        self._writer = csv.writer(self._handle)
        self._writer.writerow(PRODUCT_COLUMNS)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the file."""
        self.close()

    def close(self) -> None:
        """Close the underlying file if it is open."""
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def write(self, candidate: Candidate, verdict: Verdict, now: datetime) -> None:
        """Append one row.

        Args:
            candidate: The product that was classified.
            verdict: The classification outcome.
            now: Reference time used for the age column.
        """
        if self._writer is None:
            raise ValueError("ProductCsvWriter must be used as a context manager")
        age = age_days(candidate.harvest, now)
        self._writer.writerow(
            [
                candidate.node,
                candidate.lidvid,
                candidate.product_class,
                verdict.population.value,
                candidate.stamp or "",
                _fmt_bool(candidate.has_ancestor_refs),
                _fmt_ts(candidate.harvest),
                f"{age:.2f}" if age is not None else "",
                verdict.bundle_lid or "",
                verdict.collection_lidvid or "",
                verdict.collection_state.value if verdict.collection_state else "",
                _fmt_ts(verdict.collection_harvest),
                _fmt_bool(verdict.in_refs),
                verdict.rule.value,
                verdict.severity.value,
                verdict.rationale,
            ]
        )
        self.rows_written += 1


# ── tally ─────────────────────────────────────────────────────────────────────


@dataclass
class CollectionImpact:
    """Anomalous products attributed to one collection.

    Attributes:
        node: Node the products are registered under.
        bundle_lid: Bundle LID derived from a product LID, if derivable.
        state: Collection state value as seen on the verdicts, if known.
        harvest: Collection harvest time as seen on the verdicts, if known.
        rule_counts: Anomalous product counts per rule value.
    """

    node: str
    bundle_lid: str | None = None
    state: str | None = None
    harvest: datetime | None = None
    rule_counts: Counter[str] = field(default_factory=Counter)

    @property
    def total(self) -> int:
        """Total anomalous products attributed to the collection."""
        return sum(self.rule_counts.values())


@dataclass
class OrphanInfo:
    """Products whose derived parent collection has no API-visible document.

    Attributes:
        node: Node the products are registered under.
        pending: Products still within the product grace period.
        overdue: Products past the product grace period.
    """

    node: str
    pending: int = 0
    overdue: int = 0

    @property
    def total(self) -> int:
        """Total orphaned products for the collection LID."""
        return self.pending + self.overdue


class Tally:
    """Incremental, memory-bounded accumulator of audit results.

    State is bounded by the number of rules, nodes, product classes and collections, never by the
    number of products. The one exception is the optional set of 64-bit record keys used for the
    previous-run diff (disable it with ``collect_keys=False`` when no diff is needed).
    """

    def __init__(self, collect_keys: bool = True) -> None:
        """Create an empty tally.

        Args:
            collect_keys: Whether to collect ``record_key`` values for the previous-run diff.
        """
        self.collect_keys = collect_keys
        self.examined = 0
        self.expected = 0
        self.anomalous = 0
        self.by_rule_node: Counter[tuple[str, str, str]] = Counter()
        """Counts keyed by ``(severity, rule, node)``."""
        self.by_class: Counter[tuple[str, str]] = Counter()
        """Counts keyed by ``(product_class, severity)``."""
        self.by_age: Counter[tuple[str, str]] = Counter()
        """Counts keyed by ``(age_bucket, severity)``."""
        self.collections: dict[str, CollectionImpact] = {}
        """Anomalous-product impact keyed by collection LIDVID."""
        self.orphans: dict[str, OrphanInfo] = {}
        """Not-loaded products keyed by derived collection LID."""
        self.pending_by_node: dict[str, Counter[str]] = {}
        """Expected-pending counts per node, then per rule value."""
        self.keys: set[int] = set()
        """``record_key`` of every (product, rule) seen, when ``collect_keys`` is true."""
        self.unverified_refs_missing = 0
        """Anomalous ``refs_missing`` products reached without the collection inventory."""

    def add(self, candidate: Candidate, verdict: Verdict, now: datetime) -> None:
        """Fold one classified product into the counters.

        Args:
            candidate: The product that was classified.
            verdict: The classification outcome.
            now: Reference time used for the age bucket.
        """
        severity = verdict.severity.value
        rule = verdict.rule.value
        self.examined += 1
        if verdict.severity is Severity.ANOMALOUS:
            self.anomalous += 1
        else:
            self.expected += 1
        self.by_rule_node[(severity, rule, candidate.node)] += 1
        self.by_class[(candidate.product_class, severity)] += 1
        self.by_age[(age_bucket(age_days(candidate.harvest, now)), severity)] += 1

        if verdict.severity is Severity.ANOMALOUS and verdict.collection_lidvid:
            impact = self.collections.get(verdict.collection_lidvid)
            if impact is None:
                impact = CollectionImpact(node=candidate.node)
                self.collections[verdict.collection_lidvid] = impact
            impact.rule_counts[rule] += 1
            if impact.bundle_lid is None:
                impact.bundle_lid = verdict.bundle_lid
            if verdict.collection_state is not None:
                impact.state = verdict.collection_state.value
            if verdict.collection_harvest is not None:
                impact.harvest = verdict.collection_harvest

        if verdict.rule is Rule.REFS_MISSING and verdict.severity is Severity.ANOMALOUS:
            if not verdict.inventory_verified:
                self.unverified_refs_missing += 1

        if verdict.rule in NOT_LOADED_RULES:
            lid = derive_collection_lid(candidate.lid) or "(unknown)"
            orphan = self.orphans.get(lid)
            if orphan is None:
                orphan = OrphanInfo(node=candidate.node)
                self.orphans[lid] = orphan
            if verdict.severity is Severity.ANOMALOUS:
                orphan.overdue += 1
            else:
                orphan.pending += 1

        if verdict.severity is Severity.EXPECTED and verdict.rule in PENDING_RULES:
            self.pending_by_node.setdefault(candidate.node, Counter())[rule] += 1

        if self.collect_keys:
            self.keys.add(record_key(candidate.lidvid, verdict.rule))

    def rule_totals(self, severity: Severity | None = None) -> Counter[str]:
        """Return product counts per rule value, optionally for one severity only."""
        totals: Counter[str] = Counter()
        for (sev, rule, _node), count in self.by_rule_node.items():
            if severity is None or sev == severity.value:
                totals[rule] += count
        return totals

    def anomalous_collection_counts(self) -> dict[str, int]:
        """Return affected anomalous product counts keyed by collection LIDVID."""
        return {lidvid: impact.total for lidvid, impact in self.collections.items()}

    def worst_collections(self, limit: int) -> list[str]:
        """Return the collection LIDVIDs with the most anomalous products.

        Args:
            limit: Maximum number of collections to return.

        Returns:
            LIDVIDs ordered by affected product count (descending), then LIDVID.
        """
        ranked = sorted(self.collections.items(), key=lambda item: (-item[1].total, item[0]))
        return [lidvid for lidvid, _ in ranked[: max(limit, 0)]]


# ── diff ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DiffCounts:
    """Comparison of two runs, keyed on (LIDVID, rule).

    Attributes:
        new: Present now, absent in the previous run.
        resolved: Present in the previous run, absent now.
        persisting: Present in both.
    """

    new: int
    resolved: int
    persisting: int


def load_previous_keys(path: Path) -> set[int]:
    """Read a previous ``unprocessed_products.csv`` (or ``.csv.gz``) into record keys.

    Args:
        path: The previous products CSV.

    Returns:
        ``record_key`` of every (lidvid, rule) row.
    """
    keys: set[int] = set()
    with _open_text(Path(path), "r") as handle:
        for row in csv.DictReader(handle):
            lidvid = row.get("lidvid")
            rule = row.get("rule")
            if lidvid and rule:
                keys.add(record_key(lidvid, rule))
    return keys


def compute_diff(previous: set[int], current: set[int]) -> DiffCounts:
    """Compare two runs' record keys.

    Args:
        previous: Keys from the earlier run.
        current: Keys from this run.

    Returns:
        New, resolved and persisting counts.
    """
    return DiffCounts(
        new=len(current - previous),
        resolved=len(previous - current),
        persisting=len(current & previous),
    )


# ── collections outputs ───────────────────────────────────────────────────────


def write_collections_csv(
    path: Path,
    collections: Iterable[Collection],
    coverage: Mapping[str, RefsCoverage],
    anomalous_counts: Mapping[str, int] | None = None,
) -> int:
    """Write ``collections.csv``: one row per collection.

    Args:
        path: File to write.
        collections: Every collection that was examined.
        coverage: Refs coverage keyed by collection LIDVID (only collections that were queried).
        anomalous_counts: Affected anomalous product counts keyed by collection LIDVID.

    Returns:
        Number of rows written.
    """
    counts = anomalous_counts or {}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLLECTION_COLUMNS)
        for coll in collections:
            cov = coverage.get(coll.lidvid)
            writer.writerow(
                [
                    coll.node,
                    coll.lidvid,
                    coll.state.value if coll.state else "",
                    coll.stamp or "",
                    len(coll.ancestor_refs),
                    _fmt_ts(coll.harvest),
                    ";".join(coll.bundle_lidvids),
                    counts.get(coll.lidvid, 0),
                    cov.refs_count if cov else "",
                    cov.member_count if cov else "",
                    cov.stamped_member_count if cov else "",
                    coverage_note(cov),
                    coll.superseded_by or "",
                ]
            )
            rows += 1
    return rows


def write_anomalous_collections(path: Path, collections_lidvids: Iterable[str]) -> int:
    """Write ``anomalous_collections.txt``: one collection LIDVID per line.

    The file can be passed to ``audit_collection.py --from-file``.

    Args:
        path: File to write.
        collections_lidvids: Collection LIDVIDs that root at least one anomaly.

    Returns:
        Number of LIDVIDs written.
    """
    lidvids = sorted(set(collections_lidvids))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        for lidvid in lidvids:
            handle.write(lidvid + "\n")
    return len(lidvids)


# ── summary rendering ─────────────────────────────────────────────────────────


def _cell(value: object) -> str:
    """Escape a value for use inside a Markdown table cell."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(
    headers: list[str],
    rows: list[list[object]],
    max_rows: int,
    noun: str,
) -> list[str]:
    """Render a Markdown table capped at ``max_rows`` rows.

    Args:
        headers: Column headings.
        rows: Table rows, already sorted by importance.
        max_rows: Maximum number of rows to show.
        noun: Plural noun for the "omitted" note.

    Returns:
        Lines of Markdown, ending with a note when rows were omitted.
    """
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows[:max_rows]:
        lines.append("| " + " | ".join(_cell(c) for c in row) + " |")
    if len(rows) > max_rows:
        lines.append("")
        lines.append(f"_{len(rows) - max_rows:,} more {noun} omitted; the CSV files hold everything._")
    return lines


def _rule_order(rule: str) -> int:
    """Sort key placing rules in the order they are declared in ``Rule``."""
    for index, member in enumerate(Rule):
        if member.value == rule:
            return index
    return len(Rule)


def _bundles_for(
    lidvid: str,
    impact: CollectionImpact,
    known: Mapping[str, Collection],
) -> str:
    """Choose the bundle text for an anomalous collection row.

    Prefers the bundles found by registry lookup, then bundle-looking ``ancestor_refs`` entries, then
    the bundle LID derived from a product LID.
    """
    coll = known.get(lidvid)
    bundles: list[str] = []
    if coll is not None:
        bundles = list(coll.bundle_lidvids)
        if not bundles:
            bundles = [ref for ref in coll.ancestor_refs if _BUNDLE_LID_PATTERN.match(ref)]
    if not bundles and impact.bundle_lid:
        bundles = [impact.bundle_lid]
    if not bundles:
        return "-"
    shown = ", ".join(bundles[:_MAX_BUNDLES_SHOWN])
    if len(bundles) > _MAX_BUNDLES_SHOWN:
        shown += f" (+{len(bundles) - _MAX_BUNDLES_SHOWN} more)"
    return shown


def _section_headline(tally: Tally, th: Thresholds, params: Mapping[str, object]) -> list[str]:
    """Section 1: headline counts."""
    lines = [
        "# Unprocessed product audit",
        "",
        f"Run time: {_fmt_ts(th.now)}",
    ]
    nodes = params.get("Nodes")
    if nodes:
        lines.append(f"Nodes: {nodes}")
    lines.append("")
    if tally.examined == 0:
        lines.append("No candidate products were found: every API-visible product has current ancestry.")
    else:
        lines += [
            f"- Candidates examined: **{tally.examined:,}**",
            f"- Expected (should resolve on their own): **{tally.expected:,}**",
            f"- Anomalous (need attention): **{tally.anomalous:,}**",
        ]
    return lines


def _section_actions(tally: Tally, collections: CollectionABC[Collection]) -> list[str]:
    """Section 2: what needs to happen, grouped by who can fix it, in plain language."""
    per_rule = ownership.collections_per_rule(impact.rule_counts for impact in tally.collections.values())
    not_loaded = sum(1 for orphan in tally.orphans.values() if orphan.overdue)
    if not_loaded:
        per_rule[Rule.COLLECTION_NOT_LOADED_OVERDUE.value] = not_loaded
    rows = ownership.build_rows(
        tally.rule_totals(Severity.ANOMALOUS),
        tally.rule_totals(Severity.EXPECTED),
        per_rule,
        len(ownership.empty_refs_collections(collections)),
        tally.unverified_refs_missing,
    )
    lines = ["## What needs to happen", "", f"**{ownership.verdict(rows)}**"]
    if not rows:
        return lines
    lines += ["", "| Who | What is wrong | Products | Collections | What to do |", "|---|---|--:|--:|---|"]
    for row in rows:
        products = f"{row.products:,}" if row.products is not None else "-"
        count = f"{row.collections:,}" if row.collections is not None else "-"
        what = f"**{ownership.KIND_LABELS[row.kind]}**: {row.problem.title}"
        lines.append(
            f"| {ownership.OWNER_LABELS[row.owner]} | {_cell(what)} | {products} | {count} | "
            f"{_cell(row.problem.action)} |"
        )
    kinds_present = [k for k in ownership.Kind if any(r.kind is k for r in rows)]
    owners_present = [o for o in ownership.Owner if any(r.owner is o for r in rows)]
    lines += ["", "Kinds of problem:", ""]
    lines += [f"- **{ownership.KIND_LABELS[k]}**: {ownership.KIND_MEANING[k]}." for k in kinds_present]
    lines += ["", "Who fixes what:", ""]
    lines += [f"- **{ownership.OWNER_LABELS[o]}**: {ownership.OWNER_MEANING[o]}." for o in owners_present]
    if tally.unverified_refs_missing:
        lines += [
            "",
            f"{tally.unverified_refs_missing:,} products were not checked against the collection inventory "
            "(it was skipped with `--no-inventory` or could not be read).",
        ]
    return lines


def _section_parameters(th: Thresholds, params: Mapping[str, object]) -> list[str]:
    """Run parameters, at the end of the report."""
    lines = [
        "## Run parameters",
        "",
        f"- Ancestry version: {th.ancestry_version}",
        f"- Collection grace period: {th.collection_grace_days:g} days",
        f"- Product grace period: {th.product_grace_days:g} days",
    ]
    for key, value in params.items():
        lines.append(f"- {key}: {value}")
    return lines


def _section_anomalies(tally: Tally, max_rows: int) -> list[str]:
    """Section 2: anomalies grouped by rule, then node."""
    anomalous = Severity.ANOMALOUS.value
    totals = tally.rule_totals(Severity.ANOMALOUS)
    if not totals:
        return []
    rule_rows: list[list[object]] = [
        [rule, f"{count:,}"] for rule, count in sorted(totals.items(), key=lambda kv: _rule_order(kv[0]))
    ]
    node_counts = sorted(
        ((rule, node, count) for (sev, rule, node), count in tally.by_rule_node.items() if sev == anomalous),
        key=lambda t: (_rule_order(t[0]), -t[2], t[1]),
    )
    node_rows: list[list[object]] = [[rule, node, f"{count:,}"] for rule, node, count in node_counts]
    lines = ["## Anomalies by rule", ""]
    lines += _table(["Rule", "Products"], rule_rows, max_rows, "rules")
    lines += ["", "### By rule and node", ""]
    lines += _table(["Rule", "Node", "Products"], node_rows, max_rows, "rows")
    return lines


def _section_anomalous_collections(
    tally: Tally,
    known: Mapping[str, Collection],
    coverage: Mapping[str, RefsCoverage],
    max_rows: int,
) -> list[str]:
    """Section 3: collections that root anomalies."""
    if not tally.collections:
        return []
    ranked = sorted(tally.collections.items(), key=lambda item: (-item[1].total, item[0]))
    rows: list[list[object]] = []
    for lidvid, impact in ranked:
        coll = known.get(lidvid)
        state = coll.state.value if coll is not None and coll.state else (impact.state or "-")
        if coll is not None and coll.superseded_by:
            state += " (superseded)"
        harvest = coll.harvest if coll is not None and coll.harvest else impact.harvest
        rows.append(
            [
                impact.node,
                _bundles_for(lidvid, impact, known),
                lidvid,
                state,
                _fmt_ts(harvest) or "-",
                f"{impact.total:,}",
                coverage_note(coverage.get(lidvid)) or "not queried",
            ]
        )
    lines = [
        "## Anomalous collections",
        "",
        f"{len(ranked):,} collections root at least one anomalous product, worst first. "
        "Each can be re-audited with `audit_collection.py --from-file anomalous_collections.txt`.",
        "",
    ]
    superseded_count = sum(1 for lidvid, _ in ranked if known.get(lidvid) and known[lidvid].superseded_by)
    if superseded_count:
        lines += [
            f"{superseded_count:,} of them are superseded collection versions. Their products are still "
            "API-visible, but a superseded version is not re-harvested, so it is left out of "
            "`anomalous_collections.txt`.",
            "",
        ]
    lines += _table(
        ["Node", "Bundle(s)", "Collection", "State", "Harvested", "Affected products", "Refs coverage"],
        rows,
        max_rows,
        "collections",
    )
    return lines


def _section_empty_refs(collections: Iterable[Collection], max_rows: int) -> list[str]:
    """Section 4: stamped collections whose ``ancestor_refs`` are empty."""
    empties = [c for c in collections if c.state is CollectionState.STAMPED_EMPTY_REFS and not c.superseded_by]
    if not empties:
        return []
    with_bundle = sorted((c for c in empties if c.bundle_lidvids), key=lambda c: (c.node, c.lidvid))
    lines = [
        "## Stamped collections with empty refs",
        "",
        f"{len(empties):,} collections are stamped with the current version but have no ancestor refs. "
        f"{len(with_bundle):,} of them have a bundle, so that bundle's `/members` is empty (anomaly). "
        f"The other {len(empties) - len(with_bundle):,} have no bundle and are expected.",
    ]
    if with_bundle:
        rows: list[list[object]] = [
            [c.node, ", ".join(c.bundle_lidvids[:_MAX_BUNDLES_SHOWN]), c.lidvid, _fmt_ts(c.harvest) or "-"]
            for c in with_bundle
        ]
        lines += [""]
        lines += _table(["Node", "Bundle(s)", "Collection", "Harvested"], rows, max_rows, "collections")
    return lines


def _section_pending(tally: Tally, max_rows: int) -> list[str]:
    """Section 5: expected-pending counts by node."""
    if not tally.pending_by_node:
        return []
    rules = [r.value for r in PENDING_RULES]
    rows: list[list[object]] = []
    for node, counts in sorted(tally.pending_by_node.items(), key=lambda kv: (-sum(kv[1].values()), kv[0])):
        rows.append([node, *(f"{counts.get(r, 0):,}" for r in rules), f"{sum(counts.values()):,}"])
    total = sum(sum(c.values()) for c in tally.pending_by_node.values())
    lines = [
        "## Expected pending, by node",
        "",
        f"{total:,} products are waiting on the sweeper or a loading collection. "
        "This is the number that should shrink on its own.",
        "",
    ]
    lines += _table(["Node", *rules, "Total"], rows, max_rows, "nodes")
    return lines


def _section_orphans(tally: Tally, max_rows: int) -> list[str]:
    """Section 6: products whose parent collection is not loaded."""
    if not tally.orphans:
        return []
    ranked = sorted(tally.orphans.items(), key=lambda kv: (-kv[1].total, kv[0]))
    products = sum(o.total for o in tally.orphans.values())
    rows: list[list[object]] = [
        [lid, o.node, f"{o.overdue:,}", f"{o.pending:,}", f"{o.total:,}"] for lid, o in ranked
    ]
    lines = [
        "## Orphans",
        "",
        f"{products:,} products belong to {len(ranked):,} collection LIDs that have no API-visible "
        "collection. These are not sweeper bugs: the collection has to be loaded first.",
        "",
    ]
    lines += _table(["Collection LID", "Node", "Overdue", "Pending", "Products"], rows, max_rows, "collection LIDs")
    return lines


def _section_breakdown(tally: Tally, max_rows: int) -> list[str]:
    """Section 7: breakdown by product class and age bucket."""
    if tally.examined == 0:
        return []
    expected = Severity.EXPECTED.value
    anomalous = Severity.ANOMALOUS.value
    classes = sorted({cls for cls, _ in tally.by_class})
    class_rows: list[list[object]] = []
    for cls in sorted(classes, key=lambda c: (-(tally.by_class[(c, expected)] + tally.by_class[(c, anomalous)]), c)):
        exp, ano = tally.by_class[(cls, expected)], tally.by_class[(cls, anomalous)]
        class_rows.append([cls, f"{exp:,}", f"{ano:,}", f"{exp + ano:,}"])
    age_rows: list[list[object]] = []
    for bucket in AGE_BUCKETS:
        exp, ano = tally.by_age[(bucket, expected)], tally.by_age[(bucket, anomalous)]
        if exp or ano:
            age_rows.append([bucket, f"{exp:,}", f"{ano:,}", f"{exp + ano:,}"])
    lines = ["## Breakdown", "", "### By product class", ""]
    lines += _table(["Product class", "Expected", "Anomalous", "Total"], class_rows, max_rows, "product classes")
    lines += ["", "### By harvest age", ""]
    lines += _table(["Age", "Expected", "Anomalous", "Total"], age_rows, max_rows, "age buckets")
    return lines


def _section_diff(diff: DiffCounts | None) -> list[str]:
    """Section 8: comparison with the previous run."""
    if diff is None:
        return []
    return [
        "## Change since previous run",
        "",
        f"- New: {diff.new:,}",
        f"- Resolved: {diff.resolved:,}",
        f"- Persisting: {diff.persisting:,}",
    ]


def _section_guidance(tally: Tally) -> list[str]:
    """Section 9: what each observed rule means and what to do."""
    totals = tally.rule_totals()
    if not totals:
        return []
    lines = ["## What each rule means", ""]
    for rule, count in sorted(totals.items(), key=lambda kv: _rule_order(kv[0])):
        text = RULE_GUIDANCE.get(Rule(rule), "") if rule in {r.value for r in Rule} else ""
        lines.append(f"- **{rule}** ({count:,} products): {text}".rstrip())
    return lines


def render_summary(
    tally: Tally,
    collections: Iterable[Collection],
    coverage: Mapping[str, RefsCoverage],
    th: Thresholds,
    params: Mapping[str, object],
    diff: DiffCounts | None,
    max_rows: int = _DEFAULT_MAX_ROWS,
) -> str:
    """Render ``summary.md``.

    Sections follow the design document, in order, and are skipped when they have nothing to say
    (the headline is always present).

    Args:
        tally: Accumulated counters.
        collections: Every collection that was examined (with ``state`` and ``bundle_lidvids`` set).
        coverage: Refs coverage keyed by collection LIDVID, for the collections that were queried.
        th: Run thresholds.
        params: Extra run parameters to list in the headline, such as the node filter.
        diff: Comparison against the previous run, or ``None``.
        max_rows: Maximum rows shown in any one table.

    Returns:
        The Markdown report.
    """
    collection_list: CollectionABC[Collection] = list(collections)
    known = {c.lidvid: c for c in collection_list}
    sections = [
        _section_headline(tally, th, params),
        _section_actions(tally, collection_list),
        _section_anomalies(tally, max_rows),
        _section_anomalous_collections(tally, known, coverage, max_rows),
        _section_empty_refs(collection_list, max_rows),
        _section_pending(tally, max_rows),
        _section_orphans(tally, max_rows),
        _section_breakdown(tally, max_rows),
        _section_diff(diff),
        _section_guidance(tally),
        _section_parameters(th, params),
    ]
    return "\n\n".join("\n".join(section) for section in sections if section) + "\n"
