#!/usr/bin/env python3
"""Detect (and optionally delete) stale LDD_Info sentinel records across all PDS node registry -dd indexes.

A stale sentinel is a document in a ``-dd`` index where:
- ``class_name = "LDD_Info"``  (the sentinel written by ``JsonLddLoader.writeLddInfo()``)
- Zero sibling documents exist for that namespace with ``class_name != "LDD_Info"`` (no actual field defs)

Until stale sentinels are removed, harvest silently skips re-loading the affected namespaces,
causing persistent "Could not find the data type for the field" failures.

Progress is checkpointed to a JSON file after each sentinel is checked, so an interrupted run
resumes from where it left off.  Use --reset to discard the checkpoint and start over.

Environment variables required (same as generate_registry_status_reports.py):
    REQUEST_SIGNER_AWS_ACCOUNT
    REQUEST_SIGNER_AWS_REGION
    REQUEST_SIGNER_CLIENT_ID
    REQUEST_SIGNER_USER_POOL_ID
    REQUEST_SIGNER_IDENTITY_POOL_ID
    REQUEST_SIGNER_AOSS_ENDPOINT
    REQUEST_SIGNER_COGNITO_USER
    REQUEST_SIGNER_COGNITO_PASSWORD

The script will look for a .env file in the following locations (in order):
    1. $HOME/.pds/.registry-client
    2. ./.env (repository root)
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

_PDS_CLIENT = str(Path(sys.executable).parent / "pds-registry-client")
_SENTINEL_PAGE_SIZE = 1000

# Retry settings for transient connection errors
_MAX_RETRIES = 5
_RETRY_BACKOFF_BASE = 2  # seconds; delay = base ** attempt (2, 4, 8, 16, 32)


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    NC = "\033[0m"


def print_info(message: str) -> None:
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")


def print_warning(message: str) -> None:
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def print_error(message: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def print_section(message: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.CYAN}{message}{Colors.NC}")


def load_env_file(env_file: Path) -> None:
    """Load environment variables from a .env file."""
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value


def check_required_vars() -> list[str]:
    """Check if all required environment variables are set."""
    required_vars = [
        "REQUEST_SIGNER_AWS_ACCOUNT",
        "REQUEST_SIGNER_AWS_REGION",
        "REQUEST_SIGNER_CLIENT_ID",
        "REQUEST_SIGNER_USER_POOL_ID",
        "REQUEST_SIGNER_IDENTITY_POOL_ID",
        "REQUEST_SIGNER_AOSS_ENDPOINT",
        "REQUEST_SIGNER_COGNITO_USER",
        "REQUEST_SIGNER_COGNITO_PASSWORD",
    ]
    return [var for var in required_vars if not os.environ.get(var)]


def run_query(query: dict[str, Any], endpoint: str) -> dict[str, Any]:
    """Run a query dict using pds-registry-client, retrying on transient connection errors."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(query, f)
        tmp = Path(f.name)
    try:
        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                result = subprocess.run(
                    [_PDS_CLIENT, "-d", f"@{tmp}", endpoint],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return json.loads(result.stdout)
            except subprocess.CalledProcessError as e:
                # Distinguish transient connection errors (in stderr) from hard API errors
                is_connection_err = any(
                    marker in e.stderr
                    for marker in ("ConnectionError", "RemoteDisconnected", "Connection aborted")
                )
                if not is_connection_err:
                    raise
                last_err = e
                delay = _RETRY_BACKOFF_BASE ** (attempt + 1)
                print_warning(f"Connection error on attempt {attempt + 1}/{_MAX_RETRIES}, retrying in {delay}s...")
                time.sleep(delay)
        raise RuntimeError(f"All {_MAX_RETRIES} retries exhausted for {endpoint}") from last_err
    finally:
        tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def _checkpoint_key(index: str, namespace: str) -> str:
    return f"{index}|{namespace}"


def load_checkpoint(path: Path) -> dict[str, Any]:
    """Load checkpoint from disk. Returns empty structure if file does not exist or is corrupt."""
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError:
            print_warning(f"Corrupt checkpoint file at {path} — discarding. Use --reset to start fresh.")
    return {"sentinels": [], "results": {}}


def save_checkpoint(path: Path, data: dict[str, Any]) -> None:
    """Atomically write checkpoint to disk."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def fetch_all_sentinels() -> list[dict[str, Any]]:
    """Query all LDD_Info sentinels across every node's -dd index using search_after pagination."""
    base_query: dict[str, Any] = {
        "size": _SENTINEL_PAGE_SIZE,
        "_source": ["attr_ns", "attr_name", "date"],
        "query": {"term": {"class_name": "LDD_Info"}},
        "sort": [{"_id": "asc"}],
    }

    all_hits: list[dict[str, Any]] = []
    query = base_query

    while True:
        response = run_query(query, "/*-registry-dd/_search")
        hits = response.get("hits", {}).get("hits", [])
        all_hits.extend(hits)

        if len(hits) < _SENTINEL_PAGE_SIZE:
            break

        last_sort = hits[-1].get("sort")
        if not last_sort:
            break

        query = {**base_query, "search_after": last_sort}

    return all_hits


def count_field_docs(index: str, namespace: str) -> int:
    """Count non-sentinel field documents for a given namespace in a -dd index.

    Returns:
        The document count, or raises ValueError if the response is malformed.
    """
    query = {
        "query": {
            "bool": {
                "must": {"term": {"attr_ns": namespace}},
                "must_not": {"term": {"class_name": "LDD_Info"}},
            }
        }
    }
    response = run_query(query, f"/{index}/_count")
    if "count" not in response:
        raise ValueError(f"Malformed /_count response for [{index}] ns={namespace}: {response}")
    return response["count"]


def detect_stale_sentinels(
    hits: list[dict[str, Any]],
    checkpoint: dict[str, Any],
    checkpoint_path: Path,
) -> list[dict[str, Any]]:
    """Check each sentinel for field docs, resuming from checkpoint. Returns all stale records."""
    # setdefault ensures the key exists in checkpoint so save_checkpoint always captures mutations.
    results: dict[str, Any] = checkpoint.setdefault("results", {})
    total = len(hits)

    for i, hit in enumerate(hits, 1):
        index = hit["_index"]
        source = hit.get("_source", {})
        ns = source.get("attr_ns", "")
        filename = source.get("attr_name", "")
        date = source.get("date", "unknown")

        if not ns:
            print_warning(f"Sentinel in {index} has no attr_ns — skipping")
            continue

        key = _checkpoint_key(index, ns)
        if key in results:
            status = "STALE (cached)" if results[key]["stale"] else "OK (cached)"
            print_info(f"  [{i}/{total}] {index}  ns={ns}  → {status}")
            continue

        print_info(f"  [{i}/{total}] Checking {index}  ns={ns}  file={filename} ...")
        count = count_field_docs(index, ns)
        is_stale = count == 0
        results[key] = {
            "index": index,
            "namespace": ns,
            "filename": filename,
            "date": date,
            "stale": is_stale,
            "field_count": count,
        }

        if is_stale:
            print_warning("    STALE — 0 field docs found")
        else:
            print_info(f"    OK — {count} field doc(s) found")

        save_checkpoint(checkpoint_path, checkpoint)

    return [v for v in results.values() if v.get("stale")]


def print_status_report(checkpoint: dict[str, Any]) -> None:
    """Print a full status report from checkpoint results."""
    results = checkpoint.get("results", {})
    sentinels = checkpoint.get("sentinels", [])
    checked = len(results)
    total = len(sentinels)
    stale = [v for v in results.values() if v.get("stale")]
    ok_count = sum(1 for v in results.values() if not v.get("stale"))

    print_section(f"Status Report — {checked}/{total} checked, {len(stale)} stale, {ok_count} OK")

    if checked < total:
        print_warning(f"  {total - checked} sentinel(s) not yet checked (run again to continue)")

    if not stale:
        print_info("No stale sentinels detected.")
        return

    print(f"\n{Colors.BOLD}Stale sentinels:{Colors.NC}")
    for s in stale:
        print(f"\n  Index:     {s['index']}")
        print(f"  Namespace: {s['namespace']}")
        print(f"  LDD File:  {s['filename']}")
        print(f"  Date:      {s['date']}")
        print()
        print(f"  OpenSearch Dev Tools delete query:")
        print(f"    POST {s['index']}/_delete_by_query")
        delete_body = json.dumps({"query": {"term": {"attr_ns": s["namespace"]}}}, indent=4)
        for line in delete_body.splitlines():
            print(f"    {line}")
        print()


def confirm_deletion(stale: list[dict[str, Any]]) -> bool:
    """Prompt the user to confirm deletion. Returns True only if they type 'yes'."""
    print_section("Deletion Confirmation Required")
    print(f"{Colors.RED}You are about to DELETE all -dd documents for the following stale namespaces:{Colors.NC}\n")
    for s in stale:
        print(f"  [{s['index']}]  ns={s['namespace']}  file={s['filename']}")
    print()
    print(f"{Colors.YELLOW}This action cannot be undone without re-running harvest.{Colors.NC}")
    print()
    answer = input("Type 'yes' to confirm deletion (anything else cancels): ").strip()
    return answer == "yes"


def delete_stale_sentinel(s: dict[str, Any]) -> bool:
    """Delete all -dd documents for a given namespace in an index. Returns True on success."""
    query = {"query": {"term": {"attr_ns": s["namespace"]}}}
    try:
        response = run_query(query, f"/{s['index']}/_delete_by_query")
        deleted = response.get("deleted", 0)
        failures = response.get("failures", [])
        if failures:
            print_error(f"  Partial failure deleting [{s['index']}] ns={s['namespace']}: {failures}")
            return False
        print_info(f"  Deleted {deleted} document(s) from [{s['index']}] ns={s['namespace']}")
        return True
    except (subprocess.CalledProcessError, RuntimeError) as e:
        msg = e.stderr if isinstance(e, subprocess.CalledProcessError) else str(e)
        print_error(f"  Failed to delete [{s['index']}] ns={s['namespace']}: {msg}")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect (and optionally delete) stale LDD_Info sentinel records across all node registry -dd indexes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect stale sentinels, resuming from checkpoint if one exists (default, read-only)
  %(prog)s

  # Show status report from an existing checkpoint without making any new queries
  %(prog)s --report

  # Discard any saved checkpoint and start fresh
  %(prog)s --reset

  # Detect and interactively delete stale sentinels (requires confirmation)
  %(prog)s --delete
        """,
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        default=False,
        help=(
            "After detection, prompt for confirmation and delete stale sentinel documents. "
            "Deletion requires typing 'yes' at the prompt. "
            "Without this flag the script is read-only."
        ),
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        default=False,
        help="Discard any saved checkpoint and start detection from scratch.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        default=False,
        help="Print the status report from the existing checkpoint without running new queries.",
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="Path to the checkpoint file (default: <script_dir>/stale_ldd_checkpoint.json).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    script_dir = Path(__file__).parent.resolve()
    repo_dir = script_dir.parent
    checkpoint_path = Path(args.checkpoint) if args.checkpoint else script_dir / "stale_ldd_checkpoint.json"

    env_file_home = Path.home() / ".pds" / ".registry-client"
    env_file_repo = repo_dir / ".env"

    if env_file_home.exists():
        print_info(f"Loading environment variables from {env_file_home}")
        load_env_file(env_file_home)
    elif env_file_repo.exists():
        print_info(f"Loading environment variables from {env_file_repo}")
        load_env_file(env_file_repo)
    else:
        print_warning(f"No .env file found at {env_file_home} or {env_file_repo}")
        print_info("Assuming environment variables are already set...")

    # --report: just print existing checkpoint, no network calls
    if args.report:
        if not checkpoint_path.exists():
            print_warning(f"No checkpoint found at {checkpoint_path}")
            return 0
        print_info(f"Loading checkpoint from {checkpoint_path}")
        checkpoint = load_checkpoint(checkpoint_path)
        print_status_report(checkpoint)
        return 0

    missing_vars = check_required_vars()
    if missing_vars:
        print_error("Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print_error(f"Please set these variables in {env_file_home} or {env_file_repo}")
        return 1

    try:
        subprocess.run([_PDS_CLIENT, "--help"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error(f"pds-registry-client not found at {_PDS_CLIENT}")
        print_error("Please install it: pip install pds-registry-client")
        return 1

    # --reset: wipe checkpoint
    if args.reset:
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            print_info(f"Checkpoint reset: {checkpoint_path}")
        else:
            print_info("No existing checkpoint to reset.")

    # Load or initialise checkpoint
    checkpoint = load_checkpoint(checkpoint_path)

    # Step 1: fetch sentinels (or reuse from checkpoint)
    print_section("Step 1: Fetching LDD_Info sentinels across all -dd indexes")
    if "sentinels" in checkpoint:
        hits = checkpoint["sentinels"]
        print_info(f"Resuming from checkpoint — {len(hits)} sentinel(s) already fetched")
    else:
        try:
            hits = fetch_all_sentinels()
        except (subprocess.CalledProcessError, RuntimeError) as e:
            stderr = getattr(e, "stderr", str(e))
            print_error(f"Failed to query sentinels: {stderr}")
            return 1
        checkpoint["sentinels"] = hits
        save_checkpoint(checkpoint_path, checkpoint)
        print_info(f"Found {len(hits)} total LDD_Info sentinel(s) — checkpoint saved to {checkpoint_path}")

    if not hits:
        print_info("Nothing to do.")
        return 0

    already_checked = len(checkpoint.get("results", {}))
    remaining = len(hits) - already_checked
    if already_checked:
        print_info(f"Checkpoint: {already_checked} already checked, {remaining} remaining")

    # Step 2: check each sentinel for stale status
    print_section("Step 2: Checking each sentinel for field documents")
    try:
        stale = detect_stale_sentinels(hits, checkpoint, checkpoint_path)
    except (subprocess.CalledProcessError, RuntimeError, ValueError) as e:
        msg = e.stderr if isinstance(e, subprocess.CalledProcessError) else str(e)
        print_error(f"Failed during field-document count: {msg}")
        print_warning(f"Progress saved to {checkpoint_path} — re-run to continue from where it stopped")
        return 1

    # Step 3: report
    print_status_report(checkpoint)

    if not stale:
        return 0

    if not args.delete:
        print_info("Run with --delete to remove stale sentinels (confirmation required).")
        return 0

    # Step 4: confirm and delete
    if not confirm_deletion(stale):
        print_info("Deletion cancelled.")
        return 0

    print_section("Step 4: Deleting stale sentinel documents")
    errors = 0
    for s in stale:
        if not delete_stale_sentinel(s):
            errors += 1

    if errors:
        print_error(f"{errors} deletion(s) failed — review output above.")
        return 1

    print_info("All stale sentinels deleted. Re-run harvest to reload the affected namespaces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
