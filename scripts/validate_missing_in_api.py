#!/usr/bin/env python3
"""
Validate that LIDVIDs listed in the missing products CSVs are truly absent from
the PDS Search API.

For each LIDVID in the overall missing_bundles_in_registry.csv and
missing_collections_in_registry.csv, the script queries:

    https://pds.nasa.gov/api/search/1/products/{lidvid}

and records the HTTP status code.  Products that return HTTP 200 are
**unexpectedly found** in the API and should be investigated.

Results are written to docs/status/validation_results.csv and a short
summary is printed to stdout.

Usage:
    python scripts/validate_missing_in_api.py [options]

Options:
    --bundles FILE      Path to missing bundles CSV  (default: docs/status/missing_bundles_in_registry.csv)
    --collections FILE  Path to missing collections CSV  (default: docs/status/missing_collections_in_registry.csv)
    --api-base URL      Base API URL  (default: https://pds.nasa.gov/api/search/1)
    --output FILE       Output CSV path  (default: docs/status/validation_results.csv)
    --workers N         Concurrent HTTP workers  (default: 10)
    --timeout N         Per-request timeout in seconds  (default: 30)
    --found-only        Only write rows where the product WAS found in the API (200)
    --dry-run           Print LIDVIDs that would be checked without querying the API
"""

import argparse
import csv
import random
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ── helpers ───────────────────────────────────────────────────────────────────

def make_session(timeout: int) -> requests.Session:
    """Return a requests Session with retries and a shared timeout."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers["User-Agent"] = "pds-registry-validator/1.0"
    return session


def read_csv_rows(path: Path) -> list[tuple[str, str, str]]:
    """Return list of (node, lidvid, product_class) from a status CSV."""
    rows = []
    with open(path, "r") as f:
        for row in csv.reader(f):
            if row and len(row) >= 3:
                rows.append((row[0].strip(), row[1].strip(), row[2].strip()))
    return rows


def check_lidvid(
    session: requests.Session,
    api_base: str,
    node: str,
    lidvid: str,
    product_class: str,
    timeout: int,
) -> dict:
    """Query the API for one LIDVID and return a result dict."""
    encoded = urllib.parse.quote(lidvid, safe="")
    url = f"{api_base}/products/{encoded}"
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        status = resp.status_code
    except requests.exceptions.Timeout:
        status = -1  # sentinel for timeout
    except requests.exceptions.RequestException:
        status = -2  # sentinel for connection error

    return {
        "node": node,
        "lidvid": lidvid,
        "product_class": product_class,
        "http_status": status,
        "in_api": status == 200,
    }


# ── output ────────────────────────────────────────────────────────────────────

FIELDNAMES = ["node", "lidvid", "product_class", "http_status", "in_api"]


def write_results(results: list[dict], output_path: Path, found_only: bool) -> None:
    rows = [r for r in results if r["in_api"]] if found_only else results
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(results: list[dict]) -> None:
    total = len(results)
    found = sum(1 for r in results if r["in_api"])
    not_found = sum(1 for r in results if r["http_status"] == 404)
    timeouts = sum(1 for r in results if r["http_status"] == -1)
    errors = sum(1 for r in results if r["http_status"] == -2)
    other = total - found - not_found - timeouts - errors

    print("\n── Validation Summary ───────────────────────────────")
    print(f"  Total checked          : {total}")
    print(f"  Confirmed missing (404): {not_found}")
    print(f"  FOUND in API (200) ⚠️  : {found}")
    print(f"  Other HTTP status      : {other}")
    print(f"  Timeouts               : {timeouts}")
    print(f"  Connection errors      : {errors}")

    if found:
        print(f"\n  ⚠️  {found} product(s) returned 200 — check validation_results.csv")
        by_node: dict[str, int] = {}
        for r in results:
            if r["in_api"]:
                by_node[r["node"]] = by_node.get(r["node"], 0) + 1
        for node, count in sorted(by_node.items()):
            print(f"     {node}: {count}")
    else:
        print("\n  ✅ All queried products confirmed absent from API")
    print("─────────────────────────────────────────────────────")


# ── main ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).parent.parent
    status_dir = repo_root / "docs" / "status"

    parser = argparse.ArgumentParser(
        description="Validate missing products are absent from the PDS Search API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--bundles",
        type=Path,
        default=status_dir / "missing_bundles_in_registry.csv",
        metavar="FILE",
        help="Missing bundles CSV (default: docs/status/missing_bundles_in_registry.csv)",
    )
    parser.add_argument(
        "--collections",
        type=Path,
        default=status_dir / "missing_collections_in_registry.csv",
        metavar="FILE",
        help="Missing collections CSV (default: docs/status/missing_collections_in_registry.csv)",
    )
    parser.add_argument(
        "--api-base",
        default="https://pds.nasa.gov/api/search/1",
        metavar="URL",
        help="PDS Search API base URL (default: https://pds.nasa.gov/api/search/1)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=status_dir / "validation_results.csv",
        metavar="FILE",
        help="Output CSV path (default: docs/status/validation_results.csv)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        metavar="N",
        help="Concurrent HTTP workers (default: 10)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="N",
        help="Per-request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=500,
        metavar="N",
        help="Randomly sample up to N LIDVIDs from the full pool (default: 500, 0 = all)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="N",
        help="Random seed for reproducible sampling",
    )
    parser.add_argument(
        "--found-only",
        action="store_true",
        help="Only write rows where the product was found in the API (200)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print LIDVIDs that would be checked without querying the API",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Load input CSVs
    all_rows: list[tuple[str, str, str]] = []
    for csv_path in (args.bundles, args.collections):
        if not csv_path.exists():
            print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
            return 1
        rows = read_csv_rows(csv_path)
        print(f"Loaded {len(rows):>5} rows from {csv_path.name}")
        all_rows.extend(rows)

    # Random sample if requested
    if args.sample and args.sample < len(all_rows):
        rng = random.Random(args.seed)
        all_rows = rng.sample(all_rows, args.sample)
        seed_note = f" (seed={args.seed})" if args.seed is not None else ""
        print(f"Randomly sampled {args.sample} LIDVIDs from pool{seed_note}")

    total = len(all_rows)
    print(f"\nTotal LIDVIDs to check: {total}")

    if args.dry_run:
        print("\n── DRY RUN: LIDVIDs that would be queried ──────────")
        for node, lidvid, product_class in all_rows:
            encoded = urllib.parse.quote(lidvid, safe="")
            print(f"  {args.api_base}/products/{encoded}")
        return 0

    # Run checks concurrently
    session = make_session(args.timeout)
    results: list[dict] = [{}] * total
    completed = 0
    start = time.monotonic()

    print(f"Querying API with {args.workers} workers …\n")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_idx = {
            executor.submit(
                check_lidvid,
                session,
                args.api_base,
                node,
                lidvid,
                product_class,
                args.timeout,
            ): idx
            for idx, (node, lidvid, product_class) in enumerate(all_rows)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            result = future.result()
            results[idx] = result
            completed += 1

            status = result["http_status"]
            flag = "⚠️  FOUND" if result["in_api"] else ("TIMEOUT" if status == -1 else "ERR" if status == -2 else str(status))

            if completed % 50 == 0 or result["in_api"]:
                elapsed = time.monotonic() - start
                rate = completed / elapsed if elapsed > 0 else 0
                print(
                    f"  [{completed:>4}/{total}] {flag:8}  {result['lidvid'][:70]}"
                    f"  ({rate:.1f} req/s)"
                )

    elapsed = time.monotonic() - start
    print(f"\nCompleted {total} requests in {elapsed:.1f}s "
          f"({total / elapsed:.1f} req/s average)")

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_results(results, args.output, args.found_only)
    label = "found-only rows" if args.found_only else "rows"
    written = sum(1 for r in results if r["in_api"]) if args.found_only else total
    print(f"Wrote {written} {label} → {args.output}")

    print_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
