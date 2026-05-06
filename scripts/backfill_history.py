#!/usr/bin/env python3
"""
Backfill docs/status/counts_history.csv from git history of the status CSV files.

For each unique date found in the git log of the four status CSVs, this script:
  1. Finds the latest commit on-or-before that date for each file
  2. Reads the CSV content at that commit via `git show`
  3. Applies split_by_version to derive latest/superseded counts
  4. Appends a row to counts_history.csv

Run once from anywhere inside the repository.  The script is idempotent —
dates that already exist in counts_history.csv are skipped, so it is safe
to re-run.

Usage:
    python scripts/backfill_history.py [--dry-run]
"""

import argparse
import csv
import io
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


# ── constants ────────────────────────────────────────────────────────────────

HISTORY_HEADER = (
    "date,"
    "missing_bundles_total,missing_bundles_latest,missing_bundles_superseded,"
    "missing_collections_total,missing_collections_latest,missing_collections_superseded,"
    "staged_bundles_total,staged_collections_total"
)

# Relative paths inside the repo for the four source files
STATUS_FILES = {
    "missing_bundles": "docs/status/missing_bundles_in_registry.csv",
    "missing_collections": "docs/status/missing_collections_in_registry.csv",
    "staged_bundles": "docs/status/staged_bundles_in_registry.csv",
    "staged_collections": "docs/status/staged_collections_in_registry.csv",
}

HISTORY_FILE = "docs/status/counts_history.csv"


# ── version splitting (mirrors generate_registry_status_reports.py) ──────────

def split_by_version(rows: list[list[str]]) -> tuple[list[list[str]], list[list[str]]]:
    """Split rows into (latest, superseded) by LID using numeric version comparison."""
    by_lid: dict[str, list[tuple[tuple[int, ...], list[str]]]] = defaultdict(list)
    for row in rows:
        lidvid = row[1] if len(row) > 1 else ""
        if "::" in lidvid:
            lid, ver_str = lidvid.rsplit("::", 1)
        else:
            lid, ver_str = lidvid, "0"
        try:
            ver_key: tuple[int, ...] = tuple(int(x) for x in ver_str.split("."))
        except ValueError:
            ver_key = (0,)
        by_lid[lid].append((ver_key, row))

    latest: list[list[str]] = []
    superseded: list[list[str]] = []
    for version_rows in by_lid.values():
        sorted_rows = sorted(version_rows, key=lambda x: x[0], reverse=True)
        latest.append(sorted_rows[0][1])
        superseded.extend(r for _, r in sorted_rows[1:])
    return latest, superseded


# ── git helpers ───────────────────────────────────────────────────────────────

def find_repo_root() -> Path:
    """Return the root of the git repository containing the current directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(result.stdout.strip())


def git_log_for_file(repo_dir: Path, filepath: str) -> list[tuple[str, str]]:
    """Return [(date, sha), ...] newest-first for all commits touching filepath."""
    result = subprocess.run(
        ["git", "log", "--follow", "--format=%as %H", "--", filepath],
        cwd=repo_dir, capture_output=True, text=True, check=True,
    )
    entries = []
    for line in result.stdout.strip().splitlines():
        if line:
            date_str, sha = line.split(" ", 1)
            entries.append((date_str, sha))
    return entries  # newest first


def sha_on_or_before(entries: list[tuple[str, str]], date: str) -> str | None:
    """Return the SHA of the latest commit on-or-before `date` (YYYY-MM-DD)."""
    for entry_date, sha in entries:  # entries are newest-first
        if entry_date <= date:
            return sha
    return None


def git_show_csv(repo_dir: Path, sha: str, filepath: str) -> list[list[str]]:
    """Return parsed CSV rows from `filepath` at commit `sha`. Returns [] if absent."""
    result = subprocess.run(
        ["git", "show", f"{sha}:{filepath}"],
        cwd=repo_dir, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    return [row for row in csv.reader(io.StringIO(result.stdout)) if row]


# ── history file helpers ──────────────────────────────────────────────────────

def load_existing_dates(history_path: Path) -> set[str]:
    """Return the set of dates already recorded in counts_history.csv."""
    if not history_path.exists():
        return set()
    dates = set()
    with open(history_path, "r") as f:
        for row in csv.reader(f):
            if row and row[0] != "date":  # skip header
                dates.add(row[0])
    return dates


def build_history_row(date: str, snapshots: dict[str, list[list[str]]]) -> str:
    """Build a CSV row string for the given date from snapshot rows."""
    mb_rows = snapshots["missing_bundles"]
    mc_rows = snapshots["missing_collections"]
    sb_rows = snapshots["staged_bundles"]
    sc_rows = snapshots["staged_collections"]

    mb_latest, mb_superseded = split_by_version(mb_rows)
    mc_latest, mc_superseded = split_by_version(mc_rows)

    return ",".join([
        date,
        str(len(mb_rows)),
        str(len(mb_latest)),
        str(len(mb_superseded)),
        str(len(mc_rows)),
        str(len(mc_latest)),
        str(len(mc_superseded)),
        str(len(sb_rows)),
        str(len(sc_rows)),
    ])


# ── main ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill counts_history.csv from git history of status CSV files",
        epilog="Run once from anywhere inside the repository. Safe to re-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rows that would be written without modifying counts_history.csv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        repo_dir = find_repo_root()
    except subprocess.CalledProcessError:
        print("ERROR: not inside a git repository", file=sys.stderr)
        return 1

    history_path = repo_dir / HISTORY_FILE

    # Load dates already recorded so we can skip them
    existing_dates = load_existing_dates(history_path)
    if existing_dates:
        print(f"Skipping {len(existing_dates)} date(s) already in {HISTORY_FILE}: "
              f"{', '.join(sorted(existing_dates))}")

    # Build the commit log for each status file
    file_logs: dict[str, list[tuple[str, str]]] = {}
    for key, filepath in STATUS_FILES.items():
        file_logs[key] = git_log_for_file(repo_dir, filepath)

    # Collect all unique dates across all files
    all_dates: set[str] = set()
    for entries in file_logs.values():
        for date_str, _ in entries:
            all_dates.add(date_str)

    new_dates = sorted(all_dates - existing_dates)
    if not new_dates:
        print("Nothing to backfill — counts_history.csv is already up to date.")
        return 0

    print(f"Backfilling {len(new_dates)} date(s): {', '.join(new_dates)}")

    rows_to_write: list[str] = []
    for date in new_dates:
        # For each file, get the content at the latest commit on-or-before this date
        snapshots: dict[str, list[list[str]]] = {}
        for key, filepath in STATUS_FILES.items():
            sha = sha_on_or_before(file_logs[key], date)
            if sha:
                snapshots[key] = git_show_csv(repo_dir, sha, filepath)
                print(f"  {date}  {key:25s} → {sha[:8]}  ({len(snapshots[key])} rows)")
            else:
                snapshots[key] = []
                print(f"  {date}  {key:25s} → (no commit found, using empty)")

        row = build_history_row(date, snapshots)
        rows_to_write.append(row)

    if args.dry_run:
        print("\n--- DRY RUN: rows that would be appended ---")
        if not existing_dates:
            print(HISTORY_HEADER)
        for row in rows_to_write:
            print(row)
        return 0

    # Write to the history file (append mode; create with header if new)
    write_header = not history_path.exists() or history_path.stat().st_size == 0
    with open(history_path, "a", newline="") as f:
        if write_header:
            f.write(HISTORY_HEADER + "\n")
        for row in rows_to_write:
            f.write(row + "\n")

    print(f"\nWrote {len(rows_to_write)} row(s) to {history_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
