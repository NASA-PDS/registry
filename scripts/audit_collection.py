#!/usr/bin/env python3
"""
Audit a PDS4 collection to diagnose product count discrepancies and bad file references.

Compares four independent sources for member product counts:

  1. Label record count  — pds:Inventory.pds:records from the collection label
  2. Inventory file rows — downloads the inventory table and counts data rows
  3. API members count   — /products/{lidvid}/members hits total
  4. Registry count      — OpenSearch wildcard _count query via pds-registry-client

Pass --diff to follow up any discrepancy with a full LIDVID-level comparison
between the inventory file and the registry (the only two sources that support
complete enumeration — the API /members endpoint is capped at 10,000 items with
no pagination, so it cannot be fully diffed directly).

Pass --check-files to also audit the file paths and checksums that the registry
holds for the collection and every member product, as served by the API. A
Deep Archive (AIP/SIP) can only be generated when every file reference is an
absolute URL and every checksum is an MD5 digest, so each of these is reported:

  - a file_ref that is not an absolute URL (for example the literal string
    "null", or a bare path with no scheme and host)
  - an md5_checksum that is not 32 hexadecimal digits (for example "null")
  - data file_refs and md5_checksums that do not pair up, or a label file_ref
    with no md5_checksum, or a product with no label file_ref at all

This pages through every member product, so it can take a long time for large
collections (about 1,000 products per 1-2 seconds).

Setup:
    Install registry-client dependencies before running registry queries:

        pip install -r scripts/requirements.txt

    Source your registry credentials into the shell environment before running:

        source ~/.pds/registry-client-prod.env

Usage:
    python scripts/audit_collection.py <collection_lidvid> [options]

Examples:
    # Count comparison only (no registry)
    python scripts/audit_collection.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 --no-registry

    # Full audit including registry counts (credentials must be sourced first)
    source ~/.pds/registry-client-prod.env
    python scripts/audit_collection.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0

    # Audit multiple collections — pass directly or via a file
    source ~/.pds/registry-client-prod.env
    python scripts/audit_collection.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \\
        urn:nasa:pds:mars2020_mastcam-z_ops:data_raw::14.0

    python scripts/audit_collection.py --from-file collections.txt

    # Full audit + LIDVID-level diff written to CSV files
    # summary.csv goes to audit_results/, diff CSVs to per-collection subdirs
    source ~/.pds/registry-client-prod.env
    python scripts/audit_collection.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \\
        urn:nasa:pds:mars2020_mastcam-z_ops:data_raw::14.0 \\
        --diff --output-dir ./audit_results/

    # Check file paths and checksums of every member product (no registry
    # credentials needed); problems are also written to file_problems.csv
    python scripts/audit_collection.py \\
        urn:nasa:pds:mars2020_navcam_ops_stereo:data::16.0 \\
        --no-registry --check-files --output-dir ./audit_results/

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
    --check-files         Page through the collection and every member product
                          and report file_refs that are not absolute URLs and
                          md5_checksums that are not MD5 digests
    --output-dir DIR      Write all output files to DIR: summary.csv at the
                          root, per-collection diff and file_problems CSVs in
                          subdirectories
    --verbose-report      After the count report, print a plain-language
                          explanation of every source and, when the API
                          /members count is short, compare the collection's
                          harvest time with the latest member product's harvest
                          time to say whether the shortfall will resolve on its
                          own or needs the collection to be re-harvested
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import re
import sys
import textwrap
import urllib.parse
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
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
_REGISTRY_HARVEST_FIELD = "ops:Harvest_Info/ops:harvest_date_time"
"""Registry (OpenSearch) field holding the time a product was harvested."""
_API_HARVEST_PROPERTY = "ops:Harvest_Info.ops:harvest_date_time"
"""The same field as exposed in the Search API's ``properties`` object."""

_DATA_FILE_REF = "ops:Data_File_Info.ops:file_ref"
_DATA_FILE_MD5 = "ops:Data_File_Info.ops:md5_checksum"
_LABEL_FILE_REF = "ops:Label_File_Info.ops:file_ref"
_LABEL_FILE_MD5 = "ops:Label_File_Info.ops:md5_checksum"
_HARVEST_SORT_KEY = "ops:Harvest_Info.ops:harvest_date_time"
"""API property used to sort and page (``search-after``) through a collection's members."""
_FILE_FIELDS = [_DATA_FILE_REF, _DATA_FILE_MD5, _LABEL_FILE_REF, _LABEL_FILE_MD5, _HARVEST_SORT_KEY]
_MEMBER_PAGE_SIZE = 1000
_MD5_PATTERN = re.compile(r"[0-9a-fA-F]{32}")

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


class FileProblem(NamedTuple):
    """One unusable file reference or checksum found on a product."""

    lidvid: str
    kind: str
    problem: str
    value: str


class FileScan(NamedTuple):
    """Result of checking the file references of a collection and its members."""

    examined: int
    expected: int | None
    problems: list[FileProblem]


@dataclass
class AuditFindings:
    """Everything gathered for one collection, as input to the verbose report.

    Attributes:
        lidvid: Collection LIDVID that was audited.
        registry_queried: ``False`` when registry queries were skipped
            (``--no-registry`` or authentication unavailable).
        registry_pattern: Wildcard pattern used for the registry counts.
        label_count: ``pds:Inventory.pds:records`` from the collection label.
        inventory_url: URL of the inventory table, if the label references one.
        inventory_count: Data rows counted in the downloaded inventory table.
        members_count: Hit total from the API ``/members`` endpoint.
        registry_raw_count: All registry products matching the wildcard.
        registry_superseded_count: Superseded products among those.
        registry_non_archived_count: Non-superseded products not archived/certified.
        registry_api_count: Non-superseded, archived/certified products.
        collection_harvest: Harvest time of the collection product itself.
        latest_product_harvest: Latest harvest time among non-superseded members.
        latest_product_lidvid: LIDVID of the member with that harvest time.
    """

    lidvid: str
    registry_queried: bool
    registry_pattern: str | None = None
    label_count: int | None = None
    inventory_url: str | None = None
    inventory_count: int | None = None
    members_count: int | None = None
    registry_raw_count: int | None = None
    registry_superseded_count: int | None = None
    registry_non_archived_count: int | None = None
    registry_api_count: int | None = None
    collection_harvest: str | None = None
    latest_product_harvest: str | None = None
    latest_product_lidvid: str | None = None


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


# ── harvest times ─────────────────────────────────────────────────────────────


def _first_value(raw: object) -> str | None:
    """Return a scalar string from a field that may be a single value or a list.

    Args:
        raw: Raw field value from an API ``properties`` object or a registry
            ``_source`` document.

    Returns:
        The first element as a string, or ``None`` if the field is absent or empty.
    """
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    return None if raw is None else str(raw)


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO 8601 harvest timestamp into an aware datetime.

    Args:
        value: Timestamp string such as ``2025-03-01T12:34:56.789Z``. Naive
            values are assumed to be UTC.

    Returns:
        Timezone-aware datetime, or ``None`` if ``value`` is empty or unparseable.
    """
    if not value:
        return None
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        logger.warning("Could not parse harvest timestamp: %r", value)
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def get_latest_member_harvest(
    collection_lid: str,
    wildcard_pattern: str | None,
    registry_index: str,
    auth: RequestsAWSV4SignerAuth,
    timeout: int,
) -> tuple[str | None, str | None]:
    """Return the most recent harvest time among non-superseded member products.

    Superseded products are excluded so an old version that happens to carry a
    late harvest time cannot masquerade as the latest load.

    Args:
        collection_lid: Collection LID used to derive the default wildcard.
        wildcard_pattern: Explicit wildcard override (defaults to
            ``<collection_lid>:*``).
        registry_index: Index path used for the count query; ``_count`` is
            replaced with ``_search`` automatically.
        auth: Signed AWS auth from ``make_registry_auth``.
        timeout: Per-request timeout in seconds.

    Returns:
        A ``(lidvid, harvest_time)`` tuple for the latest-harvested member, or
        ``(None, None)`` if the query fails or no member carries a harvest time.
    """
    pattern = wildcard_pattern or f"{collection_lid}:*"
    search_index = registry_index.removesuffix("_count") + "_search"
    query = {
        "size": 1,
        "_source": ["lidvid", _REGISTRY_HARVEST_FIELD],
        "sort": [{_REGISTRY_HARVEST_FIELD: {"order": "desc", "unmapped_type": "date"}}],
        **_non_superseded_query(pattern),
    }
    data = run_registry_query(query, search_index, auth, timeout)
    if data is None:
        return None, None

    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        logger.warning("No member products found for pattern %s", pattern)
        return None, None

    source = hits[0].get("_source", {})
    return _first_value(source.get("lidvid")), _first_value(source.get(_REGISTRY_HARVEST_FIELD))


# ── source 1: label record count ─────────────────────────────────────────────


def get_label_count(
    session: requests.Session,
    api_base: str,
    lidvid: str,
    timeout: int,
) -> tuple[int | None, str | None, str | None]:
    """Return the label's stated record count, inventory file URL and harvest time.

    Args:
        session: Shared HTTP session.
        api_base: PDS Search API base URL.
        lidvid: Collection LIDVID to look up.
        timeout: Per-request timeout in seconds.

    Returns:
        A ``(record_count, file_ref, harvest_time)`` tuple. Any element may be
        ``None`` if the corresponding field is absent from the label.
    """
    encoded = urllib.parse.quote(lidvid, safe="")
    url = f"{api_base}/products/{encoded}"
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error("Failed to fetch collection product: %s", exc)
        return None, None, None

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

    harvest_time = _first_value(props.get(_API_HARVEST_PROPERTY))

    return record_count, file_ref, harvest_time


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


# ── source 5: file paths and checksums ────────────────────────────────────────


def is_absolute_url(url: str) -> bool:
    """Say whether ``url`` is an absolute URL with a scheme, host, and path.

    Args:
        url: A ``file_ref`` value from the registry.

    Returns:
        ``False`` for values such as the literal string ``null`` or a bare path
        with no scheme and host, which cannot be listed in a manifest.
    """
    parsed = urllib.parse.urlparse(url)
    return bool(parsed.scheme and parsed.netloc and parsed.path)


def is_valid_md5(md5: str) -> bool:
    """Say whether ``md5`` is an MD5 digest of exactly 32 hexadecimal digits.

    Args:
        md5: An ``md5_checksum`` value from the registry.

    Returns:
        ``False`` for values such as the literal string ``null`` or an empty string.
    """
    return _MD5_PATTERN.fullmatch(md5) is not None


def check_product_files(product: dict) -> list[FileProblem]:
    """Find the unusable file references and checksums of one API product.

    Args:
        product: A product object from the PDS Search API, with its file
            properties at ``product["properties"]``.

    Returns:
        One ``FileProblem`` per bad reference or checksum; empty when the
        product's files are all usable.
    """
    lidvid = product.get("id", "<unknown>")
    props = product.get("properties", {})
    problems: list[FileProblem] = []

    # (kind, reference, checksum) triples; a checksum of None means it is missing.
    files: list[tuple[str, str, str | None]] = []

    data_refs = props.get(_DATA_FILE_REF, [])
    data_md5s = props.get(_DATA_FILE_MD5, [])
    if len(data_refs) != len(data_md5s):
        problems.append(
            FileProblem(
                lidvid,
                "data file",
                "number of file_refs and md5_checksums differ",
                f"{len(data_refs)} file_ref(s), {len(data_md5s)} md5_checksum(s)",
            )
        )
    for i, ref in enumerate(data_refs):
        files.append(("data file", ref, data_md5s[i] if i < len(data_md5s) else None))

    label_refs = props.get(_LABEL_FILE_REF, [])
    label_md5s = props.get(_LABEL_FILE_MD5, [])
    if label_refs:
        files.append(("label file", label_refs[0], label_md5s[0] if label_md5s else None))
    else:
        problems.append(FileProblem(lidvid, "label file", "no file_ref", ""))

    for kind, ref, md5 in files:
        if not is_absolute_url(ref):
            problems.append(FileProblem(lidvid, kind, "file_ref is not an absolute URL", ref))
        if md5 is not None and not is_valid_md5(md5):
            problems.append(FileProblem(lidvid, kind, "md5_checksum is not an MD5 digest", md5))
        elif md5 is None and kind == "label file":
            problems.append(FileProblem(lidvid, kind, "no md5_checksum", ref))

    return problems


def _fetch_json(session: requests.Session, url: str, params: dict | None, timeout: int) -> dict | None:
    """GET ``url`` and return the parsed JSON object, or ``None`` after logging an error."""
    try:
        resp = session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except (requests.exceptions.RequestException, ValueError) as exc:
        logger.error("Request to %s failed: %s", url, exc)
        return None


def iter_member_pages(
    session: requests.Session,
    api_base: str,
    lidvid: str,
    timeout: int,
) -> Iterator[dict | None]:
    """Yield each page of the API ``/members`` response for a collection.

    Pages are sorted by harvest date and followed with ``search-after``, so the
    10,000-item limit on a single query does not apply.

    Args:
        session: Shared HTTP session.
        api_base: PDS Search API base URL.
        lidvid: Collection LIDVID whose members to page through.
        timeout: Per-request timeout in seconds.

    Yields:
        Each parsed response page, or ``None`` (after which iteration stops) if a
        request fails.
    """
    encoded = urllib.parse.quote(lidvid, safe="")
    url = f"{api_base}/products/{encoded}/members"
    params: dict = {
        "limit": _MEMBER_PAGE_SIZE,
        "sort": _HARVEST_SORT_KEY,
        "fields": ",".join(_FILE_FIELDS),
    }
    while True:
        data = _fetch_json(session, url, params, timeout)
        yield data
        if data is None:
            return
        members = data.get("data", [])
        if len(members) < _MEMBER_PAGE_SIZE:
            return
        next_key = members[-1].get("properties", {}).get(_HARVEST_SORT_KEY)
        if not next_key:
            logger.error("Last member on the page has no %s; cannot page further", _HARVEST_SORT_KEY)
            yield None
            return
        next_key = next_key[0] if isinstance(next_key, list) else next_key
        if next_key == params.get("search-after"):
            logger.error(
                "More than %d members share the harvest time %s; cannot page past them",
                _MEMBER_PAGE_SIZE,
                next_key,
            )
            yield None
            return
        params["search-after"] = next_key


def scan_collection_files(
    session: requests.Session,
    api_base: str,
    lidvid: str,
    timeout: int,
) -> FileScan | None:
    """Check the file paths and checksums of a collection and all its members.

    Args:
        session: Shared HTTP session.
        api_base: PDS Search API base URL.
        lidvid: Collection LIDVID to check.
        timeout: Per-request timeout in seconds.

    Returns:
        A ``FileScan``, or ``None`` if the collection itself could not be
        fetched. ``FileScan.examined`` counts the collection plus every member
        seen, and ``FileScan.expected`` is the total the API reports. If a page
        fails or paging misses or repeats products the two differ, and the
        problems found up to that point are still returned.
    """
    encoded = urllib.parse.quote(lidvid, safe="")
    collection = _fetch_json(session, f"{api_base}/products/{encoded}", None, timeout)
    if collection is None:
        return None
    problems = check_product_files(collection)
    examined = 1

    expected: int | None = None
    for page in iter_member_pages(session, api_base, lidvid, timeout):
        if page is None:
            break
        if expected is None:
            hits = page.get("summary", {}).get("hits")
            expected = hits + 1 if isinstance(hits, int) else None
        members = page.get("data", [])
        for member in members:
            problems.extend(check_product_files(member))
        examined += len(members)
        total = f"{expected:,}" if expected is not None else "?"
        logger.info("Checked the file references of %s of %s products …", f"{examined:,}", total)

    return FileScan(examined, expected, problems)


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


# ── file report ───────────────────────────────────────────────────────────────


def _write_problems_csv(problems: list[FileProblem], path: Path) -> None:
    """Write file problems to a CSV with one row per problem.

    Args:
        problems: Problems to write.
        path: Destination file path (parent directory must exist).
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FileProblem._fields)
        writer.writerows(problems)


def print_file_report(scan: FileScan | None, output_dir: Path | None) -> int | None:
    """Print the result of the file path and checksum check.

    When ``output_dir`` is provided any problems are written to
    ``file_problems.csv`` there. When it is ``None`` small lists (≤ 50 problems)
    are printed inline; larger lists show only the count with a prompt to use
    ``--output-dir``.

    Args:
        scan: Result of ``scan_collection_files``, or ``None`` if unavailable.
        output_dir: Directory to write ``file_problems.csv`` to, or ``None``.

    Returns:
        The number of problems found, or ``None`` when the check could not run.
    """
    print()
    print(Color.bold("File paths and checksums"))
    print("─" * 70)

    if scan is None:
        print(f"  {Color.yellow('⚠')}  Could not check: the collection could not be fetched from the API")
        print()
        return None

    expected = f"{scan.expected:,}" if scan.expected is not None else "an unknown number"
    print(f"  Products examined                   : {scan.examined:>10,}")
    if scan.examined != scan.expected:
        print(
            f"  {Color.yellow('⚠')}  The API reports {expected} products, so this check is incomplete "
            f"— a page failed to load or paging missed or repeated products"
        )

    n = len(scan.problems)
    if n == 0:
        if scan.examined == scan.expected:
            print(f"  {Color.green('✓')}  Every file_ref is an absolute URL and every md5_checksum is an MD5 digest")
        else:
            print(f"  {Color.yellow('⚠')}  No problems found in the products that were examined")
        print()
        return 0

    affected = len({p.lidvid for p in scan.problems})
    print(f"  {Color.red('✗')}  {n:,} problem(s) in {affected:,} product(s) — a Deep Archive cannot be generated")

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        dest = output_dir / "file_problems.csv"
        _write_problems_csv(scan.problems, dest)
        print(f"       → {dest}")
    elif n <= 50:
        for p in scan.problems:
            print(f"       {p.lidvid}: {p.kind} {p.problem}" + (f": {p.value!r}" if p.value else ""))
    else:
        print("       (use --output-dir to write the full list to CSV)")

    print()
    return n


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
        hint = (
            "secondary members or versioned products may be included"
            if diff > 0
            else "products may not be loaded, may not be API-visible, or the members "
            "relationship may be stale (rerun with --verbose-report)"
        )
        print(
            f"  {Color.yellow('⚠')}  API has {abs(diff):,} {direction} members than the label claims "
            f"— {hint}"
        )

    print()


# ── verbose report ────────────────────────────────────────────────────────────

_WRAP_WIDTH = 100


def _print_wrapped(text: str, indent: int) -> None:
    """Print ``text`` word-wrapped and indented by ``indent`` spaces."""
    pad = " " * indent
    print(textwrap.fill(text, width=_WRAP_WIDTH, initial_indent=pad, subsequent_indent=pad))


def _print_source(title: str, value: int | None, explanation: str) -> None:
    """Print one source heading with its count and a wrapped explanation."""
    shown = f"{value:,}" if value is not None else "N/A"
    print(f"  {Color.bold(title)}: {shown}")
    _print_wrapped(explanation, 6)
    print()


def _compare_phrase(value: int, reference: int, reference_name: str) -> str:
    """Return a sentence stating how ``value`` relates to ``reference``."""
    if value == reference:
        return f"This matches the {reference_name}."
    diff = value - reference
    direction = "more" if diff > 0 else "fewer"
    return f"This is {abs(diff):,} {direction} than the {reference_name} ({reference:,})."


def _expected_count(findings: AuditFindings) -> tuple[int | None, str]:
    """Return the count the other sources are compared against, and what it is called.

    The downloaded inventory file is preferred because it is the provider's actual list of members;
    the record count declared in the label is the fallback.
    """
    if findings.inventory_count is not None:
        return findings.inventory_count, "inventory file"
    return findings.label_count, "label"


def _api_visible_conclusion(api_visible: int, expected: int | None, members: int | None) -> str | None:
    """Return a sentence on what the API-visible registry count says about the shortfall, if it says anything.

    Args:
        api_visible: Non-superseded, archived/certified registry products.
        expected: The inventory (or label) count the registry is compared against.
        members: The API ``/members`` total.

    Returns:
        A conclusion, or ``None`` when the counts agree or there is nothing to compare.
    """
    if expected is None:
        return None
    if api_visible < expected:
        return (
            f"The registry has {expected - api_visible:,} fewer API-visible products than expected: they may "
            "not be loaded, may be superseded, or may not be archived/certified (rerun with --diff to "
            "list them)."
        )
    if api_visible > expected:
        return (
            f"The wildcard matches {api_visible - expected:,} more API-visible products than expected, "
            "so it may include products outside this collection version."
        )
    if members is not None and members < api_visible:
        return (
            "The registry has as many API-visible products as expected, so the /members shortfall looks "
            "like a gap in the members relationship rather than in loading (this wildcard count is "
            "approximate; use --diff to confirm)."
        )
    return None


def classify_harvest_order(collection_harvest: str | None, latest_product_harvest: str | None) -> str | None:
    """Say whether the collection was harvested before its most recent member.

    Args:
        collection_harvest: Harvest time of the collection product.
        latest_product_harvest: Latest harvest time among its member products.

    Returns:
        ``"collection_first"`` when the collection was harvested strictly before
        the latest member, ``"collection_last"`` when it was harvested at the
        same time or later, or ``None`` if either time is missing or unparseable.
    """
    collection_time = parse_timestamp(collection_harvest)
    product_time = parse_timestamp(latest_product_harvest)
    if collection_time is None or product_time is None:
        return None
    return "collection_first" if collection_time < product_time else "collection_last"


def _print_sources(findings: AuditFindings) -> None:
    """Print the "what each source says" section of the verbose report."""
    print(Color.bold("What each source says"))
    print()

    if findings.label_count is None:
        _print_source(
            "Label (pds:records)",
            None,
            "pds:Inventory.pds:records could not be read from the collection label returned by the Search API.",
        )
    else:
        _print_source(
            "Label (pds:records)",
            findings.label_count,
            "The number of member records the data provider declared in the collection label "
            "(pds:Inventory/pds:records). This is a claim by the provider and is not verified by anything else.",
        )

    if findings.inventory_count is not None:
        text = (
            f"The inventory table was downloaded from {findings.inventory_url} and confirmed to contain "
            f"{findings.inventory_count:,} data rows (header excluded)."
        )
        if findings.label_count is not None:
            text += " " + _compare_phrase(findings.inventory_count, findings.label_count, "label")
        _print_source("Inventory file rows", findings.inventory_count, text)
    elif findings.inventory_url is None:
        _print_source(
            "Inventory file rows",
            None,
            "The collection label has no inventory file reference (ops:Data_File_Info.ops:file_ref), "
            "so the inventory table could not be checked.",
        )
    else:
        _print_source(
            "Inventory file rows",
            None,
            f"Downloading or parsing the inventory table at {findings.inventory_url} failed; see the log output.",
        )

    if findings.members_count is None:
        _print_source("API /members hits", None, "The /members request failed; see the log output.")
    else:
        reference, name = _expected_count(findings)
        text = (
            "The total reported by the Search API's /members endpoint for this collection, which is what "
            "API users see. The members relationship is built by the registry sweepers after the collection "
            "has been processed, so this count can lag what is actually in the registry."
        )
        if reference is not None:
            text += " " + _compare_phrase(findings.members_count, reference, name)
        _print_source("API /members hits", findings.members_count, text)

    if not findings.registry_queried:
        _print_source(
            "Registry lid:* (all)",
            None,
            "The registry was not queried (--no-registry was given or registry authentication was "
            "unavailable). Source your registry credentials and rerun to compare against the registry.",
        )
        return

    reference, name = _expected_count(findings)
    raw = findings.registry_raw_count
    superseded = findings.registry_superseded_count
    non_archived = findings.registry_non_archived_count
    api_visible = findings.registry_api_count

    text = (
        f"Every registry product whose LID matches {findings.registry_pattern}, including superseded versions "
        "and products in any archive status. A wildcard match is approximate, not exact collection membership."
    )
    if raw is not None and reference is not None:
        text += " " + _compare_phrase(raw, reference, name)
    if raw is not None and superseded is not None and non_archived is not None and api_visible is not None:
        accounted = superseded + non_archived + api_visible
        if accounted == raw:
            text += (
                f" It breaks down into {superseded:,} superseded, {non_archived:,} not archived/certified, "
                f"and {api_visible:,} API-visible."
            )
        else:
            text += (
                f" The superseded, not archived/certified, and API-visible counts below add up to {accounted:,}, "
                f"which differs from this total by {abs(raw - accounted):,}; they were queried separately, so "
                "products may have been loaded or changed in between."
            )
    _print_source("Registry lid:* (all)", raw, text)

    text = "Products replaced by a newer version. They are not expected in the current inventory or the API."
    if superseded and raw:
        text += f" These {superseded:,} of the {raw:,} registry products are excluded from the API-visible count."
    _print_source("  of which superseded", superseded, text)

    text = (
        "Non-superseded products whose archive status is neither archived nor certified (for example "
        "staged). They are in the registry but the API does not expose them."
    )
    if non_archived and raw:
        text += f" These {non_archived:,} of the {raw:,} registry products are excluded from the API-visible count."
    _print_source("  of which not archived/certified", non_archived, text)

    text = (
        "Non-superseded products with archive status archived or certified: the set the API is able to "
        "expose."
    )
    if api_visible is not None:
        if reference is not None:
            text += " " + _compare_phrase(api_visible, reference, name)
        if findings.members_count is not None:
            text += " " + _compare_phrase(api_visible, findings.members_count, "API /members total")
        conclusion = _api_visible_conclusion(api_visible, reference, findings.members_count)
        if conclusion is not None:
            text += " " + conclusion
    _print_source("Registry lid:* (API-visible)", api_visible, text)


def _print_harvest_analysis(findings: AuditFindings, shortfall: int) -> None:
    """Print the harvest-time comparison used to judge whether /members will self-heal."""
    print(Color.bold("Will the /members shortfall resolve on its own?"))
    print()
    _print_wrapped(
        "The members relationship is only populated when the registry sweepers process a collection. "
        "Sweepers do not revisit a collection that has already been processed, so if member products "
        "were overwritten after that, /members stays stale until the collection itself is re-harvested. "
        "Comparing harvest times (ops:Harvest_Info/ops:harvest_date_time) shows which situation applies.",
        2,
    )
    print()

    collection_time = parse_timestamp(findings.collection_harvest)
    product_time = parse_timestamp(findings.latest_product_harvest)
    print(f"  Collection harvested       : {collection_time.isoformat() if collection_time else 'unknown'}")
    latest_suffix = f"  ({findings.latest_product_lidvid})" if findings.latest_product_lidvid else ""
    print(f"  Latest member harvested    : {product_time.isoformat() if product_time else 'unknown'}{latest_suffix}")
    print()

    order = classify_harvest_order(findings.collection_harvest, findings.latest_product_harvest)
    if order is None:
        if not findings.registry_queried:
            reason = "the latest member's harvest time comes from the registry, which was not queried"
        else:
            reason = "one or both harvest times are missing or could not be parsed"
        _print_wrapped(
            f"Cannot tell: {reason}. Without both times it is not possible to say whether sweepers "
            "still have work to do.",
            2,
        )
    elif order == "collection_first":
        gap = product_time - collection_time  # type: ignore[operator]
        _print_wrapped(
            f"The collection was harvested {gap} BEFORE the most recent member product, and /members "
            f"is {shortfall:,} short. Two explanations fit:",
            2,
        )
        print()
        _print_wrapped(
            "(1) Sweepers have not yet processed the remaining members listed in the inventory. "
            "This should resolve once the sweepers finish; recheck after their next run.",
            4,
        )
        _print_wrapped(
            "(2) The latest products were overwritten after the collection was processed. The "
            "collection will not be processed again unless it is also rewritten, so /members will "
            "stay short. Re-harvest the collection (label and inventory) to fix it.",
            4,
        )
        print()
        _print_wrapped(
            "If the shortfall is unchanged after the next sweeper run, treat it as (2).",
            2,
        )
    else:
        _print_wrapped(
            f"The collection was harvested at the same time as or after the most recent member product, "
            f"so load order does not explain the {shortfall:,}-product shortfall. Look at whether the "
            "missing products are loaded at all, are superseded, or are not archived/certified "
            "(rerun with --diff to list the specific LIDVIDs).",
            2,
        )
    print()


def print_verbose_report(findings: AuditFindings) -> None:
    """Print a plain-language explanation of the audit results.

    Complements ``print_report`` by saying what each count is and where it came
    from, then, when the API ``/members`` total is short of the expected count,
    uses harvest times to indicate whether the shortfall will resolve itself.

    Args:
        findings: Counts and harvest times gathered for one collection.
    """
    print(Color.bold(f"Verbose report: {findings.lidvid}"))
    print("─" * 70)
    print()
    _print_sources(findings)

    expected, expected_name = _expected_count(findings)

    print(Color.bold("What this means"))
    print()

    if findings.label_count is not None and findings.inventory_count is not None:
        if findings.label_count != findings.inventory_count:
            _print_wrapped(
                f"{Color.yellow('⚠')} The label and the inventory file disagree, so the label may be stale "
                "or the inventory file malformed. This is a problem with the submitted data itself.",
                2,
            )
        else:
            _print_wrapped(
                f"{Color.green('✓')} The label and the downloaded inventory file agree on "
                f"{findings.inventory_count:,} members, so the submitted data is internally consistent.",
                2,
            )
        print()

    if findings.members_count is None or expected is None:
        _print_wrapped("Not enough data to compare the API with the expected member count.", 2)
        print()
        return

    if findings.members_count == expected:
        _print_wrapped(
            f"{Color.green('✓')} The API /members total matches the {expected_name} ({expected:,}).", 2
        )
        print()
        return

    if findings.members_count > expected:
        _print_wrapped(
            f"{Color.yellow('⚠')} The API reports {findings.members_count - expected:,} more members than "
            f"the {expected_name}. Secondary members, duplicate registrations, or a stale "
            f"{expected_name} could explain this.",
            2,
        )
        print()
        return

    shortfall = expected - findings.members_count
    _print_wrapped(
        f"{Color.red('✗')} The API is missing {shortfall:,} of the {expected:,} members listed in the "
        f"{expected_name}.",
        2,
    )
    print()

    api_visible = findings.registry_api_count
    if api_visible is not None:
        if api_visible >= expected:
            _print_wrapped(
                f"The registry wildcard matches {api_visible:,} API-visible products, enough to cover the "
                f"expected count of {expected:,}, but that approximate count does not prove this collection's "
                "products are loaded. Use --diff to verify the exact LIDVIDs before treating this as a members-relationship gap.",
                2,
            )
        else:
            missing = expected - api_visible
            extra = ""
            if findings.registry_non_archived_count:
                extra = (
                    f" {findings.registry_non_archived_count:,} loaded products are not archived/certified "
                    "and are hidden from the API for that reason."
                )
            _print_wrapped(
                f"The registry holds only {api_visible:,} API-visible products, {missing:,} fewer than "
                f"the {expected_name}, so some products are not loaded or not visible.{extra} Rerun "
                "with --diff to list the specific LIDVIDs.",
                2,
            )
        print()

    _print_harvest_analysis(findings, shortfall)


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    """Build and return the parsed command-line arguments.

    Returns:
        Parsed argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description="Audit a PDS4 collection for product count discrepancies and bad file references",
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
        "--check-files",
        action="store_true",
        help=(
            "Page through the collection and every member product and report "
            "file_refs that are not absolute URLs and md5_checksums that are "
            "not MD5 digests. Does not need registry access, but takes a long "
            "time for large collections."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Write all output files to DIR (created if absent). "
            "summary.csv is written at the root; each collection's diff and "
            "file_problems CSVs go in a subdirectory named after the collection. "
            "Without --diff or --check-files, only summary.csv is written."
        ),
    )
    parser.add_argument(
        "--verbose-report",
        action="store_true",
        help=(
            "After the count report, print a plain-language explanation of each "
            "source. When the API /members count is short, also compare the "
            "collection's harvest time with the latest member product's harvest "
            "time to indicate whether sweepers still need to run or the "
            "collection must be re-harvested. The latest-member time requires "
            "registry access."
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
    "files_examined",
    "file_problems",
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
    label_count, file_ref, collection_harvest = get_label_count(session, args.api_base, lidvid, args.timeout)

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

    # Harvest times only matter for the verbose report, so skip the extra query otherwise.
    latest_product_lidvid: str | None = None
    latest_product_harvest: str | None = None
    if args.verbose_report and registry_auth is not None:
        logger.info("Querying registry (latest member harvest time) …")
        latest_product_lidvid, latest_product_harvest = get_latest_member_harvest(
            collection_lid, args.wildcard, args.registry_index, registry_auth, args.timeout
        )

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

    if args.verbose_report:
        print_verbose_report(
            AuditFindings(
                lidvid=lidvid,
                registry_queried=registry_auth is not None,
                registry_pattern=args.wildcard or f"{collection_lid}:*",
                label_count=label_count,
                inventory_url=file_ref,
                inventory_count=inventory_count,
                members_count=members_count,
                registry_raw_count=registry_raw_count,
                registry_superseded_count=registry_superseded_count,
                registry_non_archived_count=registry_non_archived_count,
                registry_api_count=registry_api_count,
                collection_harvest=collection_harvest,
                latest_product_harvest=latest_product_harvest,
                latest_product_lidvid=latest_product_lidvid,
            )
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

    # Optional file path and checksum check
    files_examined: int | None = None
    file_problems: int | None = None

    if args.check_files:
        logger.info("Checking file paths and checksums of all members (this can take a while) …")
        scan = scan_collection_files(session, args.api_base, lidvid, args.timeout)
        file_problems = print_file_report(scan, _diff_output_for(args.output_dir, collection_lid))
        files_examined = scan.examined if scan is not None else None

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
        "files_examined": files_examined,
        "file_problems": file_problems,
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
