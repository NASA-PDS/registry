#!/usr/bin/env python3
r"""Pick a few example products from every group of anomalous products in the per-node audits.

The per-product CSV of an audit (``unprocessed_products.csv`` or ``.csv.gz``) can hold millions of rows. This script
reads it and writes ``product_samples.csv``: for each group (one rule in one collection) of anomalous products, the
group's size and up to N example products, chosen as the lowest LIDVIDs so that two runs give the same rows. Each row
carries the owner that fixes the group, so the file is small enough to commit and shows what every group looks like.
It reads local files only.

Usage:
    AUDITS_DIR="<directory containing one sub-directory per node, each with unprocessed_products.csv.gz>"
    OUTPUT_DIR="<directory to write <node>/product_samples.csv into>"
    python scripts/audit_product_samples.py --audits-dir "${AUDITS_DIR}" --output-dir "${OUTPUT_DIR}" --per-group 10
"""

from __future__ import annotations

import argparse
import bisect
import csv
import gzip
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unprocessed_audit.model import Rule  # noqa: E402
from unprocessed_audit.model import Severity  # noqa: E402
from unprocessed_audit.ownership import Owner  # noqa: E402
from unprocessed_audit.ownership import owner_of  # noqa: E402

logger = logging.getLogger(__name__)

SAMPLE_COLUMNS = [
    "node",
    "owner",
    "rule",
    "collection_lidvid",
    "products_in_group",
    "lidvid",
    "product_class",
    "harvest_date_time",
    "rationale",
]
NO_COLLECTION = "(none found)"
_UNVERIFIED_MARKER = "inventory was not used"
_OWNER_ORDER = {owner.value: index for index, owner in enumerate(Owner)}

Group = tuple[str, str]
"""``(rule, collection_lidvid)``."""


def owner_for(rule: str, rationale: str) -> str:
    """Return the owner of a row: a ``refs_missing`` row reached without the inventory needs a closer look."""
    verified = _UNVERIFIED_MARKER not in rationale
    return owner_of(Rule(rule), verified=verified).value


def _open_rows(path: Path) -> Iterator[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:  # type: ignore[operator]
        yield from csv.DictReader(handle)


def collect_samples(path: Path, per_group: int) -> tuple[dict[Group, int], dict[Group, list[dict[str, str]]]]:
    """Read a per-product CSV and keep the lowest-LIDVID rows of every anomalous group.

    Args:
        path: ``unprocessed_products.csv`` or ``.csv.gz``.
        per_group: Maximum example rows kept per group.

    Returns:
        ``(sizes, samples)``: the number of anomalous rows per ``(rule, collection_lidvid)`` group, and the example
        rows of each group, ordered by LIDVID.
    """
    sizes: dict[Group, int] = {}
    samples: dict[Group, list[dict[str, str]]] = {}
    for row in _open_rows(path):
        if row.get("severity") != Severity.ANOMALOUS.value:
            continue
        group = (row["rule"], row.get("collection_lidvid") or NO_COLLECTION)
        sizes[group] = sizes.get(group, 0) + 1
        kept = samples.setdefault(group, [])
        keys = [r["lidvid"] for r in kept]
        position = bisect.bisect_left(keys, row["lidvid"])
        if position < per_group:
            kept.insert(position, row)
            del kept[per_group:]
    return sizes, samples


def sample_rows(node: str, path: Path, per_group: int) -> list[dict[str, str]]:
    """Return the sample rows of one node, largest groups of each owner first.

    Args:
        node: Node name for the ``node`` column.
        path: The node's per-product CSV.
        per_group: Maximum example rows per group.

    Returns:
        Rows with the ``SAMPLE_COLUMNS`` keys.
    """
    sizes, samples = collect_samples(path, per_group)
    rows: list[dict[str, str]] = []
    for (rule, collection), kept in samples.items():
        for row in kept:
            rows.append(
                {
                    "node": node,
                    "owner": owner_for(rule, row.get("rationale", "")),
                    "rule": rule,
                    "collection_lidvid": collection,
                    "products_in_group": str(sizes[(rule, collection)]),
                    "lidvid": row["lidvid"],
                    "product_class": row.get("product_class", ""),
                    "harvest_date_time": row.get("harvest_date_time", ""),
                    "rationale": row.get("rationale", ""),
                }
            )
    rows.sort(
        key=lambda r: (_OWNER_ORDER[r["owner"]], -int(r["products_in_group"]), r["rule"], r["collection_lidvid"], r["lidvid"])
    )
    return rows


def find_products_csv(node_dir: Path) -> Path | None:
    """Return the per-product CSV in a node's audit directory, or ``None``."""
    for name in ("unprocessed_products.csv.gz", "unprocessed_products.csv"):
        if (node_dir / name).is_file():
            return node_dir / name
    return None


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 on success, 1 when no node directory has a per-product CSV.
    """
    parser = argparse.ArgumentParser(description="Write example products of every anomalous group, per node.")
    parser.add_argument("--audits-dir", type=Path, required=True, metavar="DIR", help="Directory with <node>/ audits")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Where to write <node>/product_samples.csv (default: --audits-dir)",
    )
    parser.add_argument("--per-group", type=int, default=10, metavar="N", help="Example products per group (default: 10)")
    args = parser.parse_args(argv)
    if args.per_group < 1:
        parser.error("--per-group must be at least 1")
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")

    output_dir = args.output_dir or args.audits_dir
    written = 0
    for node_dir in sorted(p for p in args.audits_dir.iterdir() if p.is_dir()):
        products = find_products_csv(node_dir)
        if products is None:
            continue
        rows = sample_rows(node_dir.name, products, args.per_group)
        target = output_dir / node_dir.name / "product_samples.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=SAMPLE_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        groups = len({(r["rule"], r["collection_lidvid"]) for r in rows})
        logger.info("%s: %d example products from %d groups -> %s", node_dir.name, len(rows), groups, target)
        written += 1
    if not written:
        logger.error("No <node>/unprocessed_products.csv[.gz] found under %s", args.audits_dir)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
