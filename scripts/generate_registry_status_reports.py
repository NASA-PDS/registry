#!/usr/bin/env python3
"""
Generate CSV status reports for missing and staged products in the PDS Registry.

This script queries OpenSearch using pds-registry-client and generates CSV reports
for missing and staged bundles and collections per node.

For missing products, three CSVs are produced per product type:
  - overall   (all versions)
  - latest    (highest version per LID)
  - superseded (all older versions per LID)

Environment variables required:
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
import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from datetime import timezone
from pathlib import Path
from shutil import which
from typing import Any

# Resolve pds-registry-client using shutil.which, preferring the directory
# containing the running Python executable (to pick up the current venv),
# but also searching the existing PATH.
_PDS_CLIENT = which(
    "pds-registry-client",
    path=os.pathsep.join(
        [
            str(Path(sys.executable).parent),
            os.environ.get("PATH", ""),
        ]
    ),
)

if _PDS_CLIENT is None:
    raise RuntimeError(
        "Unable to locate 'pds-registry-client' executable. Ensure it is "
        "installed and available on PATH or in the same virtual environment "
        "as this script."
    )
# Color codes for terminal output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    NC = "\033[0m"  # No Color


def print_info(message: str) -> None:
    """Print an info message in green."""
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def print_error(message: str) -> None:
    """Print an error message in red."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def load_env_file(env_file: Path) -> None:
    """Load environment variables from a .env file."""
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Remove 'export ' prefix if present (bash-style)
            if line.startswith("export "):
                line = line[7:]  # Remove 'export '
            # Parse key=value pairs
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                # Remove quotes if present
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
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    return missing_vars


def run_query(query_file: Path, endpoint: str) -> dict[str, Any]:
    """Run a query using pds-registry-client."""
    cmd = [_PDS_CLIENT, "-d", f"@{query_file}", endpoint]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def extract_rows(data: dict[str, Any], include_harvest_date: bool = False) -> list[tuple]:
    """Extract result rows from an OpenSearch query response."""
    rows = []
    for hit in data.get("hits", {}).get("hits", []):
        source = hit.get("_source", {})

        # Try both field names for node (missing queries use "node", staged queries use "ops:Harvest_Info/ops:node_name")
        node = source.get("node") or source.get("ops:Harvest_Info/ops:node_name")
        # Handle node as a list (staged queries) or string (missing queries)
        if isinstance(node, list):
            node = node[0] if node else ""
        elif node is None:
            node = ""

        lidvid = source.get("lidvid", "")

        product_class = source.get("product_class", [])
        # Handle product_class as a list or string
        if isinstance(product_class, list):
            product_class = ", ".join(product_class) if product_class else ""

        if include_harvest_date:
            harvest_date = source.get("ops:Harvest_Info/ops:harvest_date_time", "")
            # Handle harvest_date as a list or string
            if isinstance(harvest_date, list):
                harvest_date = harvest_date[0] if harvest_date else ""
            rows.append((node, lidvid, product_class, harvest_date))
        else:
            rows.append((node, lidvid, product_class))

    return rows


def write_rows_to_csv(rows: list[tuple], output_file: Path) -> int:
    """Write rows to a CSV file. Returns the number of rows written."""
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in rows:
            writer.writerow(row)
    return len(rows)


def split_by_version(rows: list[tuple]) -> tuple[list[tuple], list[tuple]]:
    """Split rows into latest and superseded versions grouped by LID.

    Expects lidvid as the second element (index 1) of each row, in the form
    ``urn:nasa:pds:<lid>::<major>.<minor>``.  Version comparison is numeric so
    that e.g. ``3.9 < 3.13``.

    Returns:
        (latest_rows, superseded_rows) where latest_rows contains only the
        highest-versioned row per LID and superseded_rows contains all others.
    """
    by_lid: dict[str, list[tuple[tuple[int, ...], tuple]]] = defaultdict(list)

    for row in rows:
        lidvid = row[1]
        if "::" in lidvid:
            lid, ver_str = lidvid.rsplit("::", 1)
        else:
            lid, ver_str = lidvid, "0"

        try:
            ver_key: tuple[int, ...] = tuple(int(x) for x in ver_str.split("."))
        except ValueError:
            ver_key = (0,)

        by_lid[lid].append((ver_key, row))

    latest_rows: list[tuple] = []
    superseded_rows: list[tuple] = []

    for version_rows in by_lid.values():
        sorted_rows = sorted(version_rows, key=lambda x: x[0], reverse=True)
        latest_rows.append(sorted_rows[0][1])
        superseded_rows.extend(r for _, r in sorted_rows[1:])

    return latest_rows, superseded_rows


def _count_by_node(csv_path: Path) -> dict[str, int]:
    """Return a node→count mapping from a CSV file (node is the first column)."""
    counts: dict[str, int] = defaultdict(int)
    if csv_path.exists():
        with open(csv_path, "r") as f:
            for row in csv.reader(f):
                if row:
                    counts[row[0]] += 1
    return counts


def _load_all_counts(csv_files: dict[str, Path]) -> dict[str, dict[str, int]]:
    """Load node→count mappings for all CSV files at once, reading each file only once."""
    return {key: _count_by_node(path) for key, path in csv_files.items()}


def generate_metrics_from_csvs(counts: dict[str, dict[str, int]]) -> str:
    """Generate metrics summary markdown from pre-computed node→count mappings."""
    mb = counts["missing_bundles"]
    mb_latest = counts["missing_bundles_latest"]
    mb_superseded = counts["missing_bundles_superseded"]
    mc = counts["missing_collections"]
    mc_latest = counts["missing_collections_latest"]
    mc_superseded = counts["missing_collections_superseded"]
    sb = counts["staged_bundles"]
    sc = counts["staged_collections"]

    all_nodes = sorted(
        set(mb) | set(mc) | set(sb) | set(sc)
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    markdown = f"*Last updated: {timestamp}*\n\n"

    # --- Missing Products table (expanded with latest/superseded columns) ---
    markdown += "### Missing Products by Node\n\n"
    markdown += (
        "| Node "
        "| Latest Bundles | Superseded Bundles | Total Bundles "
        "| Latest Collections | Superseded Collections | Total Collections |\n"
    )
    markdown += (
        "|------"
        "|---------------:|-------------------:|--------------:"
        "|-------------------:|-----------------------:|------------------:|\n"
    )

    mb_t = mb_l_t = mb_s_t = mc_t = mc_l_t = mc_s_t = 0
    for node in all_nodes:
        b_total = mb.get(node, 0)
        b_latest = mb_latest.get(node, 0)
        b_super = mb_superseded.get(node, 0)
        c_total = mc.get(node, 0)
        c_latest = mc_latest.get(node, 0)
        c_super = mc_superseded.get(node, 0)
        if b_total > 0 or c_total > 0:
            markdown += (
                f"| {node} "
                f"| {b_latest} | {b_super} | {b_total} "
                f"| {c_latest} | {c_super} | {c_total} |\n"
            )
            mb_t += b_total
            mb_l_t += b_latest
            mb_s_t += b_super
            mc_t += c_total
            mc_l_t += c_latest
            mc_s_t += c_super

    markdown += (
        f"| **Total** "
        f"| **{mb_l_t}** | **{mb_s_t}** | **{mb_t}** "
        f"| **{mc_l_t}** | **{mc_s_t}** | **{mc_t}** |\n\n"
    )

    # --- Staged Products table (unchanged) ---
    markdown += "### Staged Products by Node\n\n"
    markdown += "| Node | Bundles | Collections |\n"
    markdown += "|------|--------:|------------:|\n"

    sb_t = sc_t = 0
    for node in all_nodes:
        bundles = sb.get(node, 0)
        collections = sc.get(node, 0)
        if bundles > 0 or collections > 0:
            markdown += f"| {node} | {bundles} | {collections} |\n"
            sb_t += bundles
            sc_t += collections

    markdown += f"| **Total** | **{sb_t}** | **{sc_t}** |\n"

    return markdown


HISTORY_HEADER = (
    "date,"
    "missing_bundles_total,missing_bundles_latest,missing_bundles_superseded,"
    "missing_collections_total,missing_collections_latest,missing_collections_superseded,"
    "staged_bundles_total,staged_collections_total"
)


def append_history_row(history_file: Path, counts: dict[str, dict[str, int]]) -> None:
    """Append one dated row of aggregate counts to the history CSV.

    If the file does not yet exist, a header row is written first.  The file is
    never truncated — only appended to — so historical data accumulates over time.
    """
    def total(key: str) -> int:
        return sum(counts[key].values())

    row = ",".join([
        datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        str(total("missing_bundles")),
        str(total("missing_bundles_latest")),
        str(total("missing_bundles_superseded")),
        str(total("missing_collections")),
        str(total("missing_collections_latest")),
        str(total("missing_collections_superseded")),
        str(total("staged_bundles")),
        str(total("staged_collections")),
    ])

    write_header = not history_file.exists()
    with open(history_file, "a", newline="") as f:
        if write_header:
            f.write(HISTORY_HEADER + "\n")
        f.write(row + "\n")


def update_readme_metrics(readme_path: Path, metrics_markdown: str) -> None:
    """Update the metrics section in the README file."""
    with open(readme_path, "r") as f:
        content = f.read()

    # Replace content between METRICS_START and METRICS_END
    pattern = r"(<!-- METRICS_START -->).*?(<!-- METRICS_END -->)"
    replacement = f"\\1\n{metrics_markdown}\n\\2"
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(readme_path, "w") as f:
        f.write(new_content)


def commit_and_push_changes(output_files: list[Path], repo_dir: Path) -> bool:
    """Commit and push the generated CSV files to GitHub."""
    try:
        # Check if there are any changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        if not result.stdout.strip():
            print_info("No changes to commit")
            return True

        # Add the CSV files
        print_info("Adding CSV files to git...")
        for file in output_files:
            subprocess.run(
                ["git", "add", str(file)],
                cwd=repo_dir,
                check=True,
            )

        # Create commit message with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Update missing products reports - {timestamp}"

        print_info(f"Creating commit: {commit_message}")
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_dir,
            check=True,
        )

        # Push to remote
        print_info("Pushing changes to GitHub...")
        subprocess.run(
            ["git", "push"],
            cwd=repo_dir,
            check=True,
        )

        print_info("Successfully committed and pushed changes to GitHub")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Git operation failed: {e}")
        return False
    except Exception as e:
        print_error(f"Failed to commit and push changes: {e}")
        return False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate CSV status reports for missing and staged products in the PDS Registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate reports only (no git commit)
  %(prog)s --no-commit

  # Generate reports and commit/push to GitHub (default)
  %(prog)s

  # Same as above, explicit flag
  %(prog)s --commit
        """,
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        default=True,
        dest="commit",
        help="Commit and push changes to GitHub (default)",
    )
    parser.add_argument(
        "--no-commit",
        action="store_false",
        dest="commit",
        help="Do not commit or push changes to GitHub",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()

    # Get script directory
    script_dir = Path(__file__).parent.resolve()
    repo_dir = script_dir.parent

    # Define possible .env file locations
    env_file_home = Path.home() / ".pds" / ".registry-client"
    env_file_repo = repo_dir / ".env"

    # Load environment variables
    if env_file_home.exists():
        print_info(f"Loading environment variables from {env_file_home}")
        load_env_file(env_file_home)
    elif env_file_repo.exists():
        print_info(f"Loading environment variables from {env_file_repo}")
        load_env_file(env_file_repo)
    else:
        print_warning(f"No .env file found at {env_file_home} or {env_file_repo}")
        print_info("Assuming environment variables are already set...")

    # Verify required environment variables
    missing_vars = check_required_vars()
    if missing_vars:
        print_error("Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print_error(f"Please set these variables in {env_file_home} or {env_file_repo}")
        return 1

    # Check if pds-registry-client is available
    try:
        subprocess.run(
            [_PDS_CLIENT, "--help"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error(f"pds-registry-client not found at {_PDS_CLIENT}")
        print_error("Please install pds-registry-client: pip install pds-registry-client")
        return 1

    # Define paths (relative to repository root, not script directory)
    conf_dir = repo_dir / "conf" / "status"
    output_dir = repo_dir / "docs" / "status"

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define queries to run:
    #   (query_file, endpoint, output_file, include_harvest_date, description, split_versions)
    #
    # split_versions=True generates additional *_latest_* and *_superseded_* CSVs
    # by grouping LIDVIDs by LID and keeping only the highest version per LID.
    queries = [
        (
            conf_dir / "missing_bundles_per_node.json",
            "/en-legacy-registry/_search",
            output_dir / "missing_bundles_in_registry.csv",
            False,
            "missing bundles",
            True,
        ),
        (
            conf_dir / "missing_collections_per_node.json",
            "/en-legacy-registry/_search",
            output_dir / "missing_collections_in_registry.csv",
            False,
            "missing collections",
            True,
        ),
        (
            conf_dir / "staged_bundles_per_node.json",
            "/*-registry/_search",
            output_dir / "staged_bundles_in_registry.csv",
            True,
            "staged bundles",
            False,
        ),
        (
            conf_dir / "staged_collections_per_node.json",
            "/*-registry/_search",
            output_dir / "staged_collections_in_registry.csv",
            True,
            "staged collections",
            False,
        ),
    ]

    # Check if all query files exist
    for query_file, _, _, _, description, _ in queries:
        if not query_file.exists():
            print_error(f"Query file not found: {query_file}")
            return 1

    # Run all queries and write CSVs
    output_files: list[Path] = []
    for query_file, endpoint, output_file, include_harvest_date, description, split_versions in queries:
        try:
            print_info(f"Querying for {description}...")
            data = run_query(query_file, endpoint)
            rows = extract_rows(data, include_harvest_date)

            # Always write the overall CSV
            count = write_rows_to_csv(rows, output_file)
            print_info(f"  overall  → {output_file.name} ({count} records)")
            output_files.append(output_file)

            if split_versions:
                # Derive sibling paths: missing_bundles_in_registry.csv
                #   → missing_bundles_latest_in_registry.csv
                #   → missing_bundles_superseded_in_registry.csv
                stem = output_file.stem  # e.g. "missing_bundles_in_registry"
                suffix = output_file.suffix
                base = stem.replace("_in_registry", "")  # "missing_bundles"
                latest_file = output_dir / f"{base}_latest_in_registry{suffix}"
                superseded_file = output_dir / f"{base}_superseded_in_registry{suffix}"

                latest_rows, superseded_rows = split_by_version(rows)

                latest_count = write_rows_to_csv(latest_rows, latest_file)
                print_info(f"  latest   → {latest_file.name} ({latest_count} records)")
                output_files.append(latest_file)

                superseded_count = write_rows_to_csv(superseded_rows, superseded_file)
                print_info(f"  superseded → {superseded_file.name} ({superseded_count} records)")
                output_files.append(superseded_file)

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to generate {description} report: {e.stderr}")
            return 1
        except Exception as e:
            print_error(f"Failed to generate {description} report: {e}")
            return 1

    print_info("\nReport generation complete!")

    # Generate and update metrics in README
    print_info("Updating metrics in README...")
    csv_files = {
        "missing_bundles": output_dir / "missing_bundles_in_registry.csv",
        "missing_bundles_latest": output_dir / "missing_bundles_latest_in_registry.csv",
        "missing_bundles_superseded": output_dir / "missing_bundles_superseded_in_registry.csv",
        "missing_collections": output_dir / "missing_collections_in_registry.csv",
        "missing_collections_latest": output_dir / "missing_collections_latest_in_registry.csv",
        "missing_collections_superseded": output_dir / "missing_collections_superseded_in_registry.csv",
        "staged_bundles": output_dir / "staged_bundles_in_registry.csv",
        "staged_collections": output_dir / "staged_collections_in_registry.csv",
    }
    readme_path = output_dir / "README.md"

    # Load all node→count mappings once; reuse for both README metrics and history row.
    counts = _load_all_counts(csv_files)

    try:
        metrics_markdown = generate_metrics_from_csvs(counts)
        update_readme_metrics(readme_path, metrics_markdown)
        print_info(f"Successfully updated metrics in {readme_path}")
        output_files.append(readme_path)
    except Exception as e:
        print_error(f"Failed to update README metrics: {e}")
        return 1

    # Append a snapshot row to the history file for burndown tracking
    history_file = output_dir / "counts_history.csv"
    try:
        append_history_row(history_file, counts)
        print_info(f"Appended counts snapshot to {history_file}")
        output_files.append(history_file)
    except Exception as e:
        print_error(f"Failed to append history row: {e}")
        return 1

    # Commit and push changes if requested
    if args.commit:
        print_info("\nCommitting and pushing changes to GitHub...")
        if not commit_and_push_changes(output_files, repo_dir):
            print_warning("Failed to commit and push changes, but reports were generated successfully")
            return 1
    else:
        print_info("\nSkipping git commit (--no-commit flag specified)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
