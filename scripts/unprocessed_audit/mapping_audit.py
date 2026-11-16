"""Compare OpenSearch index mappings across the registry node indices.

Every node has its own ``<node>-registry`` index (and ``<node>-registry-refs``), created at different times, so
their mappings drift. A field missing from one mapping is returned in ``_source`` but cannot be searched; a field
mapped as different types on different nodes behaves differently under the same query. This module flattens each
mapping into ``field -> type`` and reports the differences.
"""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path

from unprocessed_audit.model import REFS_SUFFIX
from unprocessed_audit.model import REGISTRY_SUFFIX
from unprocessed_audit.model import RegistryQueryError
from unprocessed_audit.registry import RegistryClient

GROUP_REGISTRY = "registry"
GROUP_REFS = "registry-refs"
GROUP_SUFFIXES = {GROUP_REGISTRY: REGISTRY_SUFFIX, GROUP_REFS: REFS_SUFFIX}

DEFAULT_PRESENCE_THRESHOLD = 0.8
"""A field defined on at least this fraction of a group's indices is expected on all of them."""

CORE_FIELDS = frozenset(
    {"_package_id", "alternate_ids", "description", "lid", "lidvid", "product_class", "title", "vid"}
)
"""Top-level fields the registry writes for every product. A missing mapping for one is an error. Other
top-level fields (``ref_lid_*``) exist only where products have such references, so they are warnings."""

NO_TYPE = "(absent)"
OBJECT_TYPE = "object"
_DETAIL_LIMIT = 25


class Kind(str, Enum):
    """Category of a mapping discrepancy."""

    MISSING_FIELD = "missing_field"
    """Defined on most indices of the group, absent on this one."""
    TYPE_MISMATCH = "type_mismatch"
    """Defined on this index with a different type than on most indices."""
    DYNAMIC_MISMATCH = "dynamic_mismatch"
    """The index's ``dynamic`` setting differs from most indices."""
    INDEX_MISSING = "index_missing"
    """The index does not exist."""


class Severity(str, Enum):
    """How much a discrepancy matters."""

    ERROR = "error"
    """A field every index should have (``ops:`` and top-level fields) or a type conflict."""
    WARNING = "warning"
    """A data-dictionary field that most, but not all, indices define."""


@dataclass
class IndexMapping:
    """One index's flattened mapping.

    Attributes:
        name: Index name as requested (``atm-registry``).
        node: Node the index belongs to.
        group: ``registry`` or ``registry-refs``.
        fields: Flattened ``field path -> type``; ``object`` for fields that only hold properties.
        dynamic: The mapping's ``dynamic`` setting as a string, ``"true"`` when unset (the OpenSearch default).
        present: ``False`` when the index does not exist.
    """

    name: str
    node: str
    group: str
    fields: dict[str, str] = field(default_factory=dict)
    dynamic: str = "true"
    present: bool = True


@dataclass(frozen=True)
class Discrepancy:
    """One difference between an index and its group.

    Attributes:
        index: Index name.
        node: Node name.
        group: Index group.
        field: Field path, or ``""`` for index-level discrepancies.
        kind: Category.
        severity: How much it matters.
        expected: What most indices of the group have.
        actual: What this index has.
        present_in: Indices of the group that define the field with the expected type.
        total: Indices in the group that exist.
    """

    index: str
    node: str
    group: str
    field: str
    kind: Kind
    severity: Severity
    expected: str
    actual: str
    present_in: int
    total: int


@dataclass(frozen=True)
class StaleIndex:
    """An index that is not named after a tenant node, so it may be stale or hold test data.

    Attributes:
        index: Index name.
        node: Index prefix that is not a tenant node.
        documents: Number of documents in the index.
        mapped_fields: Number of fields in its mapping.
        has_refs_index: Whether ``<node>-registry-refs`` exists.
    """

    index: str
    node: str
    documents: int
    mapped_fields: int
    has_refs_index: bool


def describe_possibly_stale(client: RegistryClient, nodes: Sequence[str]) -> list[StaleIndex]:
    """Gather the evidence for reviewing indices that are not named after a tenant node.

    Args:
        client: Registry client.
        nodes: Index prefixes that are not tenant nodes.

    Returns:
        One ``StaleIndex`` per prefix.

    Raises:
        RegistryQueryError: If an index cannot be read.
    """
    found: list[StaleIndex] = []
    for node in nodes:
        name = f"{node}{REGISTRY_SUFFIX}"
        mapping = flatten_mapping(client.get_mapping(name), name, node, GROUP_REGISTRY)
        documents = client.count(name, {"query": {"match_all": {}}})
        refs = read_mappings(client, [node], [GROUP_REFS])[0]
        found.append(StaleIndex(name, node, documents, len(mapping.fields), refs.present))
    return found


def write_stale_csv(path: Path, stale: Iterable[StaleIndex]) -> int:
    """Write the possibly stale indices to a CSV.

    Args:
        path: Output file.
        stale: Rows to write.

    Returns:
        The number of rows written.
    """
    count = 0
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["index", "node", "documents", "mapped_fields", "has_refs_index"])
        for s in stale:
            writer.writerow([s.index, s.node, s.documents, s.mapped_fields, str(s.has_refs_index).lower()])
            count += 1
    return count


def _walk(properties: object, prefix: str, out: dict[str, str]) -> None:
    if not isinstance(properties, dict):
        return
    for name, definition in properties.items():
        if not isinstance(definition, dict):
            continue
        path = f"{prefix}{name}"
        out[path] = str(definition.get("type", OBJECT_TYPE))
        _walk(definition.get("properties"), f"{path}.", out)
        sub_fields = definition.get("fields")
        if isinstance(sub_fields, dict):
            for sub_name, sub_definition in sub_fields.items():
                if isinstance(sub_definition, dict):
                    out[f"{path}.{sub_name}"] = str(sub_definition.get("type", OBJECT_TYPE))


def flatten_mapping(response: dict, name: str, node: str, group: str) -> IndexMapping:
    """Flatten a ``GET /<index>/_mapping`` response.

    The registry's field names contain ``/`` and ``:`` and are single keys, so they stay intact. An alias that
    resolves to several concrete indices is merged; the first definition of a field wins.

    Args:
        response: Parsed response, keyed by concrete index name.
        name: Index name that was requested.
        node: Node name.
        group: Index group.

    Returns:
        The flattened mapping.
    """
    mapping = IndexMapping(name=name, node=node, group=group)
    dynamics: list[str] = []
    for body in response.values():
        if not isinstance(body, dict):
            continue
        mappings = body.get("mappings", {})
        if not isinstance(mappings, dict):
            continue
        dynamics.append(str(mappings.get("dynamic", "true")).lower())
        flat: dict[str, str] = {}
        _walk(mappings.get("properties"), "", flat)
        for path, type_ in flat.items():
            mapping.fields.setdefault(path, type_)
    if dynamics:
        mapping.dynamic = dynamics[0]
    return mapping


def read_mappings(client: RegistryClient, nodes: Sequence[str], groups: Sequence[str]) -> list[IndexMapping]:
    """Read and flatten the mapping of every ``<node><suffix>`` index.

    Args:
        client: Registry client.
        nodes: Node names.
        groups: Index groups to read.

    Returns:
        One ``IndexMapping`` per node and group. An index that does not exist is returned with
        ``present=False`` for the refs group.

    Raises:
        RegistryQueryError: If a registry index cannot be read, or a registry-refs index fails with anything
            other than "not found".
    """
    mappings: list[IndexMapping] = []
    for group in groups:
        for node in nodes:
            name = f"{node}{GROUP_SUFFIXES[group]}"
            try:
                response = client.get_mapping(name)
            except RegistryQueryError as exc:
                # The client reports the status in the message; only a missing refs index is tolerated.
                if group == GROUP_REFS and "HTTP 404" in str(exc):
                    mappings.append(IndexMapping(name=name, node=node, group=group, present=False))
                    continue
                raise
            if not response:
                raise RegistryQueryError(f"The mapping of {name} came back empty")
            mappings.append(flatten_mapping(response, name, node, group))
    return mappings


def _severity(field_path: str, kind: Kind) -> Severity:
    if kind is Kind.TYPE_MISMATCH:
        return Severity.ERROR
    return Severity.ERROR if field_path.startswith("ops:") or field_path in CORE_FIELDS else Severity.WARNING


def _most_common(values: Iterable[str]) -> tuple[str, int]:
    counts = Counter(values)
    best = max(counts.values())
    # Ties go to the alphabetically first value so the result is deterministic.
    return sorted(value for value, count in counts.items() if count == best)[0], best


def analyze(mappings: Sequence[IndexMapping], presence_threshold: float = DEFAULT_PRESENCE_THRESHOLD) -> list[Discrepancy]:
    """Find the differences within each index group.

    A field's expected type is the most common type among the indices that define it. A field is expected on
    every index when at least ``presence_threshold`` of the group's indices define it; the others are then
    reported as missing it. Fields below the threshold are node-specific data-dictionary fields and are not
    reported as missing.

    Args:
        mappings: Flattened mappings of every index.
        presence_threshold: Fraction of a group's indices that must define a field for it to be expected.

    Returns:
        The discrepancies, ordered by group, index and field.
    """
    discrepancies: list[Discrepancy] = []
    for group in sorted({m.group for m in mappings}):
        members = [m for m in mappings if m.group == group]
        existing = [m for m in members if m.present]
        discrepancies.extend(
            Discrepancy(m.name, m.node, group, "", Kind.INDEX_MISSING, Severity.ERROR, "exists", "missing", 0, len(existing))
            for m in members
            if not m.present
        )
        total = len(existing)
        if total < 2:
            continue

        dynamic_expected, _ = _most_common(m.dynamic for m in existing)
        for m in existing:
            if m.dynamic != dynamic_expected:
                discrepancies.append(
                    Discrepancy(
                        m.name, m.node, group, "", Kind.DYNAMIC_MISMATCH, Severity.WARNING,
                        dynamic_expected, m.dynamic, 0, total,
                    )  # fmt: skip
                )

        all_fields = sorted({path for m in existing for path in m.fields})
        for path in all_fields:
            defined = [m for m in existing if path in m.fields]
            expected, expected_count = _most_common(m.fields[path] for m in defined)
            expected_everywhere = len(defined) / total >= presence_threshold
            for m in existing:
                actual = m.fields.get(path)
                if actual is None:
                    if expected_everywhere:
                        discrepancies.append(
                            Discrepancy(m.name, m.node, group, path, Kind.MISSING_FIELD, _severity(path, Kind.MISSING_FIELD),
                                        expected, NO_TYPE, expected_count, total)
                        )  # fmt: skip
                elif actual != expected:
                    discrepancies.append(
                        Discrepancy(
                            m.name, m.node, group, path, Kind.TYPE_MISMATCH, Severity.ERROR,
                            expected, actual, expected_count, total,
                        )  # fmt: skip
                    )
    return sorted(discrepancies, key=lambda d: (d.group, d.index, d.field, d.kind.value))


def write_discrepancies_csv(path: Path, discrepancies: Iterable[Discrepancy]) -> int:
    """Write the discrepancies to a CSV.

    Args:
        path: Output file.
        discrepancies: Rows to write.

    Returns:
        The number of rows written.
    """
    columns = ["group", "index", "node", "field", "kind", "severity", "expected", "actual", "present_in", "total"]
    count = 0
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for d in discrepancies:
            writer.writerow(
                [
                    d.group,
                    d.index,
                    d.node,
                    d.field,
                    d.kind.value,
                    d.severity.value,
                    d.expected,
                    d.actual,
                    d.present_in,
                    d.total,
                ]
            )
            count += 1
    return count


def write_matrix_csv(path: Path, mappings: Sequence[IndexMapping]) -> int:
    """Write a field-by-index matrix of mapped types.

    One row per field and group, one column per index, ``(absent)`` where an index does not map the field.

    Args:
        path: Output file.
        mappings: Flattened mappings.

    Returns:
        The number of field rows written.
    """
    rows = 0
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["group", "field", *[m.name for m in mappings if m.present]])
        for group in sorted({m.group for m in mappings}):
            members = [m for m in mappings if m.present]
            fields = sorted({p for m in members if m.group == group for p in m.fields})
            for path_ in fields:
                cells = [m.fields.get(path_, NO_TYPE) if m.group == group else "" for m in members]
                writer.writerow([group, path_, *cells])
                rows += 1
    return rows


def render_summary(
    mappings: Sequence[IndexMapping],
    discrepancies: Sequence[Discrepancy],
    presence_threshold: float,
    stale: Sequence[StaleIndex] = (),
) -> str:
    """Render the Markdown report.

    Args:
        mappings: Flattened mappings.
        discrepancies: Result of ``analyze``.
        presence_threshold: Threshold the analysis used.
        stale: Indices left out of the comparison because they are not named after a tenant node.

    Returns:
        Markdown text ending in a newline.
    """
    errors = [d for d in discrepancies if d.severity is Severity.ERROR]
    lines = ["# Index mapping audit", ""]
    lines.append(f"- Indices read: **{sum(1 for m in mappings if m.present)}**")
    lines.append(f"- Discrepancies: **{len(discrepancies)}** ({len(errors)} errors, {len(discrepancies) - len(errors)} warnings)")
    lines.append(f"- A field defined on at least {presence_threshold:.0%} of a group's indices is expected on all of them")
    if stale:
        lines.append(f"- Possibly stale or test indices (not compared): **{len(stale)}**")
    lines.append("")

    if stale:
        lines += [
            "## Possibly stale or test indices",
            "",
            "These indices are not named after a tenant node (`<node>-registry`), so they were left out of the",
            "comparison. They may be stale copies or test data and are candidates for cleanup. Confirm with their",
            "owner before deleting; the audit never changes or deletes anything.",
            "",
            "| Index | Documents | Mapped fields | Refs index |",
            "|---|---|---|---|",
        ]
        for s in stale:
            lines.append(f"| {s.index} | {s.documents:,} | {s.mapped_fields} | {'yes' if s.has_refs_index else 'no'} |")
        lines.append("")

    lines += [
        "## Per index",
        "",
        "| Group | Index | Fields | dynamic | Missing (error) | Missing (warning) | Type mismatches |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in mappings:
        mine = [d for d in discrepancies if d.index == m.name]
        miss_e = sum(1 for d in mine if d.kind is Kind.MISSING_FIELD and d.severity is Severity.ERROR)
        miss_w = sum(1 for d in mine if d.kind is Kind.MISSING_FIELD and d.severity is Severity.WARNING)
        mism = sum(1 for d in mine if d.kind is Kind.TYPE_MISMATCH)
        state = f"{len(m.fields)}" if m.present else "(index missing)"
        lines.append(f"| {m.group} | {m.name} | {state} | {m.dynamic} | {miss_e} | {miss_w} | {mism} |")
    lines.append("")

    for kind, title in (
        (Kind.MISSING_FIELD, "Fields missing from some indices"),
        (Kind.TYPE_MISMATCH, "Fields mapped with different types"),
        (Kind.DYNAMIC_MISMATCH, "Different `dynamic` setting"),
        (Kind.INDEX_MISSING, "Missing indices"),
    ):
        rows = [d for d in discrepancies if d.kind is kind]
        if not rows:
            continue
        lines += [f"## {title}", ""]
        if kind is Kind.MISSING_FIELD:
            by_field: dict[tuple[str, str, str, str], list[str]] = {}
            for d in rows:
                by_field.setdefault((d.group, d.field, d.severity.value, d.expected), []).append(d.index)
            lines += ["| Severity | Group | Field | Expected type | Missing from |", "|---|---|---|---|---|"]
            ordered = sorted(by_field.items(), key=lambda item: (item[0][2] != "error", item[0][0], item[0][1]))
            for (group, field_path, severity, expected), indices in ordered[:_DETAIL_LIMIT * 4]:
                lines.append(f"| {severity} | {group} | `{field_path}` | {expected} | {', '.join(sorted(indices))} |")
            hidden = len(ordered) - _DETAIL_LIMIT * 4
            if hidden > 0:
                lines.append(f"| | | ... and {hidden} more fields (see mapping_discrepancies.csv) | | |")
        elif kind is Kind.TYPE_MISMATCH:
            lines += [
                "| Group | Index | Field | Expected | Actual | Indices with the expected type |",
                "|---|---|---|---|---|---|",
            ]
            for d in rows[:_DETAIL_LIMIT * 4]:
                lines.append(f"| {d.group} | {d.index} | `{d.field}` | {d.expected} | {d.actual} | {d.present_in} of {d.total} |")
            if len(rows) > _DETAIL_LIMIT * 4:
                lines.append(f"| | | ... and {len(rows) - _DETAIL_LIMIT * 4} more (see mapping_discrepancies.csv) | | | |")
        else:
            lines += ["| Group | Index | Expected | Actual |", "|---|---|---|---|"]
            for d in rows:
                lines.append(f"| {d.group} | {d.index} | {d.expected} | {d.actual} |")
        lines.append("")
    return "\n".join(lines) + "\n"
