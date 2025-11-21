#!/usr/bin/env python3
"""
Generate CSV reports for missing bundles and collections in the registry.

This script queries OpenSearch using pds-registry-client and generates CSV reports
for missing bundles and collections per node.

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
import subprocess
import sys
from datetime import datetime
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


def write_csv(data: dict[str, Any], output_file: Path) -> int:
    """Write query results to CSV file."""
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        count = 0
        for hit in data.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            node = source.get("node", "")
            lidvid = source.get("lidvid", "")
            product_class = source.get("product_class", [])
            # Join product_class if it's a list
            if isinstance(product_class, list):
                product_class = ", ".join(product_class)
            writer.writerow([node, lidvid, product_class])
            count += 1
        return count


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
        description="Generate CSV reports for missing bundles and collections in the PDS Registry",
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

    # Define paths
    conf_dir = script_dir / "conf"
    output_dir = script_dir / "docs" / "status"
    bundles_query = conf_dir / "missing_bundles_per_node.json"
    collections_query = conf_dir / "missing_collections_per_node.json"
    bundles_output = output_dir / "missing_bundles_in_registry.csv"
    collections_output = output_dir / "missing_collections_in_registry.csv"

    # Check if query files exist
    if not bundles_query.exists():
        print_error(f"Query file not found: {bundles_query}")
        return 1

    if not collections_query.exists():
        print_error(f"Query file not found: {collections_query}")
        return 1

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Query for missing bundles
    try:
        print_info("Querying for missing bundles...")
        bundles_data = run_query(bundles_query, "/en-legacy-registry/_search")
        bundle_count = write_csv(bundles_data, bundles_output)
        print_info(f"Successfully generated {bundles_output} ({bundle_count} records)")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to generate missing bundles report: {e.stderr}")
        return 1
    except Exception as e:
        print_error(f"Failed to generate missing bundles report: {e}")
        return 1

    # Query for missing collections
    try:
        print_info("Querying for missing collections...")
        collections_data = run_query(collections_query, "/en-legacy-registry/_search")
        collection_count = write_csv(collections_data, collections_output)
        print_info(f"Successfully generated {collections_output} ({collection_count} records)")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to generate missing collections report: {e.stderr}")
        return 1
    except Exception as e:
        print_error(f"Failed to generate missing collections report: {e}")
        return 1

    print_info("Report generation complete!")
    print_info("Output files:")
    print(f"  - {bundles_output}")
    print(f"  - {collections_output}")

    # Commit and push changes if requested
    if args.commit:
        print_info("\nCommitting and pushing changes to GitHub...")
        output_files = [bundles_output, collections_output]
        if not commit_and_push_changes(output_files, repo_dir):
            print_warning("Failed to commit and push changes, but reports were generated successfully")
            return 1
    else:
        print_info("\nSkipping git commit (--no-commit flag specified)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
