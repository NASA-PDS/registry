#!/usr/bin/env python3
r"""Count the API-visible products of every node, as the denominator of the registry report card.

A product is API-visible when its archive status is ``archived`` or ``certified`` and it is not superseded. The
script issues one read-only ``_count`` per node index and writes a small JSON file:

    {"generated": "2026-11-17", "visible_products": {"atm": 6955786, "en": 1234, ...}}

Setup:
    pip install -r scripts/requirements.txt
    source ~/.pds/registry-client-prod.env

Usage:
    python scripts/collect_node_totals.py --output docs/status/fidelity/node_totals.json

Options:
    --output FILE     File to write (required)
    --node NODE       Limit to one node; repeatable (default: every tenant node)
    --env-file FILE   Load credentials from FILE in addition to the shell environment
    --timeout N       Per-request timeout in seconds (default: 120)
    --log-level LEVEL Logging verbosity: debug, info, warn, warning (default: info)

Exit codes: 0 on success, 1 on a registry or unexpected error, 2 on invalid arguments.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_unprocessed_products import load_credentials  # noqa: E402
from unprocessed_audit.model import TENANT_NODES  # noqa: E402
from unprocessed_audit.model import RegistryQueryError  # noqa: E402
from unprocessed_audit.registry import RegistryClient  # noqa: E402
from unprocessed_audit.registry import api_visible_clauses  # noqa: E402
from unprocessed_audit.registry import make_registry_auth  # noqa: E402
from unprocessed_audit.registry import registry_endpoint_from_env  # noqa: E402
from unprocessed_audit.registry import registry_index  # noqa: E402

logger = logging.getLogger(__name__)

_LOG_LEVELS = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARNING, "warning": logging.WARNING}


def count_visible_products(client: RegistryClient, nodes: Sequence[str]) -> dict[str, int]:
    """Count the API-visible products of each node.

    Args:
        client: Registry client (read-only).
        nodes: Node names.

    Returns:
        Product count per node.

    Raises:
        RegistryQueryError: If a count fails.
    """
    totals: dict[str, int] = {}
    for node in nodes:
        totals[node] = client.count(registry_index([node]), {"query": {"bool": api_visible_clauses()}})
        logger.info("%s: %s API-visible products", node, f"{totals[node]:,}")
    return totals


def write_totals(path: Path, totals: dict[str, int], today: date) -> None:
    """Write the totals file.

    Args:
        path: File to write.
        totals: Product count per node.
        today: Date recorded as the time of the counts.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {"generated": today.isoformat(), "visible_products": dict(sorted(totals.items()))}
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Count the API-visible products of every node.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--node", action="append", default=[])
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--log-level", choices=sorted(_LOG_LEVELS), default="info")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 on success, 1 on a registry or unexpected error.
    """
    args = parse_args(argv)
    logging.basicConfig(level=_LOG_LEVELS[args.log_level], stream=sys.stderr, format="%(levelname)s %(message)s")
    try:
        load_credentials(args.env_file)
        client = RegistryClient(
            make_registry_auth(), registry_endpoint_from_env(), timeout=args.timeout, refresh_auth=make_registry_auth
        )
        totals = count_visible_products(client, args.node or sorted(TENANT_NODES))
        write_totals(args.output, totals, date.today())
    except RegistryQueryError:
        logger.exception("Registry query failed")
        return 1
    except Exception:  # noqa: BLE001 - last-resort process boundary
        logger.exception("Fatal error: node totals failed")
        return 1
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
