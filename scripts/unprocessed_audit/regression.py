"""Regression checks for the unprocessed product audit: metrics, invariants and a baseline comparison.

A run writes ``metrics.json``. With ``--check`` the metrics are evaluated against invariants that a
healthy registry satisfies, and the process exits non-zero when one is violated. With ``--baseline`` (the
``metrics.json`` of an earlier run) the check fails only for anomalies that are new since that run, so a
known backlog does not fail every run while a new problem does.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path

from unprocessed_audit.model import SUPERSEDED_FIELD
from unprocessed_audit.model import Collection
from unprocessed_audit.model import CollectionState
from unprocessed_audit.model import RegistryQueryError
from unprocessed_audit.model import Rule
from unprocessed_audit.model import Severity
from unprocessed_audit.registry import RegistryClient
from unprocessed_audit.registry import registry_index
from unprocessed_audit.report import Tally

METRICS_JSON = "metrics.json"
METRICS_SCHEMA_VERSION = 1

NO_ANOMALOUS_PRODUCTS = "no_anomalous_products"
NO_NEW_ANOMALIES = "no_new_anomalies"
NO_EMPTY_REFS_WITH_BUNDLE = "no_empty_refs_collection_with_bundle"
SUPERSEDED_BY_MAPPED = "superseded_by_mapped"

HISTORY_PREFIX_COLUMNS = ["run_time", "ancestry_version", "nodes", "examined", "expected", "anomalous"]
HISTORY_SUFFIX_COLUMNS = ["anomalous_collections", "empty_refs_with_bundle"]
HISTORY_COLUMNS = HISTORY_PREFIX_COLUMNS + [rule.value for rule in Rule] + HISTORY_SUFFIX_COLUMNS

_DETAIL_LIMIT = 20


class BaselineError(ValueError):
    """The baseline metrics cannot be read or cannot be compared with this run."""


class HistoryFormatError(ValueError):
    """The history CSV exists but does not have the columns this version writes."""


@dataclass
class Metrics:
    """Machine-readable result of one audit run.

    Attributes:
        run_time: ISO 8601 time of the run.
        ancestry_version: Ancestry version stamp the run audited against.
        nodes: Nodes audited, sorted.
        examined: Candidate products examined.
        expected: Candidates expected to resolve on their own.
        anomalous: Candidates that need attention.
        rules: Anomalous product count per rule value; every rule is present, zero when unused.
        anomalous_collections: LIDVIDs of current (not superseded) collections rooting anomalous products.
        superseded_anomalous_collections: LIDVIDs of superseded collection versions rooting anomalous products.
        empty_refs_with_bundle: LIDVIDs of collections stamped with empty refs that have a bundle.
        unmapped_superseded: Indices whose mapping lacks the superseded field; ``None`` when not checked.
    """

    run_time: str
    ancestry_version: int
    nodes: list[str]
    examined: int
    expected: int
    anomalous: int
    rules: dict[str, int]
    anomalous_collections: list[str]
    superseded_anomalous_collections: list[str]
    empty_refs_with_bundle: list[str]
    unmapped_superseded: list[str] | None = None

    def to_json(self) -> str:
        """Serialise to the ``metrics.json`` text."""
        payload = {"schema_version": METRICS_SCHEMA_VERSION, **self.__dict__}
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"


@dataclass
class Violation:
    """A failed invariant.

    Attributes:
        invariant: Short name of the invariant.
        message: One-line statement of what is wrong.
        details: Items to look at (collection LIDVIDs, index names); long lists are truncated when rendered.
    """

    invariant: str
    message: str
    details: list[str] = field(default_factory=list)


def build_metrics(
    tally: Tally,
    collections: Iterable[Collection],
    nodes: Sequence[str],
    ancestry_version: int,
    now: datetime,
) -> Metrics:
    """Condense a finished audit into ``Metrics``.

    Args:
        tally: The run's counters.
        collections: Every collection examined, classified and with bundles attached.
        nodes: Nodes audited.
        ancestry_version: Ancestry version stamp audited against.
        now: Run time.

    Returns:
        The metrics, without the mapping check (``unmapped_superseded`` is ``None``).
    """
    collections = list(collections)
    superseded = {c.lidvid for c in collections if c.superseded_by}
    anomalous_totals = tally.rule_totals(Severity.ANOMALOUS)
    return Metrics(
        run_time=now.isoformat(timespec="seconds"),
        ancestry_version=ancestry_version,
        nodes=sorted(nodes),
        examined=tally.examined,
        expected=tally.expected,
        anomalous=tally.anomalous,
        rules={rule.value: anomalous_totals.get(rule.value, 0) for rule in Rule},
        anomalous_collections=sorted(lidvid for lidvid in tally.collections if lidvid not in superseded),
        superseded_anomalous_collections=sorted(lidvid for lidvid in tally.collections if lidvid in superseded),
        empty_refs_with_bundle=sorted(
            c.lidvid
            for c in collections
            if c.state is CollectionState.STAMPED_EMPTY_REFS and c.bundle_lidvids and not c.superseded_by
        ),
    )


def load_metrics(path: Path) -> Metrics:
    """Read a ``metrics.json`` written by an earlier run.

    Args:
        path: The file.

    Returns:
        The parsed metrics.

    Raises:
        BaselineError: If the file is missing, is not valid JSON, or lacks the expected fields.
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BaselineError(f"Could not read the baseline metrics {path}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != METRICS_SCHEMA_VERSION:
        raise BaselineError(f"{path} is not a schema version {METRICS_SCHEMA_VERSION} metrics file")
    try:
        return Metrics(
            run_time=str(raw["run_time"]),
            ancestry_version=int(raw["ancestry_version"]),
            nodes=[str(n) for n in raw["nodes"]],
            examined=int(raw["examined"]),
            expected=int(raw["expected"]),
            anomalous=int(raw["anomalous"]),
            rules={str(k): int(v) for k, v in raw["rules"].items()},
            anomalous_collections=[str(c) for c in raw["anomalous_collections"]],
            superseded_anomalous_collections=[str(c) for c in raw["superseded_anomalous_collections"]],
            empty_refs_with_bundle=[str(c) for c in raw["empty_refs_with_bundle"]],
            unmapped_superseded=None
            if raw.get("unmapped_superseded") is None
            else [str(i) for i in raw["unmapped_superseded"]],
        )
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise BaselineError(f"{path} is missing or has malformed metrics fields: {exc!r}") from exc


# ── mapping canary ────────────────────────────────────────────────────────────


def mapping_has_field(mapping: object, field_name: str) -> bool:
    """Say whether an index ``_mapping`` response defines ``field_name`` anywhere.

    Args:
        mapping: Parsed ``_mapping`` response (or any nested part of one).
        field_name: Field name; the registry uses the slash form, e.g. ``ops:Provenance/ops:superseded_by``.

    Returns:
        ``True`` when the name is a key of a mapping definition.
    """
    if isinstance(mapping, dict):
        for key, value in mapping.items():
            if key == field_name and isinstance(value, dict):
                return True
            if mapping_has_field(value, field_name):
                return True
    return False


def find_unmapped_superseded(client: RegistryClient, nodes: Sequence[str]) -> list[str]:
    """Return the registry indices whose mapping lacks ``ops:Provenance/ops:superseded_by``.

    A field absent from the mapping is returned in ``_source`` but cannot be searched, so the registry API
    cannot exclude superseded products with it.

    Args:
        client: Registry client.
        nodes: Nodes to check.

    Returns:
        Index names without the mapping, in node order.

    Raises:
        RegistryQueryError: If a mapping cannot be read.
    """
    missing: list[str] = []
    for node in nodes:
        index = registry_index([node])
        mapping = client.get_mapping(index)
        if not mapping:
            raise RegistryQueryError(f"The mapping of {index} came back empty")
        if not mapping_has_field(mapping, SUPERSEDED_FIELD):
            missing.append(index)
    return missing


# ── invariants ────────────────────────────────────────────────────────────────


def _new_items(current: Iterable[str], previous: Iterable[str]) -> list[str]:
    return sorted(set(current) - set(previous))


def check_comparable(nodes: Sequence[str], ancestry_version: int, baseline: Metrics) -> None:
    """Raise ``BaselineError`` when the baseline cannot be compared with this run.

    Args:
        nodes: Nodes this run audits.
        ancestry_version: Ancestry version stamp this run audits against.
        baseline: The earlier run's metrics.

    Raises:
        BaselineError: If the runs audited different nodes or a different ancestry version.
    """
    if baseline.nodes != sorted(nodes):
        raise BaselineError(f"The baseline audited nodes {baseline.nodes}, this run {sorted(nodes)}")
    if baseline.ancestry_version != ancestry_version:
        raise BaselineError(
            f"The baseline used ancestry version {baseline.ancestry_version}, this run {ancestry_version}"
        )


def evaluate(metrics: Metrics, baseline: Metrics | None = None) -> list[Violation]:
    """Evaluate the invariants.

    Without a baseline every anomaly is a violation. With one, only what is new since the baseline is:
    collections that now root anomalous products or are stamped with empty refs although they have a bundle,
    and any rule whose anomalous product count grew (which also covers products with no collection, such as
    orphans). The mapping invariant never uses the baseline: an unmapped field is always a violation.

    Args:
        metrics: This run's metrics, with ``unmapped_superseded`` filled in when it was checked.
        baseline: An earlier run's metrics, already confirmed comparable.

    Returns:
        The violations, empty when every invariant holds.
    """
    violations: list[Violation] = []

    if baseline is None:
        if metrics.anomalous:
            worst = {r: n for r, n in metrics.rules.items() if n}
            violations.append(
                Violation(
                    NO_ANOMALOUS_PRODUCTS,
                    f"{metrics.anomalous:,} products are anomalous",
                    [f"{rule}: {count:,}" for rule, count in sorted(worst.items(), key=lambda i: -i[1])],
                )
            )
        if metrics.empty_refs_with_bundle:
            violations.append(
                Violation(
                    NO_EMPTY_REFS_WITH_BUNDLE,
                    f"{len(metrics.empty_refs_with_bundle)} collections with a bundle are stamped with empty refs",
                    list(metrics.empty_refs_with_bundle),
                )
            )
    else:
        new_collections = _new_items(
            metrics.anomalous_collections + metrics.superseded_anomalous_collections,
            baseline.anomalous_collections + baseline.superseded_anomalous_collections,
        )
        grown = [
            f"{rule}: {baseline.rules.get(rule, 0):,} -> {count:,}"
            for rule, count in sorted(metrics.rules.items())
            if count > baseline.rules.get(rule, 0)
        ]
        if new_collections or grown:
            violations.append(
                Violation(
                    NO_NEW_ANOMALIES,
                    f"{len(new_collections)} collections newly root anomalous products; "
                    f"{len(grown)} rules have more anomalous products than the baseline of {baseline.run_time}",
                    new_collections + grown,
                )
            )
        new_empty = _new_items(metrics.empty_refs_with_bundle, baseline.empty_refs_with_bundle)
        if new_empty:
            violations.append(
                Violation(
                    NO_EMPTY_REFS_WITH_BUNDLE,
                    f"{len(new_empty)} collections with a bundle are newly stamped with empty refs",
                    new_empty,
                )
            )

    if metrics.unmapped_superseded:
        violations.append(
            Violation(
                SUPERSEDED_BY_MAPPED,
                f"{len(metrics.unmapped_superseded)} registry indices do not map {SUPERSEDED_FIELD}, so the API "
                "cannot exclude superseded products there",
                list(metrics.unmapped_superseded),
            )
        )
    return violations


def render_check_section(violations: Sequence[Violation], baseline: Metrics | None, mapping_checked: bool) -> str:
    """Render the regression check result as a Markdown section for ``summary.md``.

    Args:
        violations: Result of ``evaluate``.
        baseline: The baseline used, if any.
        mapping_checked: Whether the mapping invariant was evaluated.

    Returns:
        Markdown text ending in a newline.
    """
    compared = f"against the baseline of {baseline.run_time}" if baseline else "with no baseline (any anomaly fails)"
    lines = ["## Regression check", "", f"Evaluated {compared}."]
    if not mapping_checked:
        lines.append(f"The `{SUPERSEDED_BY_MAPPED}` invariant was not evaluated.")
    lines.append("")
    if not violations:
        lines.append("**PASS** - every invariant holds.")
        return "\n".join(lines) + "\n"
    lines.append(f"**FAIL** - {len(violations)} invariant(s) violated.")
    lines.append("")
    for violation in violations:
        lines.append(f"- `{violation.invariant}`: {violation.message}")
        for item in violation.details[:_DETAIL_LIMIT]:
            lines.append(f"  - {item}")
        hidden = len(violation.details) - _DETAIL_LIMIT
        if hidden > 0:
            lines.append(f"  - ... and {hidden} more")
    return "\n".join(lines) + "\n"


# ── history ───────────────────────────────────────────────────────────────────


def check_history_format(path: Path) -> bool:
    """Confirm an existing history CSV has the columns ``append_history`` writes.

    Args:
        path: The history CSV; it need not exist.

    Returns:
        ``True`` when the file exists and is not empty, ``False`` when a new file will be started.

    Raises:
        HistoryFormatError: If the file exists with a different header.
    """
    path = Path(path)
    if not (path.is_file() and path.stat().st_size > 0):
        return False
    with path.open("r", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle), [])
    if header != HISTORY_COLUMNS:
        raise HistoryFormatError(f"{path} has columns {header}, expected {HISTORY_COLUMNS}")
    return True


def append_history(path: Path, metrics: Metrics) -> None:
    """Append one row for this run to the history CSV, writing the header when the file is new.

    Args:
        path: The history CSV.
        metrics: This run's metrics.

    Raises:
        HistoryFormatError: If the file exists with a different header.
    """
    path = Path(path)
    exists = check_history_format(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if not exists:
            writer.writerow(HISTORY_COLUMNS)
        writer.writerow(
            [
                metrics.run_time,
                metrics.ancestry_version,
                " ".join(metrics.nodes),
                metrics.examined,
                metrics.expected,
                metrics.anomalous,
                *[metrics.rules.get(rule.value, 0) for rule in Rule],
                len(metrics.anomalous_collections) + len(metrics.superseded_anomalous_collections),
                len(metrics.empty_refs_with_bundle),
            ]
        )
