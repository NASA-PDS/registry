#!/usr/bin/env python3
"""
Audit a PDS4 collection to diagnose product count discrepancies.

Compares four independent sources for member product counts:

  1. Label record count  — pds:Inventory.pds:records from the collection label
  2. Inventory file rows — downloads the inventory table and counts data rows
  3. API members count   — /products/{lidvid}/members hits total
  4. Registry count      — OpenSearch wildcard _count query via pds-registry-client

Pass --diff to follow up any discrepancy with a full LIDVID-level comparison
between the inventory file and the registry (the only two sources that support
complete enumeration — the API /members endpoint is capped at 10,000 items with
no pagination, so it cannot be fully diffed directly).

Setup:
    Install registry-client dependencies before running registry queries:

        pip install -r scripts/requirements.txt

    Source your registry credentials into the shell environment before running:

        source ~/.pds/registry-client-prod.env

Usage:
    python scripts/audit_collection_counts.py <collection_lidvid> [options]

Examples:
    # Count comparison only (no registry)
    python scripts/audit_collection_counts.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 --no-registry

    # Full audit including registry counts (credentials must be sourced first)
    source ~/.pds/registry-client-prod.env
    python scripts/audit_collection_counts.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0

    # Audit multiple collections — pass directly or via a file
    source ~/.pds/registry-client-prod.env
    python scripts/audit_collection_counts.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \\
        urn:nasa:pds:mars2020_mastcam-z_ops:data_raw::14.0

    python scripts/audit_collection_counts.py --from-file collections.txt

    # Full audit + LIDVID-level diff written to CSV files
    # summary.csv goes to audit_results/, diff CSVs to per-collection subdirs
    source ~/.pds/registry-client-prod.env
    python scripts/audit_collection_counts.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \\
        urn:nasa:pds:mars2020_mastcam-z_ops:data_raw::14.0 \\
        --diff --output-dir ./audit_results/

Options:
    --api-base URL        PDS Search API base URL
                          (default: https://pds.mcp.nasa.gov/api/search/1)
    --registry-index IDX  OpenSearch index pattern for the _count query
                          (default: /*-registry/_count)
    --wildcard PAT        Override the wildcard pattern for the registry query
                          (default: derived from collection LID as "<lid>:*")
    --timeout N           Per-request timeout in seconds (default: 30)
    --from-file FILE      Newline-separated file of collection LIDVIDs; combined
                          with any LIDVIDs given on the command line
    --no-registry         Skip the registry client query
    --env-file FILE       Load credentials from FILE in addition to the shell
                          environment (optional; shell-sourced vars take
                          precedence via os.environ.setdefault)
    --log-level LEVEL     Logging verbosity: debug, info, warn, warning
                          (default: info)
    --diff                After the count report, fetch all LIDVIDs from
                          inventory and registry and compute set differences
    --output-dir DIR      Write all output files to DIR: summary.csv at the
                          root, per-collection diff CSVs in subdirectories
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import sys
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING
from typing import NamedTuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

if TYPE_CHECKING:
    from opensearchpy import RequestsAWSV4SignerAuth

# Registry-client dependencies (opensearch-py, botocore, pds.aossrequestsigner) are
# optional: they are only imported when registry queries are actually requested.
# Install via: pip install -r scripts/requirements.txt

_DEFAULT_API_BASE = "https://pds.mcp.nasa.gov/api/search/1"
_DEFAULT_REGISTRY_INDEX = "/*-registry/_count"
_REGISTRY_PAGE_SIZE = 10000
_API_VISIBLE_ARCHIVE_STATUSES = ["archived", "certified"]
"""Archive-status values that the PDS Search API exposes to callers."""

_REGISTRY_ENV_VARS = (
    "REQUEST_SIGNER_AWS_REGION",
    "REQUEST_SIGNER_AWS_ACCOUNT",
    "REQUEST_SIGNER_CLIENT_ID",
    "REQUEST_SIGNER_IDENTITY_POOL_ID",
    "REQUEST_SIGNER_USER_POOL_ID",
    "REQUEST_SIGNER_COGNITO_USER",
    "REQUEST_SIGNER_COGNITO_PASSWORD",
    "REQUEST_SIGNER_AOSS_ENDPOINT",
)

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
}

logger = logging.getLogger(__name__)


class _ReportRow(NamedTuple):
    label: str
    value: int | None
    primary: bool


# ── terminal colours ──────────────────────────────────────────────────────────


class Color:
    """ANSI color codes and helpers for terminal output."""

    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @staticmethod
    def red(text: str) -> str:
        """Returns text wrapped in red ANSI color codes."""
        return f"{Color.RED}{text}{Color.RESET}"

    @staticmethod
    def yellow(text: str) -> str:
        """Returns text wrapped in yellow ANSI color codes."""
        return f"{Color.YELLOW}{text}{Color.RESET}"

    @staticmethod
    def green(text: str) -> str:
        """Returns text wrapped in green ANSI color codes."""
        return f"{Color.GREEN}{text}{Color.RESET}"

    @staticmethod
    def cyan(text: str) -> str:
        """Returns text wrapped in cyan ANSI color codes."""
        return f"{Color.CYAN}{text}{Color.RESET}"

    @staticmethod
    def bold(text: str) -> str:
        """Returns text wrapped in bold ANSI escape codes."""
        return f"{Color.BOLD}{text}{Color.RESET}"


# ── HTTP session (public API calls) ──────────────────────────────────────────


def make_session() -> requests.Session:
    """Build a requests Session with retry logic and standard headers.

    Timeout is not set at the session level; callers pass it per-request.

    Returns:
        A configured requests.Session ready for use.
    """
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
    session.headers["Accept"] = "application/json"
    session.headers["User-Agent"] = "pds-collection-auditor/1.0"
    return session


# ── env loading ───────────────────────────────────────────────────────────────


def load_env_file(path: Path) -> None:
    """Load environment variables from a .env / shell-export file.

    Args:
        path: Path to the env file. Lines starting with ``#`` and blank lines
            are ignored. An optional ``export `` prefix is stripped.
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

    Registry credentials are expected to be sourced into the shell environment
    before this script is invoked (e.g. ``source ~/.pds/registry-client-prod.env``).
    This function only supplements: it calls ``os.environ.setdefault`` so
    already-set variables are never overwritten.

    When ``env_file`` is provided it is loaded first; otherwise the function
    is a no-op (the caller is responsible for sourcing credentials).

    Args:
        env_file: Optional path to a supplemental .env file. When ``None``
            no file is read and no warning is emitted.
    """
    if env_file is None:
        return
    if env_file.exists():
        load_env_file(env_file)
        logger.debug("Supplemented credentials from %s", env_file)
    else:
        logger.warning("--env-file path does not exist: %s", env_file)


# ── registry auth ─────────────────────────────────────────────────────────────


def make_registry_auth() -> RequestsAWSV4SignerAuth | None:
    """Authenticate to AOSS via Cognito and return a signed auth object.

    Reads all required credentials from environment variables (loaded by
    ``load_credentials`` before this is called).

    Returns:
        A ``RequestsAWSV4SignerAuth`` instance ready for use in HTTP calls,
        or ``None`` if any required variable is missing or authentication fails.
    """
    try:
        import botocore.exceptions
        from opensearchpy import RequestsAWSV4SignerAuth
        from pds.aossrequestsigner.credentials import get_credentials_via_cognito_userpass_flow
    except ImportError as exc:
        logger.error(
            "Registry client packages not installed: %s. "
            "Run: pip install -r scripts/requirements.txt",
            exc,
        )
        return None

    missing = [v for v in _REGISTRY_ENV_VARS if not os.environ.get(v)]
    if missing:
        logger.error("Missing required environment variables: %s", missing)
        return None

    region = os.environ["REQUEST_SIGNER_AWS_REGION"]
    try:
        credentials = get_credentials_via_cognito_userpass_flow(
            region=region,
            account_id=os.environ["REQUEST_SIGNER_AWS_ACCOUNT"],
            client_id=os.environ["REQUEST_SIGNER_CLIENT_ID"],
            identity_pool_id=os.environ["REQUEST_SIGNER_IDENTITY_POOL_ID"],
            user_pool_id=os.environ["REQUEST_SIGNER_USER_POOL_ID"],
            username=os.environ["REQUEST_SIGNER_COGNITO_USER"],
            password=os.environ["REQUEST_SIGNER_COGNITO_PASSWORD"],
        )
    except botocore.exceptions.ClientError as exc:
        logger.error("Cognito authentication failed: %s", exc)
        return None

    return RequestsAWSV4SignerAuth(credentials, region, "aoss")


# ── registry queries ──────────────────────────────────────────────────────────


def run_registry_query(
    query: dict,
    index_path: str,
    auth: RequestsAWSV4SignerAuth,
    timeout: int,
) -> dict | None:
    """POST a signed OpenSearch query and return the parsed response.

    Args:
        query: OpenSearch DSL query body.
        index_path: Host-relative path, e.g. ``/*-registry/_count``.
        auth: Signed AWS auth object from ``make_registry_auth``.
        timeout: Per-request timeout in seconds.

    Returns:
        Parsed JSON response dict, or ``None`` on error.
    """
    endpoint = os.environ.get("REQUEST_SIGNER_AOSS_ENDPOINT")
    if not endpoint:
        logger.error("REQUEST_SIGNER_AOSS_ENDPOINT is not set")
        return None
    url = endpoint.rstrip("/") + urllib.parse.quote(index_path, safe="/")
    try:
        resp = requests.post(
            url=url,
            data=json.dumps(query),
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        logger.error("Registry query failed: %s", exc)
        return None


def _wildcard_query(pattern: str) -> dict:
    """Return a raw OpenSearch wildcard query body matching member LIDs.

    Matches on the ``lid`` field (not ``lidvid``) so the collection document
    itself is never included — a collection's ``lid`` has no trailing product
    segment and therefore cannot satisfy ``<collection_lid>:*``.
    No superseded or archive-status filtering is applied.

    Args:
        pattern: Wildcard expression matched against the ``lid`` field,
            e.g. ``urn:nasa:pds:mybundle:mydata:*``.

    Returns:
        OpenSearch DSL dict suitable for passing to ``run_registry_query``.
    """
    return {
        "query": {
            "wildcard": {
                "lid": {
                    "value": pattern,
                    "case_insensitive": True,
                }
            }
        }
    }


def _superseded_query(pattern: str) -> dict:
    """Return a query counting products that have been superseded.

    Matches member products by ``lid`` wildcard where
    ``ops:Provenance/ops:superseded_by`` is present, regardless of
    archive status.

    Args:
        pattern: Wildcard expression matched against the ``lid`` field.

    Returns:
        OpenSearch DSL dict suitable for passing to ``run_registry_query``.
    """
    return {
        "query": {
            "bool": {
                "must": [
                    {
                        "wildcard": {
                            "lid": {
                                "value": pattern,
                                "case_insensitive": True,
                            }
                        }
                    }
                ],
                "filter": [
                    {"exists": {"field": "ops:Provenance/ops:superseded_by"}}
                ],
            }
        }
    }


def _non_superseded_query(pattern: str) -> dict:
    """Return a query matching all non-superseded member products.

    Matches member products by ``lid`` wildcard where
    ``ops:Provenance/ops:superseded_by`` is absent. No archive-status filter
    is applied — this covers all non-superseded products regardless of whether
    they are currently visible through the API.

    Used for the registry side of the inventory diff: a superseded product is
    not expected to appear in the current inventory, so it should not be
    flagged as an anomaly.

    Args:
        pattern: Wildcard expression matched against the ``lid`` field.

    Returns:
        OpenSearch DSL dict suitable for passing to ``run_registry_query``.
    """
    return {
        "query": {
            "bool": {
                "must": [
                    {
                        "wildcard": {
                            "lid": {
                                "value": pattern,
                                "case_insensitive": True,
                            }
                        }
                    }
                ],
                "must_not": [
                    {"exists": {"field": "ops:Provenance/ops:superseded_by"}}
                ],
            }
        }
    }


def _non_archived_query(pattern: str) -> dict:
    """Return a query counting non-superseded products outside archived/certified.

    Matches member products by ``lid`` wildcard that are not superseded AND
    whose ``ops:Tracking_Meta/ops:archive_status`` is not in the API-visible
    set (``archived`` / ``certified``).  These products exist in the registry
    but are invisible to the API for a reason other than supersession.

    Args:
        pattern: Wildcard expression matched against the ``lid`` field.

    Returns:
        OpenSearch DSL dict suitable for passing to ``run_registry_query``.
    """
    return {
        "query": {
            "bool": {
                "must": [
                    {
                        "wildcard": {
                            "lid": {
                                "value": pattern,
                                "case_insensitive": True,
                            }
                        }
                    }
                ],
                "must_not": [
                    {"exists": {"field": "ops:Provenance/ops:superseded_by"}},
                    {
                        "terms": {
                            "ops:Tracking_Meta/ops:archive_status": _API_VISIBLE_ARCHIVE_STATUSES
                        }
                    },
                ],
            }
        }
    }


def _api_visible_query(pattern: str) -> dict:
    """Return a query that mirrors what the PDS Search API exposes.

    Matches member products by ``lid`` wildcard and additionally filters to
    products that are:

    - Not superseded (``ops:Provenance/ops:superseded_by`` field absent)
    - Have an ``ops:Tracking_Meta/ops:archive_status`` of ``archived`` or
      ``certified``

    Args:
        pattern: Wildcard expression matched against the ``lid`` field.

    Returns:
        OpenSearch DSL dict suitable for passing to ``run_registry_query``.
    """
    return {
        "query": {
            "bool": {
                "must": [
                    {
                        "wildcard": {
                            "lid": {
                                "value": pattern,
                                "case_insensitive": True,
                            }
                        }
                    }
                ],
                "must_not": [
                    {"exists": {"field": "ops:Provenance/ops:superseded_by"}}
                ],
                "filter": [
                    {
                        "terms": {
                            "ops:Tracking_Meta/ops:archive_status": _API_VISIBLE_ARCHIVE_STATUSES
                        }
                    }
                ],
            }
        }
    }


def get_registry_count(
    query: dict,
    registry_index: str,
    auth: RequestsAWSV4SignerAuth,
    timeout: int,
) -> int | None:
    """Return the document count for a pre-built query via the ``_count`` endpoint.

    Uses ``_count`` so no pagination is required and the result is not
    constrained by ``max_result_window``.

    Args:
        query: OpenSearch DSL query body (from ``_wildcard_query`` or
            ``_api_visible_query``).
        registry_index: Index path ending with ``_count``
            (e.g. ``/*-registry/_count``).
        auth: Signed AWS auth from ``make_registry_auth``.
        timeout: Per-request timeout in seconds.

    Returns:
        Total document count, or ``None`` on error.
    """
    data = run_registry_query(query, registry_index, auth, timeout)
    if data is None:
        return None

    count = data.get("count")
    if isinstance(count, int):
        return count

    logger.error("Unexpected _count response shape: %s", list(data.keys()))
    return None


# ── diff: full LIDVID enumeration ─────────────────────────────────────────────


def get_all_registry_lidvids(
    collection_lid: str,
    wildcard_pattern: str | None,
    registry_index: str,
    auth: RequestsAWSV4SignerAuth,
    timeout: int,
) -> set[str] | None:
    """Paginate through registry _search and return LIDVIDs of non-superseded products.

    Filters to non-superseded products only (``ops:Provenance/ops:superseded_by``
    absent) with no archive-status restriction. Superseded products are excluded
    because they are not expected to appear in the current collection inventory;
    including them would produce false positives in the "registry not in inventory"
    diff direction.

    The search index is derived from ``registry_index`` by replacing ``_count``
    with ``_search``.

    Args:
        collection_lid: Collection LID used to derive the default wildcard.
        wildcard_pattern: Explicit wildcard override (defaults to
            ``<collection_lid>:*``).
        registry_index: Index path used for the count query; ``_count`` is
            replaced with ``_search`` automatically.
        auth: Signed AWS auth from ``make_registry_auth``.
        timeout: Per-request timeout in seconds.

    Returns:
        Set of LIDVID strings for non-superseded products, or ``None`` if any
        page fails.
    """
    pattern = wildcard_pattern or f"{collection_lid}:*"
    search_index = registry_index.removesuffix("_count") + "_search"
    logger.info(
        "Fetching non-superseded registry LIDVIDs (index: %s, lid pattern: %s)",
        search_index,
        pattern,
    )

    base_query: dict = {
        "_source": ["lidvid"],
        "size": _REGISTRY_PAGE_SIZE,
        "sort": [{"_id": "asc"}],
        **_non_superseded_query(pattern),
    }

    lidvids: set[str] = set()
    query = base_query
    page = 0

    while True:
        page += 1
        logger.info("Registry page %d (collected %d so far) …", page, len(lidvids))
        data = run_registry_query(query, search_index, auth, timeout)
        if data is None:
            return None

        hits = data.get("hits", {}).get("hits", [])
        for hit in hits:
            lidvid = hit.get("_source", {}).get("lidvid")
            if lidvid:
                lidvids.add(lidvid)
            else:
                logger.debug("Hit missing lidvid in _source: %s", hit.get("_id"))

        if len(hits) < _REGISTRY_PAGE_SIZE:
            break

        last_sort = hits[-1].get("sort")
        if not last_sort:
            break

        query = {**base_query, "search_after": last_sort}

    return lidvids


# ── source 1: label record count ─────────────────────────────────────────────


def get_label_count(
    session: requests.Session,
    api_base: str,
    lidvid: str,
    timeout: int,
) -> tuple[int | None, str | None]:
    """Return the label's stated record count and the inventory file URL.

    Args:
        session: Shared HTTP session.
        api_base: PDS Search API base URL.
        lidvid: Collection LIDVID to look up.
        timeout: Per-request timeout in seconds.

    Returns:
        A ``(record_count, file_ref)`` tuple. Either element may be ``None``
        if the corresponding field is absent from the label.
    """
    encoded = urllib.parse.quote(lidvid, safe="")
    url = f"{api_base}/products/{encoded}"
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error("Failed to fetch collection product: %s", exc)
        return None, None

    # API returns properties at the top level of the response object.
    props = resp.json().get("properties", {})

    record_count: int | None = None
    raw = props.get("pds:Inventory.pds:records")
    if raw is not None:
        val = raw[0] if isinstance(raw, list) else raw
        try:
            record_count = int(val)
        except (TypeError, ValueError):
            logger.warning("Could not parse pds:Inventory.pds:records value: %r", val)

    file_ref: str | None = None
    raw = props.get("ops:Data_File_Info.ops:file_ref")
    if raw is not None:
        file_ref = raw[0] if isinstance(raw, list) else raw

    return record_count, file_ref


# ── source 2: inventory file ──────────────────────────────────────────────────


def count_inventory_rows(
    session: requests.Session,
    file_ref: str,
    timeout: int,
) -> int | None:
    """Download the inventory table and return the number of data rows.

    Args:
        session: Shared HTTP session.
        file_ref: URL of the PDS4 inventory CSV file.
        timeout: Per-request timeout in seconds.

    Returns:
        Number of data rows (header excluded), or ``None`` on error.
    """
    count, _ = _download_inventory(session, file_ref, timeout, collect_lidvids=False)
    return count


def fetch_inventory_lidvids(
    session: requests.Session,
    file_ref: str,
    timeout: int,
) -> tuple[int | None, set[str] | None]:
    """Download the inventory table and return the row count and LIDVID set.

    Args:
        session: Shared HTTP session.
        file_ref: URL of the PDS4 inventory CSV file.
        timeout: Per-request timeout in seconds.

    Returns:
        A ``(row_count, lidvid_set)`` tuple. ``row_count`` counts all data rows
        (including duplicates). ``lidvid_set`` contains unique LIDVIDs only.
        Both elements are ``None`` on error.
    """
    return _download_inventory(session, file_ref, timeout, collect_lidvids=True)


def _download_inventory(
    session: requests.Session,
    file_ref: str,
    timeout: int,
    collect_lidvids: bool,
) -> tuple[int | None, set[str] | None]:
    """Download and parse the inventory CSV; inner implementation for both callers.

    Args:
        session: Shared HTTP session.
        file_ref: URL of the PDS4 inventory CSV file.
        timeout: Per-request timeout in seconds.
        collect_lidvids: When ``True`` build and return the LIDVID set;
            when ``False`` return ``None`` for that element (saves memory).

    Returns:
        ``(row_count, lidvid_set_or_None)`` tuple, or ``(None, None)`` on error.
    """
    try:
        resp = session.get(file_ref, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error("Failed to download inventory file: %s", exc)
        return None, None

    resp.encoding = "utf-8"
    rows = [r for r in csv.reader(io.StringIO(resp.text)) if any(cell.strip() for cell in r)]
    if not rows:
        logger.error("Inventory file is empty: %s", file_ref)
        return None, None

    # PDS4 inventory data rows always begin with 'P' (primary) or 'S' (secondary).
    # Any other first-cell value is treated as a header and skipped.
    # Using Member_Status is more reliable than scanning for '::' because bare
    # LID references (no version suffix) are legal and would fool a '::' check.
    first_cell = rows[0][0].strip().upper() if rows[0] else ""
    has_header = first_cell not in ("P", "S")
    data_rows = rows[1:] if has_header else rows
    row_count = len(data_rows)

    if not collect_lidvids:
        return row_count, None

    # Column 1 is the LIDVID (or LID) reference.
    short = [r for r in data_rows if len(r) < 2]
    if short:
        logger.warning(
            "%d inventory row(s) have fewer than 2 columns and were skipped", len(short)
        )
    lidvids = {row[1].strip() for row in data_rows if len(row) >= 2}
    return row_count, lidvids


# ── source 3: API members count ───────────────────────────────────────────────


def get_api_members_count(
    session: requests.Session,
    api_base: str,
    lidvid: str,
    timeout: int,
) -> int | None:
    """Return the total member count from the /members endpoint.

    Note:
        The /members endpoint is capped at 10,000 items and accepts no
        pagination parameters, so only the summary total is reliable for
        large collections.

    Args:
        session: Shared HTTP session.
        api_base: PDS Search API base URL.
        lidvid: Collection LIDVID to query.
        timeout: Per-request timeout in seconds.

    Returns:
        Total member hit count, or ``None`` on error.
    """
    encoded = urllib.parse.quote(lidvid, safe="")
    # limit=1 minimises payload; the total lives in summary.hits.
    url = f"{api_base}/products/{encoded}/members?limit=1"
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error("Failed to fetch members: %s", exc)
        return None

    data = resp.json()
    hits = data.get("summary", {}).get("hits")
    if isinstance(hits, int):
        return hits

    logger.error("Unexpected members response shape: %s", list(data.keys()))
    return None


# ── diff report ───────────────────────────────────────────────────────────────


def _write_diff_csv(lidvids: set[str], path: Path) -> None:
    """Write a sorted set of LIDVIDs to a single-column CSV.

    Args:
        lidvids: LIDVIDs to write.
        path: Destination file path (parent directory must exist).
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["lidvid"])
        for lid in sorted(lidvids):
            writer.writerow([lid])


def print_diff_report(
    inventory_lidvids: set[str] | None,
    registry_lidvids: set[str] | None,
    output_dir: Path | None,
) -> tuple[int | None, int | None]:
    """Compute set differences between inventory and registry and report them.

    When ``output_dir`` is provided each non-empty diff is written to a CSV
    file there. When it is ``None`` small diffs (≤ 50 LIDVIDs) are printed
    inline; larger diffs show only the count with a prompt to use
    ``--output-dir``.

    Args:
        inventory_lidvids: Full set of LIDVIDs parsed from the inventory CSV,
            or ``None`` if unavailable.
        registry_lidvids: Set of LIDVIDs for non-superseded registry products
            (from ``get_all_registry_lidvids``), or ``None`` if unavailable.
            Superseded products are excluded because they are not expected in
            the current inventory and would produce false positives.
        output_dir: Directory to write diff CSV files to. ``None`` means
            print-only mode.

    Returns:
        ``(inv_not_reg_count, reg_not_inv_count)`` — sizes of the two diff
        sets, or ``(None, None)`` when the diff could not be computed.
    """
    if inventory_lidvids is None or registry_lidvids is None:
        logger.warning("Cannot compute diff: one or both LIDVID sets are unavailable")
        return None, None

    in_inv_not_reg = inventory_lidvids - registry_lidvids
    in_reg_not_inv = registry_lidvids - inventory_lidvids

    print()
    print(Color.bold("LIDVID diff: inventory vs registry (non-superseded)"))
    print("─" * 70)
    print(f"  Inventory LIDVIDs                   : {len(inventory_lidvids):>10,}")
    print(f"  Registry LIDVIDs (non-superseded)   : {len(registry_lidvids):>10,}")
    print()

    diffs = {
        "inventory_not_registry": (
            "In inventory, missing from registry",
            in_inv_not_reg,
        ),
        "registry_not_inventory": (
            "In registry (non-superseded), absent from inventory",
            in_reg_not_inv,
        ),
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    for filename, (label, lidvid_set) in diffs.items():
        n = len(lidvid_set)
        symbol = Color.red("✗") if n > 0 else Color.green("✓")
        print(f"  {symbol}  {label}: {n:,}")

        if n == 0:
            continue

        if output_dir is not None:
            dest = output_dir / f"diff_{filename}.csv"
            _write_diff_csv(lidvid_set, dest)
            print(f"       → {dest}")
        elif n <= 50:
            for lid in sorted(lidvid_set):
                print(f"       {lid}")
        else:
            print("       (use --output-dir to write full list to CSV)")

    print()
    return len(in_inv_not_reg), len(in_reg_not_inv)


# ── count report ──────────────────────────────────────────────────────────────


def print_report(
    lidvid: str,
    label_count: int | None,
    inventory_count: int | None,
    members_count: int | None,
    registry_raw_count: int | None,
    registry_superseded_count: int | None,
    registry_non_archived_count: int | None,
    registry_api_count: int | None,
) -> None:
    """Print the formatted count-comparison table to stdout.

    Args:
        lidvid: The collection LIDVID that was audited.
        label_count: Record count from the collection label.
        inventory_count: Row count from the downloaded inventory file.
        members_count: Hit count from the API /members endpoint.
        registry_raw_count: Raw wildcard count from the registry (all products).
        registry_superseded_count: Count of products that have been superseded
            (``ops:Provenance/ops:superseded_by`` present).
        registry_non_archived_count: Count of non-superseded products whose
            archive status is not ``archived`` or ``certified``.
        registry_api_count: Registry count filtered to non-superseded,
            archived/certified products (mirrors what the API exposes).
    """
    print()
    print(Color.bold(f"Collection audit: {lidvid}"))
    print("─" * 70)

    # primary=True rows are used for the all_match determination.
    # Informational rows (primary=False) are displayed with ℹ and excluded
    # from the match check.
    rows = [
        _ReportRow("Label (pds:records)", label_count, True),
        _ReportRow("Inventory file rows", inventory_count, True),
        _ReportRow("API /members hits", members_count, True),
        _ReportRow("Registry lid:* (all)", registry_raw_count, False),
        _ReportRow("  ↳ superseded", registry_superseded_count, False),
        _ReportRow("  ↳ not archived/certified", registry_non_archived_count, False),
        _ReportRow("Registry lid:* (API-visible) ¹", registry_api_count, True),
    ]

    primary_counts = [r.value for r in rows if r.value is not None and r.primary]
    all_match = len(primary_counts) >= 2 and len(set(primary_counts)) == 1
    ref = primary_counts[0] if primary_counts else None

    for row in rows:
        display = str(row.value) if row.value is not None else "N/A"
        if row.value is None:
            print(f"  {Color.yellow('⚠')}  {row.label:<32}  {display}")
        elif not row.primary:
            print(f"  {Color.cyan('ℹ')}  {row.label:<32}  {display}")
        elif all_match:
            print(f"  {Color.green('✓')}  {row.label:<32}  {display}")
        else:
            symbol = Color.green("✓") if row.value == ref else Color.red("✗")
            print(f"  {symbol}  {row.label:<32}  {display}")

    print()
    if all_match and primary_counts:
        print(f"  {Color.green('✓')}  All sources agree: {primary_counts[0]:,} products")
    else:
        print(f"  {Color.yellow('⚠')}  Sources disagree — investigate discrepancies above")
    collection_lid = lidvid.rsplit("::", 1)[0] if "::" in lidvid else lidvid
    print(
        f"  {Color.cyan('¹')}  Registry rows use a lid wildcard ({collection_lid}:*) — "
        f"approximate, not guaranteed to match exact collection membership"
    )

    if label_count is not None and inventory_count is not None and label_count != inventory_count:
        diff = inventory_count - label_count
        direction = "more" if diff > 0 else "fewer"
        print(
            f"  {Color.yellow('⚠')}  Inventory file has {abs(diff):,} {direction} rows than pds:records "
            f"— label may be stale or inventory file is malformed"
        )

    if members_count is not None and registry_api_count is not None and members_count != registry_api_count:
        diff = registry_api_count - members_count
        direction = "more" if diff > 0 else "fewer"
        print(
            f"  {Color.yellow('⚠')}  Registry lid:* (API-visible) has {abs(diff):,} {direction} products than API members "
            f"— possible indexing lag, version mismatch, or products outside this collection"
        )

    if label_count is not None and members_count is not None and label_count != members_count:
        diff = members_count - label_count
        direction = "more" if diff > 0 else "fewer"
        print(
            f"  {Color.yellow('⚠')}  API has {abs(diff):,} {direction} members than the label claims "
            f"— secondary members or versioned products may be included"
        )

    print()


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    """Build and return the parsed command-line arguments.

    Returns:
        Parsed argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description="Audit a PDS4 collection for product count discrepancies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "lidvids",
        nargs="*",
        metavar="LIDVID",
        help=(
            "One or more collection LIDVIDs to audit, e.g. "
            "urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0. "
            "May be combined with --from-file."
        ),
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "Path to a newline-separated file of collection LIDVIDs. "
            "Blank lines and lines starting with '#' are ignored. "
            "Combined with any LIDVIDs given on the command line."
        ),
    )
    parser.add_argument(
        "--api-base",
        default=_DEFAULT_API_BASE,
        metavar="URL",
        help=f"PDS Search API base URL (default: {_DEFAULT_API_BASE})",
    )
    parser.add_argument(
        "--registry-index",
        default=_DEFAULT_REGISTRY_INDEX,
        metavar="INDEX",
        help=f"OpenSearch index path (default: {_DEFAULT_REGISTRY_INDEX})",
    )
    parser.add_argument(
        "--wildcard",
        default=None,
        metavar="PAT",
        help=(
            "Override the wildcard pattern for the registry query. "
            "Only valid when auditing a single LIDVID."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="N",
        help="Per-request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Skip the registry client query",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "Optional path to a .env file to supplement credentials already "
            "sourced into the shell environment. Shell-sourced variables take "
            "precedence (loaded via os.environ.setdefault). Prefer sourcing "
            "credentials before invoking this script."
        ),
    )
    parser.add_argument(
        "--log-level",
        "-l",
        default="info",
        choices=list(_LOG_LEVELS),
        metavar="LEVEL",
        help="Logging verbosity: debug, info, warn, warning (default: info)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help=(
            "After the count report, fetch all LIDVIDs from inventory and "
            "registry and print missing LIDVIDs for each direction. "
            "Requires registry access (incompatible with --no-registry)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Write all output files to DIR (created if absent). "
            "summary.csv is written at the root; each collection's diff CSVs "
            "go in a subdirectory named after the collection. "
            "Without --diff, only summary.csv is written."
        ),
    )
    return parser.parse_args()


def _read_lidvids_from_file(path: Path) -> list[str]:
    """Read a newline-separated list of LIDVIDs from a file.

    Blank lines and lines whose first non-whitespace character is ``#`` are
    skipped, allowing comments and section breaks in the file.

    Args:
        path: Path to the LIDVID list file.

    Returns:
        Ordered list of LIDVID strings.

    Raises:
        SystemExit: If the file cannot be read.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        logger.error("Cannot read --from-file %s: %s", path, exc)
        raise SystemExit(1) from exc
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def _collection_slug(collection_lid: str) -> str:
    """Return a short filesystem-safe name for a collection LID.

    Uses the last two colon-separated segments of the LID joined with ``-``,
    e.g. ``mars2020_navcam_ops_stereo-data``.

    Args:
        collection_lid: Collection LID (LIDVID with version stripped).

    Returns:
        Slug string suitable for use as a directory or filename component.
    """
    parts = collection_lid.rsplit(":", 2)
    return "-".join(parts[-2:]) if len(parts) >= 2 else collection_lid.replace(":", "_")


def _diff_output_for(base: Path | None, collection_lid: str) -> Path | None:
    """Return the diff output directory for one collection.

    Always places diff CSVs in a per-collection subdirectory of ``base`` so
    the collection identity is embedded in the path and files never overwrite
    one another when multiple LIDVIDs are audited.

    Args:
        base: The ``--output-dir`` path supplied by the user, or ``None``.
        collection_lid: The collection LID (LIDVID with version stripped).

    Returns:
        ``<base>/<slug>/`` directory path, or ``None`` when ``base`` is ``None``.
    """
    if base is None:
        return None
    return base / _collection_slug(collection_lid)


_SUMMARY_FIELDNAMES = [
    "lidvid",
    "label",
    "inventory",
    "api_members",
    "registry_all",
    "registry_superseded",
    "registry_not_archived",
    "registry_api_visible",
    "diff_inventory_not_registry",
    "diff_registry_not_inventory",
]


def write_summary_csv(results: list[dict], output_dir: Path) -> None:
    """Write a one-row-per-collection summary of all audit results.

    Args:
        results: List of result dicts returned by ``_audit_one``.
        output_dir: Directory in which to write ``summary.csv``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "summary.csv"
    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_SUMMARY_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    logger.info("Summary written to %s", dest)


def _audit_one(
    lidvid: str,
    args: argparse.Namespace,
    session: requests.Session,
    registry_auth: RequestsAWSV4SignerAuth | None,
) -> dict:
    """Run the full audit for a single collection LIDVID.

    Args:
        lidvid: Collection LIDVID to audit.
        args: Parsed CLI arguments shared across all collections.
        session: Shared HTTP session for public API calls.
        registry_auth: Authenticated AOSS auth object, or ``None`` when
            ``--no-registry`` was passed or authentication failed.

    Returns:
        Dict of counts keyed by ``_SUMMARY_FIELDNAMES``, suitable for a row
        in the summary CSV.
    """
    collection_lid = lidvid.rsplit("::", 1)[0] if "::" in lidvid else lidvid

    logger.info("Auditing collection: %s", lidvid)

    # Source 1: label count + inventory file URL
    logger.info("Fetching collection label from API …")
    label_count, file_ref = get_label_count(session, args.api_base, lidvid, args.timeout)

    if label_count is not None:
        logger.info("pds:records = %d", label_count)
    else:
        logger.warning("Could not read pds:records from label")

    # Source 2: inventory file.
    # When --diff is set we collect the full LIDVID set in the same download.
    inventory_count: int | None = None
    inventory_lidvids: set[str] | None = None

    if file_ref:
        logger.info("Inventory file: %s", file_ref)
        logger.info("Downloading inventory table …")
        if args.diff:
            inventory_count, inventory_lidvids = fetch_inventory_lidvids(
                session, file_ref, args.timeout
            )
        else:
            inventory_count = count_inventory_rows(session, file_ref, args.timeout)
        if inventory_count is not None:
            logger.info("Inventory row count = %d", inventory_count)
    else:
        logger.warning(
            "ops:Data_File_Info.ops:file_ref not found in label — skipping inventory check"
        )

    # Source 3: API members count
    logger.info("Querying API members endpoint …")
    members_count = get_api_members_count(session, args.api_base, lidvid, args.timeout)
    if members_count is not None:
        logger.info("API members hits = %d", members_count)

    # Source 4: registry counts (skipped when auth is unavailable)
    registry_raw_count: int | None = None
    registry_superseded_count: int | None = None
    registry_non_archived_count: int | None = None
    registry_api_count: int | None = None

    if registry_auth is not None:
        pattern = args.wildcard or f"{collection_lid}:*"
        logger.info("Registry lid pattern: %s", pattern)

        logger.info("Querying registry (all products) …")
        registry_raw_count = get_registry_count(
            _wildcard_query(pattern), args.registry_index, registry_auth, args.timeout
        )
        if registry_raw_count is not None:
            logger.info("Registry count (all) = %d", registry_raw_count)

        logger.info("Querying registry (superseded) …")
        registry_superseded_count = get_registry_count(
            _superseded_query(pattern), args.registry_index, registry_auth, args.timeout
        )
        if registry_superseded_count is not None:
            logger.info("Registry count (superseded) = %d", registry_superseded_count)

        logger.info("Querying registry (not archived/certified, non-superseded) …")
        registry_non_archived_count = get_registry_count(
            _non_archived_query(pattern), args.registry_index, registry_auth, args.timeout
        )
        if registry_non_archived_count is not None:
            logger.info("Registry count (not archived/certified) = %d", registry_non_archived_count)

        logger.info("Querying registry (API-visible: non-superseded, archived/certified) …")
        registry_api_count = get_registry_count(
            _api_visible_query(pattern), args.registry_index, registry_auth, args.timeout
        )
        if registry_api_count is not None:
            logger.info("Registry count (API-visible) = %d", registry_api_count)
    else:
        logger.info("Registry query skipped")

    print_report(
        lidvid,
        label_count,
        inventory_count,
        members_count,
        registry_raw_count,
        registry_superseded_count,
        registry_non_archived_count,
        registry_api_count,
    )

    # Optional LIDVID-level diff
    diff_inv_not_reg: int | None = None
    diff_reg_not_inv: int | None = None

    if args.diff:
        if registry_auth is None:
            logger.error("Registry authentication unavailable; skipping diff for %s", lidvid)
        else:
            logger.info("Fetching all registry LIDVIDs for diff …")
            registry_lidvids = get_all_registry_lidvids(
                collection_lid, args.wildcard, args.registry_index, registry_auth, args.timeout
            )
            diff_output = _diff_output_for(args.output_dir, collection_lid)
            diff_inv_not_reg, diff_reg_not_inv = print_diff_report(
                inventory_lidvids, registry_lidvids, diff_output
            )

    return {
        "lidvid": lidvid,
        "label": label_count,
        "inventory": inventory_count,
        "api_members": members_count,
        "registry_all": registry_raw_count,
        "registry_superseded": registry_superseded_count,
        "registry_not_archived": registry_non_archived_count,
        "registry_api_visible": registry_api_count,
        "diff_inventory_not_registry": diff_inv_not_reg,
        "diff_registry_not_inventory": diff_reg_not_inv,
    }


def main() -> int:
    """Entry point for the collection audit script.

    Returns:
        Exit code (0 on success, 1 on argument or authentication error).
    """
    args = parse_args()

    logging.basicConfig(
        level=_LOG_LEVELS[args.log_level],
        stream=sys.stderr,
        format="%(levelname)s %(message)s",
    )

    if args.diff and args.no_registry:
        logger.error("--diff requires registry access; cannot be used with --no-registry")
        return 1

    # Merge LIDVIDs from positional args and --from-file, preserving order.
    lidvids: list[str] = list(args.lidvids)
    if args.from_file:
        lidvids += _read_lidvids_from_file(args.from_file)

    if not lidvids:
        logger.error("No LIDVIDs provided. Pass them on the command line or via --from-file.")
        return 1

    if args.wildcard and len(lidvids) > 1:
        logger.error("--wildcard can only be used when auditing a single LIDVID")
        return 1

    logger.info("API base: %s", args.api_base)

    session = make_session()

    # Authenticate once; the auth object is reused for every collection.
    registry_auth = None
    if not args.no_registry:
        load_credentials(args.env_file)
        logger.info("Authenticating to registry …")
        registry_auth = make_registry_auth()

    results = []
    for lidvid in lidvids:
        results.append(_audit_one(lidvid, args, session, registry_auth))

    if args.output_dir is not None:
        write_summary_csv(results, args.output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
