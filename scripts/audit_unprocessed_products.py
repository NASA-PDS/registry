#!/usr/bin/env python3
r"""Audit NASA-PDS registry products that the registry sweepers' ancestry sweeper has not processed.

The ancestry sweeper writes ``ops:Provenance/ops:ancestor_refs`` and stamps
``ops:Provenance/ops:registry_sweepers_ancestry_version`` on each product it processes. Products
without current ancestry are missing from /members, /ancestors and related API results. Some are just
waiting for the sweeper or for a parent collection that is still loading; others are broken. This
script examines every API-visible (not superseded, archived or certified) non-aggregate product that
lacks current ancestry and assigns each one a rule, a severity (expected or anomalous) and a one-line
rationale. Where audit_collection.py answers "what is wrong with this collection", this script answers
"which products across the whole registry are missing ancestry, and why".

The audit is READ-ONLY: it issues only _search queries against OpenSearch. It talks to OpenSearch
directly because the public API does not expose the registry-refs indices.

Files written to --output-dir (none are meant to be committed):

  unprocessed_products.csv   one row per product, with its rule, severity and rationale
                             (unprocessed_products.csv.gz with --gzip)
  collections.csv            one row per collection with state, bundles and refs coverage
  anomalous_collections.txt  collection LIDVIDs to look at or re-harvest: those rooting anomalies and those
                             stamped with empty refs that have a bundle, for audit_collection.py --from-file
  summary.md                 the report; also printed to the terminal
  metrics.json               machine-readable totals, per-rule counts and collection lists; the
                             baseline for a later run's --check

Setup:
    Install registry-client dependencies before running registry queries:

        pip install -r scripts/requirements.txt

    Source your registry credentials into the shell environment before running:

        source ~/.pds/registry-client-prod.env

Usage:
    python scripts/audit_unprocessed_products.py --output-dir DIR [options]

Examples:
    # Dry run against one node, stopping after 5,000 candidates
    ENV_FILE="<path-to-your-registry-client-env-file>"
    NODE="<node-name>"
    python scripts/audit_unprocessed_products.py \
        --output-dir ./audit_unprocessed/ --env-file "$ENV_FILE" \
        --node "$NODE" --max-products 5000

    # Full run across every node (credentials sourced into the shell first)
    source "$ENV_FILE"
    python scripts/audit_unprocessed_products.py --output-dir ./audit_unprocessed/

    # Compare against a previous run, with a compressed products CSV
    PREVIOUS_CSV="<path-to-previous-unprocessed_products.csv>"
    python scripts/audit_unprocessed_products.py \
        --output-dir ./audit_unprocessed/ --previous-csv "$PREVIOUS_CSV" --gzip

    # Re-audit the worst collections found
    python scripts/audit_collection.py \
        --from-file ./audit_unprocessed/anomalous_collections.txt --check-files

Options:
    --output-dir DIR              Directory to write all output files to (required)
    --node NODE                   Limit the audit to <NODE>-registry and <NODE>-registry-refs;
                                  repeatable (default: discover every node)
    --collection-grace-days N     Days an unprocessed collection is left alone (default: 1)
    --product-grace-days N        Days a product waiting for its collection is left alone
                                  (default: 7)
    --ancestry-version N          Current ancestry version stamp (default: 7)
    --previous-csv FILE           A previous unprocessed_products.csv (or .csv.gz); the summary
                                  then reports products that are new, resolved and persisting
    --max-products N              Stop after N candidate products (for dry runs)
    --max-coverage-collections N  Refs coverage queries run once per collection, so only the N
                                  anomalous collections with the most affected products are
                                  queried (default: 200)
    --gzip                        Write the products CSV as unprocessed_products.csv.gz
    --inventory-cache-dir DIR     Keep downloaded collection inventories in DIR and reuse them in later
                                  runs, which saves the slow downloads; delete a file to refresh it
    --no-inventory                Do not download collection inventories. By default a collection's
                                  current inventory is read when one of its products is in no refs
                                  document, to tell stale refs from products the inventory does not
                                  list; without it those products are reported as refs_missing
    --check                       Evaluate regression invariants; exit 2 when one is violated. Without
                                  --baseline any anomalous product fails; with it only new anomalies do.
                                  Not allowed with --max-products
    --baseline FILE               metrics.json of an earlier run (same nodes and ancestry version);
                                  needs --check
    --no-mapping-check            With --check, skip the per-index check that the superseded_by field
                                  is mapped (searchable)
    --history-csv FILE            Append one row of run totals to FILE for trend charts
    --env-file FILE               Load credentials from FILE in addition to the shell
                                  environment (optional; shell-sourced vars take precedence via
                                  os.environ.setdefault)
    --timeout N                   Per-request timeout in seconds (default: 60)
    --log-level LEVEL             Logging verbosity: debug, info, warn, warning (default: info)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unprocessed_audit.classify import classify_collection  # noqa: E402
from unprocessed_audit.classify import classify_product  # noqa: E402
from unprocessed_audit.classify import needs_refs_lookup  # noqa: E402
from unprocessed_audit.model import CURRENT_ANCESTRY_VERSION  # noqa: E402
from unprocessed_audit.model import Collection  # noqa: E402
from unprocessed_audit.model import CollectionState  # noqa: E402
from unprocessed_audit.model import RefsCoverage  # noqa: E402
from unprocessed_audit.model import SUPERSEDED_FIELD  # noqa: E402
from unprocessed_audit.model import RegistryQueryError  # noqa: E402
from unprocessed_audit.model import Thresholds  # noqa: E402
from unprocessed_audit.registry import RegistryClient  # noqa: E402
from unprocessed_audit.registry import discover_nodes  # noqa: E402
from unprocessed_audit.registry import find_bundles  # noqa: E402
from unprocessed_audit.registry import get_refs_coverage  # noqa: E402
from unprocessed_audit.registry import iter_candidate_pages  # noqa: E402
from unprocessed_audit.registry import iter_collections  # noqa: E402
from unprocessed_audit.inventory import InventoryCache  # noqa: E402
from unprocessed_audit.inventory import make_session as make_inventory_session  # noqa: E402
from unprocessed_audit.registry import lookup_refs  # noqa: E402
from unprocessed_audit.registry import lookup_refs_by_lid  # noqa: E402
from unprocessed_audit.registry import make_registry_auth  # noqa: E402
from unprocessed_audit.registry import registry_endpoint_from_env  # noqa: E402
from unprocessed_audit.regression import METRICS_JSON  # noqa: E402
from unprocessed_audit.regression import BaselineError  # noqa: E402
from unprocessed_audit.regression import HistoryFormatError  # noqa: E402
from unprocessed_audit.regression import Metrics  # noqa: E402
from unprocessed_audit.regression import Violation  # noqa: E402
from unprocessed_audit.regression import append_history  # noqa: E402
from unprocessed_audit.regression import build_metrics  # noqa: E402
from unprocessed_audit.regression import check_comparable  # noqa: E402
from unprocessed_audit.regression import check_history_format  # noqa: E402
from unprocessed_audit.regression import evaluate  # noqa: E402
from unprocessed_audit.regression import find_unmapped_superseded  # noqa: E402
from unprocessed_audit.regression import load_metrics  # noqa: E402
from unprocessed_audit.regression import render_check_section  # noqa: E402
from unprocessed_audit.report import DiffCounts  # noqa: E402
from unprocessed_audit.report import ProductCsvWriter  # noqa: E402
from unprocessed_audit.report import Tally  # noqa: E402
from unprocessed_audit.report import compute_diff  # noqa: E402
from unprocessed_audit.report import load_previous_keys  # noqa: E402
from unprocessed_audit.report import render_summary  # noqa: E402
from unprocessed_audit.report import write_anomalous_collections  # noqa: E402
from unprocessed_audit.report import write_collections_csv  # noqa: E402

_DEFAULT_COLLECTION_GRACE_DAYS = 1.0
_DEFAULT_PRODUCT_GRACE_DAYS = 7.0
_DEFAULT_MAX_COVERAGE_COLLECTIONS = 200
_DEFAULT_TIMEOUT = 60
_PAGE_SIZE = 10000

PRODUCTS_CSV = "unprocessed_products.csv"
COLLECTIONS_CSV = "collections.csv"
ANOMALOUS_COLLECTIONS_TXT = "anomalous_collections.txt"
SUMMARY_MD = "summary.md"

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
}

logger = logging.getLogger(__name__)


# ── terminal colours ──────────────────────────────────────────────────────────


class Color:
    """ANSI color codes and helpers for terminal output."""

    RED = "\033[31m"
    GREEN = "\033[32m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @staticmethod
    def red(text: str) -> str:
        """Returns text wrapped in red ANSI color codes."""
        return f"{Color.RED}{text}{Color.RESET}"

    @staticmethod
    def green(text: str) -> str:
        """Returns text wrapped in green ANSI color codes."""
        return f"{Color.GREEN}{text}{Color.RESET}"

    @staticmethod
    def bold(text: str) -> str:
        """Returns text wrapped in bold ANSI escape codes."""
        return f"{Color.BOLD}{text}{Color.RESET}"


# ── env loading ───────────────────────────────────────────────────────────────


def load_env_file(path: Path) -> None:
    """Load environment variables from a .env / shell-export file.

    Args:
        path: Path to the env file. Lines starting with ``#`` and blank lines
            are ignored. An optional ``export `` prefix is stripped. Variables that are
            already set are never overwritten.
    """
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" in line:
                key, value = line.split("=", 1)
                v = value.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
                    v = v[1:-1]
                os.environ.setdefault(key.strip(), v)


def load_credentials(env_file: Path | None) -> None:
    """Supplement shell-environment credentials from an optional env file.

    Args:
        env_file: Optional path to a supplemental .env file. When ``None`` nothing is read.
    """
    if env_file is None:
        return
    if env_file.exists():
        load_env_file(env_file)
        logger.debug("Supplemented credentials from %s", env_file)
    else:
        logger.warning("--env-file path does not exist: %s", env_file)


# ── orchestration ─────────────────────────────────────────────────────────────


@dataclass
class AuditResult:
    """Outcome of one audit run.

    Attributes:
        tally: Accumulated counters.
        collections: Every collection examined, with state and bundles filled in.
        coverage: Refs coverage for the collections that were queried, keyed by LIDVID.
        diff: Comparison with the previous run, when ``--previous-csv`` was given.
        summary: The rendered ``summary.md`` text.
        output_dir: Directory the files were written to.
        metrics: The run's machine-readable metrics (also written to ``metrics.json``).
        violations: Invariants that failed; always empty unless ``--check`` was given.
        checked: Whether ``--check`` evaluated the invariants.
        paths: Files written, keyed by short name.
    """

    tally: Tally
    collections: list[Collection]
    coverage: dict[str, RefsCoverage]
    diff: DiffCounts | None
    summary: str
    output_dir: Path
    metrics: Metrics
    violations: list[Violation] = field(default_factory=list)
    checked: bool = False
    paths: dict[str, Path] = field(default_factory=dict)


def _classify_collections(collections: list[Collection], th: Thresholds) -> dict[str, list[Collection]]:
    """Set ``state`` on every collection and index them by LID.

    Args:
        collections: Collections to classify (modified in place).
        th: Run thresholds.

    Returns:
        Collections keyed by LID.
    """
    by_lid: dict[str, list[Collection]] = {}
    counts: dict[CollectionState, int] = {}
    superseded = 0
    for coll in collections:
        coll.state = classify_collection(coll, th)
        by_lid.setdefault(coll.lid, []).append(coll)
        if coll.superseded_by:
            superseded += 1
            continue
        counts[coll.state] = counts.get(coll.state, 0) + 1
    logger.info("Collections: %d current, %d superseded versions", len(collections) - superseded, superseded)
    for state in CollectionState:
        logger.info("  %s: %d", state.value, counts.get(state, 0))
    return by_lid


def _attach_bundles(client: RegistryClient, collections: list[Collection], nodes: list[str]) -> None:
    """Record the bundles of every stamped-with-empty-refs collection.

    Args:
        client: Registry client.
        collections: Classified collections (``bundle_lidvids`` is filled in place).
        nodes: Nodes to search.
    """
    empties = [c for c in collections if c.state is CollectionState.STAMPED_EMPTY_REFS and not c.superseded_by]
    if not empties:
        return
    lids = sorted({c.lid for c in empties})
    bundles = find_bundles(client, lids, nodes)
    for coll in empties:
        coll.bundle_lidvids = list(bundles.get(coll.lid, []))
    with_bundle = sum(1 for c in empties if c.bundle_lidvids)
    logger.info("Stamped collections with empty refs: %d (%d have a bundle)", len(empties), with_bundle)


def run_audit(args: argparse.Namespace, client: RegistryClient, now: datetime | None = None) -> AuditResult:
    """Run the audit and write every output file.

    Args:
        args: Parsed command-line arguments.
        client: Registry client (read-only).
        now: Reference time; defaults to the current UTC time. Injected so tests are deterministic.

    Returns:
        The tally, collections, coverage and rendered summary.

    Raises:
        RegistryQueryError: If a registry request fails. Files written so far are flushed first.
        BaselineError: If ``--baseline`` cannot be read or compared with this run. Raised before any product is
            examined.
        HistoryFormatError: If ``--history-csv`` exists with different columns. Raised before any product is
            examined.
    """
    now = now or datetime.now(timezone.utc)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    th = Thresholds(
        now=now,
        collection_grace_days=args.collection_grace_days,
        product_grace_days=args.product_grace_days,
        ancestry_version=args.ancestry_version,
    )

    nodes: list[str] = list(args.node) if args.node else discover_nodes(client)
    logger.info("Nodes: %s", ", ".join(nodes))

    # Fail before the long product scan when the comparison or the history file cannot work.
    baseline = load_metrics(args.baseline) if args.baseline is not None else None
    if baseline is not None:
        check_comparable(nodes, args.ancestry_version, baseline)
    if args.history_csv is not None:
        check_history_format(args.history_csv)

    collections = list(iter_collections(client, nodes))
    collections_by_lid = _classify_collections(collections, th)
    _attach_bundles(client, collections, nodes)

    inventory_cache = (
        None
        if args.no_inventory
        else InventoryCache(make_inventory_session(), args.timeout, cache_dir=args.inventory_cache_dir)
    )
    tally = Tally(collect_keys=args.previous_csv is not None)
    products_name = PRODUCTS_CSV + (".gz" if args.gzip else "")
    products_path = output_dir / products_name
    with ProductCsvWriter(products_path) as writer:
        for page in iter_candidate_pages(
            client, nodes, args.ancestry_version, page_size=_PAGE_SIZE, max_products=args.max_products
        ):
            lookups = [c.lidvid for c in page if needs_refs_lookup(c, th, collections_by_lid)]
            refs = lookup_refs(client, lookups, nodes) if lookups else {}
            looked_up = set(lookups)
            # A product no refs document lists by LIDVID may be listed under another version.
            unlisted_lids = sorted({c.lid for c in page if c.lidvid in looked_up and c.lidvid not in refs})
            listed_versions = lookup_refs_by_lid(client, unlisted_lids, nodes) if unlisted_lids else {}
            for candidate in page:
                checked = candidate.lidvid in looked_up
                verdict = classify_product(
                    candidate,
                    th,
                    collections_by_lid,
                    refs.get(candidate.lidvid) if checked else None,
                    refs_checked=checked,
                    listed_lidvid=listed_versions.get(candidate.lid) if checked else None,
                    inventory_for=inventory_cache,
                )
                writer.write(candidate, verdict, now)
                tally.add(candidate, verdict, now)
            logger.info("Examined %d products so far (%d anomalous)", tally.examined, tally.anomalous)

    coverage = _collect_coverage(client, collections, tally, nodes, args)

    paths = {"products": products_path}
    paths["collections"] = output_dir / COLLECTIONS_CSV
    write_collections_csv(paths["collections"], collections, coverage, tally.anomalous_collection_counts())
    paths["anomalous_collections"] = output_dir / ANOMALOUS_COLLECTIONS_TXT
    # The list holds the collections to look at or re-harvest: those rooting anomalous products, and those
    # stamped with empty refs that have a bundle (the bundle's /members is empty even though no product is
    # unprocessed). A superseded collection version is not re-harvested, so it is left out.
    superseded = {c.lidvid for c in collections if c.superseded_by}
    listed = [lidvid for lidvid in tally.collections if lidvid not in superseded]
    empty_refs_with_bundle = sorted(
        c.lidvid
        for c in collections
        if c.state is CollectionState.STAMPED_EMPTY_REFS and c.bundle_lidvids and not c.superseded_by
    )
    listed += [lidvid for lidvid in empty_refs_with_bundle if lidvid not in listed]
    write_anomalous_collections(paths["anomalous_collections"], listed)

    diff: DiffCounts | None = None
    if args.previous_csv is not None:
        diff = compute_diff(load_previous_keys(Path(args.previous_csv)), tally.keys)
        logger.info("Diff: %d new, %d resolved, %d persisting", diff.new, diff.resolved, diff.persisting)

    metrics = build_metrics(tally, collections, nodes, args.ancestry_version, now)
    violations: list[Violation] = []
    if args.check:
        if not args.no_mapping_check:
            metrics.unmapped_superseded = find_unmapped_superseded(client, nodes)
        violations = evaluate(metrics, baseline)
        logger.info("Regression check: %d invariants violated", len(violations))

    params = _run_params(args, nodes)
    summary = render_summary(tally, collections, coverage, th, params, diff)
    if args.check:
        summary += "\n" + render_check_section(violations, baseline, not args.no_mapping_check)
    paths["summary"] = output_dir / SUMMARY_MD
    paths["summary"].write_text(summary, encoding="utf-8")
    paths["metrics"] = output_dir / METRICS_JSON
    paths["metrics"].write_text(metrics.to_json(), encoding="utf-8")
    if args.history_csv is not None:
        append_history(args.history_csv, metrics)
        paths["history"] = Path(args.history_csv)

    return AuditResult(
        tally=tally,
        collections=collections,
        coverage=coverage,
        diff=diff,
        summary=summary,
        output_dir=output_dir,
        metrics=metrics,
        violations=violations,
        checked=args.check,
        paths=paths,
    )


def _collect_coverage(
    client: RegistryClient,
    collections: list[Collection],
    tally: Tally,
    nodes: list[str],
    args: argparse.Namespace,
) -> dict[str, RefsCoverage]:
    """Run refs coverage queries for the worst anomalous collections.

    Args:
        client: Registry client.
        collections: Every collection examined.
        tally: Counters that rank the anomalous collections.
        nodes: Nodes to search.
        args: Parsed arguments (``max_coverage_collections``, ``ancestry_version``).

    Returns:
        Coverage keyed by collection LIDVID, for the collections that were queried.
    """
    known = {c.lidvid: c for c in collections}
    worst = [lidvid for lidvid in tally.worst_collections(args.max_coverage_collections) if lidvid in known]
    coverage: dict[str, RefsCoverage] = {}
    for index, lidvid in enumerate(worst, start=1):
        coverage[lidvid] = get_refs_coverage(client, known[lidvid], nodes, args.ancestry_version)
        if index % 25 == 0 or index == len(worst):
            logger.info("Refs coverage: %d of %d collections", index, len(worst))
    skipped = len(tally.collections) - len(worst)
    if skipped > 0:
        logger.info("Refs coverage skipped for %d lower-impact collections (--max-coverage-collections)", skipped)
    return coverage


def _run_params(args: argparse.Namespace, nodes: list[str]) -> dict[str, object]:
    """Describe the run parameters for the summary headline."""
    params: dict[str, object] = {"Nodes": ", ".join(nodes) if nodes else "all"}
    if args.node:
        params["Node filter"] = ", ".join(args.node)
    if args.max_products is not None:
        params["Max products (partial run)"] = f"{args.max_products:,}"
    params["Refs coverage queried for up to"] = f"{args.max_coverage_collections} collections"
    if args.previous_csv is not None:
        params["Previous run"] = Path(args.previous_csv).name
    return params


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        The parsed namespace.
    """
    parser = argparse.ArgumentParser(
        description="Audit registry products that the ancestry sweeper has not processed.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        metavar="DIR",
        help="Directory to write all output files to",
    )
    parser.add_argument(
        "--node",
        action="append",
        default=None,
        metavar="NODE",
        help="Limit to <NODE>-registry and <NODE>-registry-refs; repeatable (default: discover every node)",
    )
    parser.add_argument(
        "--collection-grace-days",
        type=float,
        default=_DEFAULT_COLLECTION_GRACE_DAYS,
        metavar="N",
        help=f"Days an unprocessed collection is left alone (default: {_DEFAULT_COLLECTION_GRACE_DAYS:g})",
    )
    parser.add_argument(
        "--product-grace-days",
        type=float,
        default=_DEFAULT_PRODUCT_GRACE_DAYS,
        metavar="N",
        help=f"Days a product waiting for its collection is left alone (default: {_DEFAULT_PRODUCT_GRACE_DAYS:g})",
    )
    parser.add_argument(
        "--ancestry-version",
        type=int,
        default=CURRENT_ANCESTRY_VERSION,
        metavar="N",
        help=f"Current ancestry version stamp (default: {CURRENT_ANCESTRY_VERSION})",
    )
    parser.add_argument(
        "--previous-csv",
        type=Path,
        default=None,
        metavar="FILE",
        help="Previous unprocessed_products.csv (or .csv.gz) to report new, resolved and persisting products",
    )
    parser.add_argument(
        "--max-products",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N candidate products (for dry runs)",
    )
    parser.add_argument(
        "--max-coverage-collections",
        type=int,
        default=_DEFAULT_MAX_COVERAGE_COLLECTIONS,
        metavar="N",
        help=(
            "Refs coverage queries run per collection, so only the N anomalous collections with the most "
            f"affected products are queried (default: {_DEFAULT_MAX_COVERAGE_COLLECTIONS})"
        ),
    )
    parser.add_argument(
        "--gzip",
        action="store_true",
        help=f"Write the products CSV gzip-compressed as {PRODUCTS_CSV}.gz",
    )
    parser.add_argument(
        "--inventory-cache-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Keep downloaded collection inventories in DIR and reuse them in later runs, which saves the slow "
            "downloads. A kept inventory is never refreshed: delete it to fetch the current one"
        ),
    )
    parser.add_argument(
        "--no-inventory",
        action="store_true",
        help=(
            "Do not download collection inventories. By default the current inventory of a collection is "
            "read when one of its products is in no refs document, to tell stale refs from products the "
            "inventory does not list. Without it those products are reported as refs_missing"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Evaluate regression invariants and exit with code 2 when one is violated. Without --baseline any "
            "anomalous product fails; with it only anomalies that are new since that run fail. Not allowed "
            "with --max-products"
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        metavar="FILE",
        help="metrics.json of an earlier run (same nodes and ancestry version) to compare against; needs --check",
    )
    parser.add_argument(
        "--no-mapping-check",
        action="store_true",
        help=f"With --check, skip reading each index mapping to confirm {SUPERSEDED_FIELD} is searchable",
    )
    parser.add_argument(
        "--history-csv",
        type=Path,
        default=None,
        metavar="FILE",
        help="Append one row of run totals (per-rule counts included) to FILE, for trend charts",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "Optional path to a .env file to supplement credentials already sourced into the shell "
            "environment. Shell-sourced variables take precedence (loaded via os.environ.setdefault)."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=_DEFAULT_TIMEOUT,
        metavar="N",
        help=f"Per-request timeout in seconds (default: {_DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--log-level",
        "-l",
        default="info",
        choices=list(_LOG_LEVELS),
        metavar="LEVEL",
        help="Logging verbosity: debug, info, warn, warning (default: info)",
    )
    args = parser.parse_args(argv)
    if args.baseline is not None and not args.check:
        parser.error("--baseline needs --check")
    if args.check and args.max_products is not None:
        parser.error("--check cannot be used with --max-products: a partial run's counts are not comparable")
    return args


def _print_result(result: AuditResult) -> None:
    """Print the summary and a one-line status to the terminal."""
    print(result.summary)
    tally = result.tally
    status = f"{tally.anomalous:,} anomalous of {tally.examined:,} candidates"
    print(Color.red(status) if tally.anomalous else Color.green(status))
    if result.checked:
        if result.violations:
            print(Color.red(f"Regression check: {len(result.violations)} invariants violated"))
        else:
            print(Color.green("Regression check: passed"))
    print(f"Output files written to {result.output_dir}")


def main(argv: list[str] | None = None) -> int:
    """Entry point for the unprocessed product audit.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 on success (and, with ``--check``, when every invariant holds), 1 on a registry,
        authentication, baseline, history-file or unexpected error, 2 when ``--check`` finds a violated invariant.
    """
    args = parse_args(argv)
    logging.basicConfig(
        level=_LOG_LEVELS[args.log_level],
        stream=sys.stderr,
        format="%(levelname)s %(message)s",
    )

    if args.previous_csv is not None and not args.previous_csv.is_file():
        logger.error("--previous-csv file does not exist: %s", args.previous_csv)
        return 1

    try:
        load_credentials(args.env_file)
        logger.info("Authenticating to registry ...")
        auth = make_registry_auth()
        client = RegistryClient(
            auth, registry_endpoint_from_env(), timeout=args.timeout, refresh_auth=make_registry_auth
        )
        result = run_audit(args, client)
    except RegistryQueryError:
        logger.exception("Registry query failed; partial output may be in %s", args.output_dir)
        return 1
    except (BaselineError, HistoryFormatError) as exc:
        logger.error("%s", exc)
        return 1
    except Exception:  # noqa: BLE001 - last-resort process boundary
        logger.exception("Fatal error: unprocessed product audit failed")
        return 1

    _print_result(result)
    return 2 if result.violations else 0


if __name__ == "__main__":
    sys.exit(main())
