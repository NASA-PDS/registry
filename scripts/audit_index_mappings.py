#!/usr/bin/env python3
r"""Audit the OpenSearch index mappings of every registry node for discrepancies.

Each node has its own ``<node>-registry`` index, created at a different time, so their mappings drift. A field
that is missing from a mapping is returned in ``_source`` but cannot be searched (for example
``ops:Provenance/ops:superseded_by`` on the ATM index); a field mapped with different types on different nodes
behaves differently under the same query. The audit reads ``GET /<index>/_mapping`` for every node (optionally
the ``<node>-registry-refs`` indices too), compares the indices of a group with each other, and reports:

  missing_field      defined on most indices of the group, absent on this one
  type_mismatch      defined with a different type than on most indices
  dynamic_mismatch   the index's ``dynamic`` setting differs from most indices
  index_missing      a registry-refs index that does not exist

Fields starting with ``ops:`` and the core top-level fields (``lid``, ``lidvid``, ``vid``, ``title``, ...) must be
mapped on every node, so their discrepancies are errors, as is any type conflict. Any other missing field
(``pds:...``, ``ref_lid_*``) is a warning, and fields defined on fewer than --presence-threshold of the indices are
node-specific and not reported as missing.

An index is named after its node (``<node>-registry``, ``<node>-registry-refs``). The ATM products index is
``temp-atm-registry`` behind the alias ``atm-registry``, while its refs index is ``atm-registry-refs``: name that
node ``atm`` with --node, because node discovery returns the concrete name ``temp-atm`` and its refs index would
be reported missing.

The audit is READ-ONLY: it only issues GET /<index>/_mapping.

Files written to --output-dir:

  mapping_discrepancies.csv  one row per discrepancy
  mapping_matrix.csv         one row per field, one column per index, with the mapped type
  mapping_summary.md         the report; also printed to the terminal

Setup:
    pip install -r scripts/requirements.txt
    source ~/.pds/registry-client-prod.env

Usage:
    python scripts/audit_index_mappings.py --output-dir DIR [options]

Examples:
    # Every node's registry index
    python scripts/audit_index_mappings.py --output-dir ./audit_mappings/

    # Include the registry-refs indices, and fail (exit 2) when there is an error-level discrepancy
    python scripts/audit_index_mappings.py --output-dir ./audit_mappings/ --include-refs --check

Options:
    --output-dir DIR        Directory to write all output files to (required)
    --node NODE             Limit to <NODE>-registry (and -refs); repeatable (default: discover every node)
    --include-refs          Also compare the <node>-registry-refs indices
    --known-node NODE       Tenant node name; repeatable (default: atm, en, geo, img, naif, ppi, psa, rms,
                            sbnpsi, sbnumd). A discovered index prefix that is not a tenant node is listed as
                            possibly stale or test data (candidates for cleanup) and left out of the comparison
    --presence-threshold F  Fraction of a group's indices that must define a field for it to be expected on all
                            of them (default: 0.8)
    --check                 Exit with code 2 when an error-level discrepancy is found
    --env-file FILE         Load credentials from FILE in addition to the shell environment
    --timeout N             Per-request timeout in seconds (default: 120)
    --log-level LEVEL       Logging verbosity: debug, info, warn, warning (default: info)

Exit codes: 0 on success (and, with --check, no error-level discrepancy), 1 on an error, 2 when --check finds
an error-level discrepancy.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_unprocessed_products import Color  # noqa: E402
from audit_unprocessed_products import load_credentials  # noqa: E402
from unprocessed_audit.mapping_audit import DEFAULT_PRESENCE_THRESHOLD  # noqa: E402
from unprocessed_audit.mapping_audit import GROUP_REFS  # noqa: E402
from unprocessed_audit.mapping_audit import GROUP_REGISTRY  # noqa: E402
from unprocessed_audit.mapping_audit import Discrepancy  # noqa: E402
from unprocessed_audit.mapping_audit import IndexMapping  # noqa: E402
from unprocessed_audit.mapping_audit import Severity  # noqa: E402
from unprocessed_audit.mapping_audit import StaleIndex  # noqa: E402
from unprocessed_audit.mapping_audit import analyze  # noqa: E402
from unprocessed_audit.mapping_audit import describe_possibly_stale  # noqa: E402
from unprocessed_audit.mapping_audit import read_mappings  # noqa: E402
from unprocessed_audit.mapping_audit import render_summary  # noqa: E402
from unprocessed_audit.mapping_audit import write_discrepancies_csv  # noqa: E402
from unprocessed_audit.mapping_audit import write_matrix_csv  # noqa: E402
from unprocessed_audit.mapping_audit import write_stale_csv  # noqa: E402
from unprocessed_audit.model import TENANT_NODES  # noqa: E402
from unprocessed_audit.model import RegistryQueryError  # noqa: E402
from unprocessed_audit.registry import RegistryClient  # noqa: E402
from unprocessed_audit.registry import discover_nodes  # noqa: E402
from unprocessed_audit.registry import make_registry_auth  # noqa: E402
from unprocessed_audit.registry import registry_endpoint_from_env  # noqa: E402
from unprocessed_audit.registry import split_tenant_nodes  # noqa: E402

_DEFAULT_TIMEOUT = 120
DISCREPANCIES_CSV = "mapping_discrepancies.csv"
MATRIX_CSV = "mapping_matrix.csv"
SUMMARY_MD = "mapping_summary.md"
STALE_CSV = "mapping_possibly_stale.csv"

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
}

logger = logging.getLogger(__name__)


@dataclass
class MappingAuditResult:
    """Outcome of one mapping audit.

    Attributes:
        mappings: Flattened mapping of every index read.
        discrepancies: Differences found.
        summary: The rendered Markdown report.
        output_dir: Directory the files were written to.
        paths: Files written, keyed by short name.
        stale: Indices left out of the comparison because they are not named after a tenant node.
    """

    mappings: list[IndexMapping]
    discrepancies: list[Discrepancy]
    summary: str
    output_dir: Path
    paths: dict[str, Path]
    stale: list[StaleIndex] = field(default_factory=list)

    @property
    def errors(self) -> list[Discrepancy]:
        """Discrepancies with error severity."""
        return [d for d in self.discrepancies if d.severity is Severity.ERROR]


def run_audit(args: argparse.Namespace, client: RegistryClient) -> MappingAuditResult:
    """Read every mapping, compare them and write the output files.

    Args:
        args: Parsed command-line arguments.
        client: Registry client (read-only).

    Returns:
        The mappings, discrepancies and report.

    Raises:
        RegistryQueryError: If a mapping cannot be read.
    """
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stale: list[StaleIndex] = []
    if args.node:
        nodes: list[str] = list(args.node)
    else:
        nodes, stale_nodes = split_tenant_nodes(discover_nodes(client), args.known_node or TENANT_NODES)
        if stale_nodes:
            logger.warning("Indices that are not tenant nodes, possibly stale: %s", ", ".join(stale_nodes))
            stale = describe_possibly_stale(client, stale_nodes)
    logger.info("Nodes: %s", ", ".join(nodes))
    groups = [GROUP_REGISTRY, GROUP_REFS] if args.include_refs else [GROUP_REGISTRY]

    mappings = read_mappings(client, nodes, groups)
    discrepancies = analyze(mappings, args.presence_threshold)
    logger.info("Read %d mappings; %d discrepancies", len(mappings), len(discrepancies))

    paths = {
        "discrepancies": output_dir / DISCREPANCIES_CSV,
        "matrix": output_dir / MATRIX_CSV,
        "summary": output_dir / SUMMARY_MD,
    }
    write_discrepancies_csv(paths["discrepancies"], discrepancies)
    write_matrix_csv(paths["matrix"], mappings)
    if stale:
        paths["stale"] = output_dir / STALE_CSV
        write_stale_csv(paths["stale"], stale)
    summary = render_summary(mappings, discrepancies, args.presence_threshold, stale)
    paths["summary"].write_text(summary, encoding="utf-8")
    return MappingAuditResult(mappings, discrepancies, summary, output_dir, paths, stale)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        The parsed namespace.
    """
    parser = argparse.ArgumentParser(
        description="Audit registry index mappings for discrepancies between nodes.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output-dir", type=Path, required=True, metavar="DIR", help="Directory for the output files")
    parser.add_argument(
        "--node",
        action="append",
        default=None,
        metavar="NODE",
        help="Limit to <NODE>-registry (and -refs); repeatable (default: discover every node)",
    )
    parser.add_argument("--include-refs", action="store_true", help="Also compare the <node>-registry-refs indices")
    parser.add_argument(
        "--known-node",
        action="append",
        default=None,
        metavar="NODE",
        help=(
            "Tenant node name; repeatable (default: " + ", ".join(TENANT_NODES) + "). A discovered index prefix "
            "that is not a tenant node is reported as possibly stale instead of being compared"
        ),
    )
    parser.add_argument(
        "--presence-threshold",
        type=float,
        default=DEFAULT_PRESENCE_THRESHOLD,
        metavar="F",
        help=f"Fraction of indices that must define a field for it to be expected on all (default: {DEFAULT_PRESENCE_THRESHOLD})",
    )
    parser.add_argument("--check", action="store_true", help="Exit with code 2 when an error-level discrepancy is found")
    parser.add_argument("--env-file", type=Path, default=None, metavar="FILE", help="Supplemental credentials file")
    parser.add_argument(
        "--timeout",
        type=int,
        default=_DEFAULT_TIMEOUT,
        metavar="N",
        help=f"Per-request timeout in seconds (default: {_DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--log-level", "-l", default="info", choices=list(_LOG_LEVELS), metavar="LEVEL", help="Logging verbosity (default: info)"
    )
    args = parser.parse_args(argv)
    if not 0 < args.presence_threshold <= 1:
        parser.error("--presence-threshold must be above 0 and at most 1")
    return args


def main(argv: list[str] | None = None) -> int:
    """Entry point for the index mapping audit.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 on success, 1 on a registry or unexpected error, 2 when ``--check`` finds an error-level
        discrepancy.
    """
    args = parse_args(argv)
    logging.basicConfig(level=_LOG_LEVELS[args.log_level], stream=sys.stderr, format="%(levelname)s %(message)s")
    try:
        load_credentials(args.env_file)
        logger.info("Authenticating to registry ...")
        client = RegistryClient(
            make_registry_auth(), registry_endpoint_from_env(), timeout=args.timeout, refresh_auth=make_registry_auth
        )
        result = run_audit(args, client)
    except RegistryQueryError:
        logger.exception("Registry query failed")
        return 1
    except Exception:  # noqa: BLE001 - last-resort process boundary
        logger.exception("Fatal error: index mapping audit failed")
        return 1

    print(result.summary)
    errors = result.errors
    status = f"{len(errors)} error-level discrepancies, {len(result.discrepancies) - len(errors)} warnings"
    print(Color.red(status) if errors else Color.green(status))
    if result.stale:
        names = ", ".join(s.index for s in result.stale)
        print(f"Possibly stale or test indices (candidates for cleanup, not compared): {names}")
    print(f"Output files written to {result.output_dir}")
    return 2 if args.check and errors else 0


if __name__ == "__main__":
    sys.exit(main())
