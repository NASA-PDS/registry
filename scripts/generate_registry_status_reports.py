#!/usr/bin/env python3
"""
Generate CSV status reports for missing and staged products in the PDS Registry.

This script queries OpenSearch using pds-registry-client and generates CSV reports
for missing and staged bundles and collections per node.

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
from typing import Any


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
    cmd = ["pds-registry-client", "-d", f"@{query_file}", endpoint]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def write_csv(data: dict[str, Any], output_file: Path, include_harvest_date: bool = False) -> int:
    """Write query results to CSV file."""
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        count = 0
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
                writer.writerow([node, lidvid, product_class, harvest_date])
            else:
                writer.writerow([node, lidvid, product_class])
            count += 1
        return count


def generate_metrics_from_csvs(csv_files: dict[str, Path]) -> str:
    """Generate metrics summary markdown from CSV files."""
    # Count by node for each report type
    missing_bundles_by_node = defaultdict(int)
    missing_collections_by_node = defaultdict(int)
    staged_bundles_by_node = defaultdict(int)
    staged_collections_by_node = defaultdict(int)

    # Read missing bundles
    if csv_files["missing_bundles"].exists():
        with open(csv_files["missing_bundles"], "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:  # Skip empty rows
                    node = row[0]
                    missing_bundles_by_node[node] += 1

    # Read missing collections
    if csv_files["missing_collections"].exists():
        with open(csv_files["missing_collections"], "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    node = row[0]
                    missing_collections_by_node[node] += 1

    # Read staged bundles
    if csv_files["staged_bundles"].exists():
        with open(csv_files["staged_bundles"], "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    node = row[0]
                    staged_bundles_by_node[node] += 1

    # Read staged collections
    if csv_files["staged_collections"].exists():
        with open(csv_files["staged_collections"], "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    node = row[0]
                    staged_collections_by_node[node] += 1

    # Get all unique nodes
    all_nodes = set()
    all_nodes.update(missing_bundles_by_node.keys())
    all_nodes.update(missing_collections_by_node.keys())
    all_nodes.update(staged_bundles_by_node.keys())
    all_nodes.update(staged_collections_by_node.keys())
    all_nodes = sorted(all_nodes)

    # Generate timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build markdown tables
    markdown = f"*Last updated: {timestamp}*\n\n"
    markdown += "### Missing Products by Node\n\n"
    markdown += "| Node | Bundles | Collections |\n"
    markdown += "|------|---------|-------------|\n"

    missing_bundles_total = 0
    missing_collections_total = 0
    for node in all_nodes:
        bundles = missing_bundles_by_node.get(node, 0)
        collections = missing_collections_by_node.get(node, 0)
        if bundles > 0 or collections > 0:
            markdown += f"| {node} | {bundles} | {collections} |\n"
            missing_bundles_total += bundles
            missing_collections_total += collections

    markdown += f"| **Total** | **{missing_bundles_total}** | **{missing_collections_total}** |\n\n"

    markdown += "### Staged Products by Node\n\n"
    markdown += "| Node | Bundles | Collections |\n"
    markdown += "|------|---------|-------------|\n"

    staged_bundles_total = 0
    staged_collections_total = 0
    for node in all_nodes:
        bundles = staged_bundles_by_node.get(node, 0)
        collections = staged_collections_by_node.get(node, 0)
        if bundles > 0 or collections > 0:
            markdown += f"| {node} | {bundles} | {collections} |\n"
            staged_bundles_total += bundles
            staged_collections_total += collections

    markdown += f"| **Total** | **{staged_bundles_total}** | **{staged_collections_total}** |\n"

    return markdown


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
            ["pds-registry-client", "--help"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("pds-registry-client command not found")
        print_error("Please install pds-registry-client: pip install pds-registry-client")
        return 1

    # Define paths (relative to repository root, not script directory)
    conf_dir = repo_dir / "conf" / "status"
    output_dir = repo_dir / "docs" / "status"

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define queries to run: (query_file, endpoint, output_file, include_harvest_date, description)
    queries = [
        (
            conf_dir / "missing_bundles_per_node.json",
            "/en-legacy-registry/_search",
            output_dir / "missing_bundles_in_registry.csv",
            False,
            "missing bundles",
        ),
        (
            conf_dir / "missing_collections_per_node.json",
            "/en-legacy-registry/_search",
            output_dir / "missing_collections_in_registry.csv",
            False,
            "missing collections",
        ),
        (
            conf_dir / "staged_bundles_per_node.json",
            "/*-registry/_search",
            output_dir / "staged_bundles_in_registry.csv",
            True,
            "staged bundles",
        ),
        (
            conf_dir / "staged_collections_per_node.json",
            "/*-registry/_search",
            output_dir / "staged_collections_in_registry.csv",
            True,
            "staged collections",
        ),
    ]

    # Check if all query files exist
    for query_file, _, _, _, description in queries:
        if not query_file.exists():
            print_error(f"Query file not found: {query_file}")
            return 1

    # Run all queries
    output_files = []
    for query_file, endpoint, output_file, include_harvest_date, description in queries:
        try:
            print_info(f"Querying for {description}...")
            data = run_query(query_file, endpoint)
            count = write_csv(data, output_file, include_harvest_date)
            print_info(f"Successfully generated {output_file} ({count} records)")
            output_files.append(output_file)
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to generate {description} report: {e.stderr}")
            return 1
        except Exception as e:
            print_error(f"Failed to generate {description} report: {e}")
            return 1

    print_info("\nReport generation complete!")
    print_info("Output files:")
    for output_file in output_files:
        print(f"  - {output_file}")

    # Generate and update metrics in README
    print_info("\nUpdating metrics in README...")
    csv_files = {
        "missing_bundles": output_dir / "missing_bundles_in_registry.csv",
        "missing_collections": output_dir / "missing_collections_in_registry.csv",
        "staged_bundles": output_dir / "staged_bundles_in_registry.csv",
        "staged_collections": output_dir / "staged_collections_in_registry.csv",
    }
    readme_path = output_dir / "README.md"

    try:
        metrics_markdown = generate_metrics_from_csvs(csv_files)
        update_readme_metrics(readme_path, metrics_markdown)
        print_info(f"Successfully updated metrics in {readme_path}")
        # Add README to list of files to commit
        output_files.append(readme_path)
    except Exception as e:
        print_error(f"Failed to update README metrics: {e}")
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
