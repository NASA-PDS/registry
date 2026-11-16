#!/usr/bin/env python3
r"""Roll up the per-node audits into one table of who has to act, node by node.

Reads ``<audits-dir>/<node>/metrics.json`` as written by audit_unprocessed_products.py and prints a Markdown
table with one row per node: products that need attention, split by who can fix them (the node, registry
operations, the sweepers team, or "needs a closer look" when the collection inventory was not read), the
collections stamped with empty refs that have a bundle (their bundle lists no members), and products that are
only waiting. It reads local files only.

Usage:
    AUDITS_DIR="<directory containing one sub-directory per node>"
    python scripts/audit_rollup.py --audits-dir "${AUDITS_DIR}" [--output FILE]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unprocessed_audit.ownership import OWNER_LABELS  # noqa: E402
from unprocessed_audit.ownership import Owner  # noqa: E402
from unprocessed_audit.regression import BaselineError  # noqa: E402
from unprocessed_audit.regression import Metrics  # noqa: E402
from unprocessed_audit.regression import load_metrics  # noqa: E402

logger = logging.getLogger(__name__)

_COLUMNS = [
    "Node",
    "Products examined",
    f"Needs attention: {OWNER_LABELS[Owner.NODE]}",
    f"Needs attention: {OWNER_LABELS[Owner.REGISTRY_OPERATIONS]}",
    f"Needs attention: {OWNER_LABELS[Owner.SWEEPERS_TEAM]}",
    f"Needs attention: {OWNER_LABELS[Owner.NEEDS_CHECK]}",
    "Collections whose bundle shows no members",
    "Waiting (no action)",
]


def load_all(audits_dir: Path) -> dict[str, Metrics]:
    """Read ``<audits-dir>/<node>/metrics.json`` for every node directory.

    Args:
        audits_dir: Directory with one sub-directory per node.

    Returns:
        Metrics keyed by node directory name, sorted by name.

    Raises:
        BaselineError: If a metrics file exists but cannot be read.
    """
    found: dict[str, Metrics] = {}
    for path in sorted(Path(audits_dir).glob("*/metrics.json")):
        found[path.parent.name] = load_metrics(path)
    return found


def render_table(all_metrics: dict[str, Metrics]) -> str:
    """Render the roll-up table.

    Args:
        all_metrics: Metrics keyed by node.

    Returns:
        Markdown, ending in a newline.
    """
    lines = ["| " + " | ".join(_COLUMNS) + " |", "|---|" + "--:|" * (len(_COLUMNS) - 1)]
    totals = [0] * (len(_COLUMNS) - 1)
    for node, m in all_metrics.items():
        owners = m.owners
        cells = [
            m.examined,
            owners.get(Owner.NODE.value, 0),
            owners.get(Owner.REGISTRY_OPERATIONS.value, 0),
            owners.get(Owner.SWEEPERS_TEAM.value, 0),
            owners.get(Owner.NEEDS_CHECK.value, 0),
            len(m.empty_refs_with_bundle),
            m.expected,
        ]
        totals = [t + c for t, c in zip(totals, cells)]
        lines.append(f"| {node} | " + " | ".join(f"{c:,}" for c in cells) + " |")
    lines.append("| **Total** | " + " | ".join(f"**{t:,}**" for t in totals) + " |")
    unchecked = {n: m.unverified_refs_missing for n, m in all_metrics.items() if m.unverified_refs_missing}
    note = ""
    if unchecked:
        listed = ", ".join(f"{n} ({count:,})" for n, count in unchecked.items())
        note = (
            "\nProducts that could not be checked against their collection's inventory are counted under "
            f"\"Needs a closer look\": {listed}.\n"
        )
    return "\n".join(lines) + "\n" + note


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 on success, 1 when no metrics are found or a file cannot be read.
    """
    parser = argparse.ArgumentParser(description="Roll up per-node audit metrics by who has to act.")
    parser.add_argument("--audits-dir", type=Path, required=True, metavar="DIR", help="Directory with <node>/metrics.json")
    parser.add_argument("--output", type=Path, default=None, metavar="FILE", help="Write the table here as well")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")
    try:
        all_metrics = load_all(args.audits_dir)
    except BaselineError as exc:
        logger.error("%s", exc)
        return 1
    if not all_metrics:
        logger.error("No <node>/metrics.json found under %s", args.audits_dir)
        return 1
    table = render_table(all_metrics)
    print(table)
    if args.output is not None:
        args.output.write_text(table, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
