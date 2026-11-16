"""Read-only OpenSearch access for the unprocessed product audit.

This is the only module that talks to the registry (AWS OpenSearch Serverless, signed requests). It
issues ``_search`` and ``_count`` POSTs only. Query bodies are built by small pure functions so they
can be tested without a network.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.parse
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sequence
from datetime import datetime
from datetime import timezone
from typing import TYPE_CHECKING

import requests

from unprocessed_audit.model import AGGREGATE_CLASSES
from unprocessed_audit.model import API_VISIBLE_ARCHIVE_STATUSES
from unprocessed_audit.model import ARCHIVE_STATUS_FIELD
from unprocessed_audit.model import CONCRETE_NODE_NAMES
from unprocessed_audit.model import DATA_FILE_REF_FIELD
from unprocessed_audit.model import HARVEST_FIELD
from unprocessed_audit.model import LEGACY_INDEX
from unprocessed_audit.model import REFS_FIELD
from unprocessed_audit.model import REFS_SUFFIX
from unprocessed_audit.model import REGISTRY_SUFFIX
from unprocessed_audit.model import STAMP_FIELD
from unprocessed_audit.model import SUPERSEDED_FIELD
from unprocessed_audit.model import TENANT_NODES
from unprocessed_audit.model import Candidate
from unprocessed_audit.model import Collection
from unprocessed_audit.model import RefsCoverage
from unprocessed_audit.model import RegistryQueryError

if TYPE_CHECKING:
    from opensearchpy import RequestsAWSV4SignerAuth

logger = logging.getLogger(__name__)

MAX_PAGE_SIZE = 10000
"""AOSS result window; a larger ``size`` silently returns garbage."""
BUNDLE_COLLECTION_REF_FIELD = "ref_lid_collection"
"""Bundle field listing the LIDs of its collections (unverified on the registry index)."""
REFS_PRODUCT_BATCH = 1000
BUNDLE_LID_BATCH = 500
MAX_RETRIES = 3
AUTH_MAX_AGE_SECONDS = 45 * 60
"""Credentials issued at login last about an hour; renew them well before that."""
_AUTH_REJECTED_STATUSES = (401, 403)
"""Retries after the first attempt for HTTP 429/5xx and connection failures."""

_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_INDEX_PATH_SAFE = "/,*-"
_ERROR_BODY_LIMIT = 500

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


# ── authentication and endpoint ───────────────────────────────────────────────


def make_registry_auth() -> RequestsAWSV4SignerAuth:
    """Authenticate to AOSS via Cognito and return a signed auth object.

    Reads credentials from the ``REQUEST_SIGNER_*`` environment variables.

    Returns:
        A ``RequestsAWSV4SignerAuth`` instance ready for use in HTTP calls.

    Raises:
        RegistryQueryError: If the registry client packages are missing, environment variables
            are unset, or Cognito authentication fails.
    """
    try:
        import botocore.exceptions
        from opensearchpy import RequestsAWSV4SignerAuth
        from pds.aossrequestsigner.credentials import get_credentials_via_cognito_userpass_flow
    except ImportError as exc:
        raise RegistryQueryError(
            f"Registry client packages not installed: {exc}. Run: pip install -r scripts/requirements.txt"
        ) from exc

    missing = [name for name in _REGISTRY_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise RegistryQueryError(f"Missing required environment variables: {', '.join(missing)}")

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
        raise RegistryQueryError(f"Cognito authentication failed: {exc}") from exc

    return RequestsAWSV4SignerAuth(credentials, region, "aoss")


def registry_endpoint_from_env() -> str:
    """Return the AOSS endpoint from ``REQUEST_SIGNER_AOSS_ENDPOINT``.

    Raises:
        RegistryQueryError: If the variable is unset or empty.
    """
    endpoint = os.environ.get("REQUEST_SIGNER_AOSS_ENDPOINT")
    if not endpoint:
        raise RegistryQueryError("REQUEST_SIGNER_AOSS_ENDPOINT is not set")
    return endpoint


# ── index names ───────────────────────────────────────────────────────────────


def registry_index(nodes: Sequence[str] | None) -> str:
    """Return the index expression for registry products.

    Args:
        nodes: Node names, or ``None`` for every node. The wildcard also matches the legacy Solr
            mirror, which AOSS cannot exclude in the index path; callers skip it by index name.

    Returns:
        A comma-separated index expression.
    """
    if not nodes:
        return f"*{REGISTRY_SUFFIX}"
    return ",".join(f"{node}{REGISTRY_SUFFIX}" for node in nodes)


def refs_index(nodes: Sequence[str] | None) -> str:
    """Return the index expression for ``registry-refs`` documents.

    Args:
        nodes: Node names, or ``None`` for every node.

    Returns:
        A comma-separated index expression.
    """
    if not nodes:
        return f"*{REFS_SUFFIX}"
    return ",".join(f"{node}{REFS_SUFFIX}" for node in nodes)


_AOSS_INDEX_PATTERN = re.compile(r"^(?:.*::SEARCH::)?(?P<name>.+?)(?::\d+)?$")
"""AOSS reports ``_index`` as ``<account>::<collection id>::SEARCH::<index name>:<n>``."""


def index_name_of(raw_index: str) -> str:
    """Return the plain index name from an ``_index`` value (``...::SEARCH::atm-registry:0`` -> ``atm-registry``).

    Values that are already plain index names are returned unchanged.
    """
    match = _AOSS_INDEX_PATTERN.match(raw_index)
    return match.group("name") if match else raw_index


def node_of_index(index_name: str) -> str:
    """Return the node name for a registry index (``atm-registry`` -> ``atm``).

    Accepts either a plain index name or the AOSS ``_index`` form. Names without the ``-registry``
    suffix are returned unchanged.
    """
    return index_name_of(index_name).removesuffix(REGISTRY_SUFFIX)


# ── client ────────────────────────────────────────────────────────────────────


class RegistryClient:
    """Signed, read-only OpenSearch client with retry on throttling and server errors.

    Attributes:
        backoff_seconds: Base delay before a retry; doubles on each subsequent retry.
    """

    def __init__(
        self,
        auth: RequestsAWSV4SignerAuth,
        endpoint: str,
        timeout: int = 60,
        refresh_auth: Callable[[], RequestsAWSV4SignerAuth] | None = None,
        auth_max_age_seconds: float = AUTH_MAX_AGE_SECONDS,
    ) -> None:
        """Create a client.

        Args:
            auth: Signed auth object from ``make_registry_auth``.
            endpoint: AOSS endpoint URL.
            timeout: Per-request timeout in seconds.
            refresh_auth: Returns fresh credentials. The credentials issued at login expire after about an
                hour, so a long audit must renew them. They are renewed when older than ``auth_max_age_seconds``
                and once more when the service rejects a request with HTTP 401 or 403.
            auth_max_age_seconds: Age after which the credentials are renewed before the next request.
        """
        self._auth = auth
        self._endpoint = endpoint.rstrip("/")
        self._timeout = timeout
        self._refresh_auth = refresh_auth
        self._auth_max_age_seconds = auth_max_age_seconds
        self._auth_obtained = time.monotonic()
        self.backoff_seconds = 1.0

    def _renew_auth(self, reason: str) -> None:
        """Replace the credentials with fresh ones. Does nothing when no ``refresh_auth`` was given."""
        if self._refresh_auth is None:
            return
        logger.info("Renewing the registry credentials (%s)", reason)
        self._auth = self._refresh_auth()
        self._auth_obtained = time.monotonic()

    def search(self, index: str, body: dict) -> dict:
        """POST ``<endpoint>/<index>/_search`` and return the parsed response.

        Args:
            index: Index expression, e.g. ``atm-registry``.
            body: OpenSearch DSL body.

        Returns:
            Parsed JSON response.

        Raises:
            RegistryQueryError: On HTTP, connection or JSON errors after retries.
        """
        return self._post(index, "_search", body)

    def count(self, index: str, body: dict) -> int:
        """POST ``<endpoint>/<index>/_count`` and return the document count.

        Args:
            index: Index expression.
            body: OpenSearch DSL body (``query`` only).

        Returns:
            The ``count`` value of the response.

        Raises:
            RegistryQueryError: On HTTP, connection or JSON errors, or if no count is returned.
        """
        data = self._post(index, "_count", body)
        value = data.get("count")
        if not isinstance(value, int):
            raise RegistryQueryError(f"Unexpected _count response from {index}: {str(data)[:_ERROR_BODY_LIMIT]}")
        return value

    def get_mapping(self, index: str) -> dict:
        """GET ``<endpoint>/<index>/_mapping`` and return the parsed response.

        Args:
            index: Index or alias name, e.g. ``atm-registry``.

        Returns:
            Parsed JSON response, keyed by concrete index name.

        Raises:
            RegistryQueryError: On HTTP, connection or JSON errors after retries.
        """
        return self._request("GET", index, "_mapping", None)

    def _post(self, index: str, operation: str, body: dict) -> dict:
        return self._request("POST", index, operation, json.dumps(body))

    def _request(self, method: str, index: str, operation: str, payload: str | None) -> dict:
        url = f"{self._endpoint}/{urllib.parse.quote(index, safe=_INDEX_PATH_SAFE)}/{operation}"
        send = requests.post if method == "POST" else requests.get
        last_error = ""
        renewed_after_rejection = False
        if self._refresh_auth is not None and time.monotonic() - self._auth_obtained > self._auth_max_age_seconds:
            self._renew_auth("older than the maximum age")
        for attempt in range(MAX_RETRIES + 1):
            if attempt:
                delay = self.backoff_seconds * 2 ** (attempt - 1)
                logger.warning(
                    "Retrying %s %s in %.1fs (%d/%d): %s", operation, index, delay, attempt, MAX_RETRIES, last_error
                )
                time.sleep(delay)
            try:
                resp = send(
                    url=url,
                    data=payload,
                    auth=self._auth,
                    headers={"Content-Type": "application/json"},
                    timeout=self._timeout,
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
                last_error = str(exc)
                continue
            except requests.exceptions.RequestException as exc:
                raise RegistryQueryError(f"Registry request to {index}/{operation} failed: {exc}") from exc

            if resp.status_code in _RETRY_STATUSES:
                last_error = f"HTTP {resp.status_code}: {resp.text[:_ERROR_BODY_LIMIT]}"
                continue
            if resp.status_code in _AUTH_REJECTED_STATUSES and self._refresh_auth and not renewed_after_rejection:
                # Expired credentials look like a plain 403. Renew once; a genuine permission error fails below.
                renewed_after_rejection = True
                last_error = f"HTTP {resp.status_code}: {resp.text[:_ERROR_BODY_LIMIT]}"
                self._renew_auth(f"the service answered HTTP {resp.status_code}")
                continue
            if resp.status_code >= 400:
                raise RegistryQueryError(
                    f"Registry request to {index}/{operation} failed: HTTP {resp.status_code}: "
                    f"{resp.text[:_ERROR_BODY_LIMIT]}"
                )
            try:
                data = resp.json()
            except ValueError as exc:
                raise RegistryQueryError(f"Registry returned invalid JSON for {index}/{operation}: {exc}") from exc
            if not isinstance(data, dict):
                raise RegistryQueryError(f"Registry returned a non-object response for {index}/{operation}")
            return data
        raise RegistryQueryError(
            f"Registry request to {index}/{operation} failed after {MAX_RETRIES} retries: {last_error}"
        )


# ── query builders ────────────────────────────────────────────────────────────


def api_visible_clauses() -> dict:
    """Return the ``bool`` pieces that select API-visible (non-superseded, archived/certified) products."""
    return {
        "filter": [{"terms": {ARCHIVE_STATUS_FIELD: list(API_VISIBLE_ARCHIVE_STATUSES)}}],
        "must_not": [{"exists": {"field": SUPERSEDED_FIELD}}],
    }


def collections_query() -> dict:
    """Return the query body selecting every ``Product_Collection`` with an API-visible archive status.

    Superseded collection versions are included: products of an older collection version stay
    API-visible, and leaving the version out would attribute them to a newer one.
    """
    return {
        "query": {
            "bool": {
                "filter": [
                    {"terms": {ARCHIVE_STATUS_FIELD: list(API_VISIBLE_ARCHIVE_STATUSES)}},
                    {"term": {"product_class": "Product_Collection"}},
                ]
            }
        }
    }


def candidate_query(ancestry_version: int) -> dict:
    """Return the query body selecting non-aggregate products that lack current ancestry.

    A product matches when any of these holds: it has no stamp (A); it has no non-empty
    ``ancestor_refs`` (B); it has a stamp other than ``ancestry_version`` (C). The stamp is a
    ``keyword`` field, so it is compared for equality only.

    Args:
        ancestry_version: The current ancestry version.
    """
    clauses = api_visible_clauses()
    clauses["must_not"].append({"terms": {"product_class": list(AGGREGATE_CLASSES)}})
    clauses["should"] = [
        {"bool": {"must_not": [{"exists": {"field": STAMP_FIELD}}]}},
        {"bool": {"must_not": [{"exists": {"field": REFS_FIELD}}]}},
        {
            "bool": {
                "filter": [{"exists": {"field": STAMP_FIELD}}],
                "must_not": [{"term": {STAMP_FIELD: str(ancestry_version)}}],
            }
        },
    ]
    clauses["minimum_should_match"] = 1
    return {"query": {"bool": clauses}}


def _members_query(collection_lid: str, ancestry_version: int | None) -> dict:
    clauses = api_visible_clauses()
    clauses["filter"].append({"wildcard": {"lid": {"value": f"{collection_lid}:*", "case_insensitive": True}}})
    if ancestry_version is not None:
        clauses["filter"].append({"term": {STAMP_FIELD: str(ancestry_version)}})
        clauses["filter"].append({"exists": {"field": REFS_FIELD}})
    return {"query": {"bool": clauses}}


# ── field parsing ─────────────────────────────────────────────────────────────


def _scalar(raw: object) -> str | None:
    """Return the first non-empty value of a scalar-or-list field as a string."""
    if isinstance(raw, list):
        for item in raw:
            text = _scalar(item)
            if text is not None:
                return text
        return None
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _string_list(raw: object) -> list[str]:
    """Return a scalar-or-list field as a list of non-empty strings."""
    if raw is None:
        return []
    items = raw if isinstance(raw, list) else [raw]
    values = (_scalar(item) for item in items)
    return [value for value in values if value is not None]


def _parse_timestamp(raw: object) -> datetime | None:
    """Parse an ISO 8601 timestamp into an aware datetime (naive values are UTC); ``None`` if bad."""
    text = _scalar(raw)
    if text is None:
        return None
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _lid_of(lidvid: str) -> str:
    return lidvid.split("::", 1)[0]


# ── paging ────────────────────────────────────────────────────────────────────


def _page_hits(client: RegistryClient, index: str, body: dict, page_size: int) -> Iterator[list[dict]]:
    """Yield pages of hits, paging with ``search_after`` on ``_id``."""
    base = {**body, "size": page_size, "sort": [{"_id": "asc"}]}
    query = base
    while True:
        hits = client.search(index, query).get("hits", {}).get("hits", [])
        if hits:
            yield hits
        if len(hits) < page_size:
            return
        last_sort = hits[-1].get("sort")
        if not last_sort:
            return
        query = {**base, "search_after": last_sort}


# ── queries ───────────────────────────────────────────────────────────────────


def _is_legacy_index(index_name: str) -> bool:
    """Say whether ``index_name`` is the legacy Solr mirror, which ``*-registry`` also matches."""
    return index_name_of(index_name) == LEGACY_INDEX


def discover_nodes(client: RegistryClient) -> list[str]:
    """Return the sorted node names found in the registry indices.

    Uses a size-0 terms aggregation on ``_index``.

    Raises:
        RegistryQueryError: If the aggregation fails or finds nothing. Pass ``--node`` to avoid
            discovery.
    """
    body = {"size": 0, "aggs": {"indices": {"terms": {"field": "_index", "size": 1000}}}}
    try:
        data = client.search(registry_index(None), body)
    except RegistryQueryError as exc:
        raise RegistryQueryError(
            f"Could not discover registry nodes with a terms aggregation on _index ({exc}). "
            "Name the nodes explicitly with the --node option."
        ) from exc
    buckets = data.get("aggregations", {}).get("indices", {}).get("buckets", [])
    nodes = sorted(
        {
            node_of_index(str(bucket["key"]))
            for bucket in buckets
            if "key" in bucket and not _is_legacy_index(str(bucket["key"]))
        }
    )
    if not nodes:
        raise RegistryQueryError(
            "Node discovery found no registry indices (terms aggregation on _index returned no buckets). "
            "Name the nodes explicitly with the --node option."
        )
    return nodes


def split_tenant_nodes(
    nodes: Sequence[str], tenants: Sequence[str] = TENANT_NODES
) -> tuple[list[str], list[str]]:
    """Separate the tenant nodes from index prefixes that are not one.

    An index whose prefix is not a tenant node (a personal, temporary or test copy such as
    ``<name>-registry``) is possibly stale. It is reported for cleanup instead of being audited.

    Args:
        nodes: Node names, as returned by ``discover_nodes``.
        tenants: Tenant node names. A concrete name in ``CONCRETE_NODE_NAMES`` counts as its tenant.

    Returns:
        ``(tenant nodes, possibly stale nodes)``, each in the order given.
    """
    recognised = set(tenants)
    tenant = [n for n in nodes if CONCRETE_NODE_NAMES.get(n, n) in recognised]
    stale = [n for n in nodes if n not in tenant]
    return tenant, stale


def iter_collections(client: RegistryClient, nodes: Sequence[str] | None) -> Iterator[Collection]:
    """Yield every API-visible collection.

    Args:
        client: Registry client.
        nodes: Nodes to limit to, or ``None`` for all.
    """
    body = {
        "_source": ["lidvid", "lid", STAMP_FIELD, REFS_FIELD, HARVEST_FIELD, SUPERSEDED_FIELD, DATA_FILE_REF_FIELD],
        **collections_query(),
    }
    for hits in _page_hits(client, registry_index(nodes), body, MAX_PAGE_SIZE):
        for hit in hits:
            if _is_legacy_index(str(hit.get("_index", ""))):
                continue
            source = hit.get("_source", {})
            lidvid = _scalar(source.get("lidvid"))
            if lidvid is None:
                logger.debug("Collection hit without lidvid: %s", hit.get("_id"))
                continue
            yield Collection(
                lidvid=lidvid,
                lid=_scalar(source.get("lid")) or _lid_of(lidvid),
                node=node_of_index(str(hit.get("_index", ""))),
                stamp=_scalar(source.get(STAMP_FIELD)),
                ancestor_refs=_string_list(source.get(REFS_FIELD)),
                harvest=_parse_timestamp(source.get(HARVEST_FIELD)),
                superseded_by=_scalar(source.get(SUPERSEDED_FIELD)),
                inventory_url=_scalar(source.get(DATA_FILE_REF_FIELD)),
            )


def _candidate_from_hit(hit: dict) -> Candidate | None:
    source = hit.get("_source", {})
    lidvid = _scalar(source.get("lidvid"))
    if lidvid is None:
        logger.debug("Candidate hit without lidvid: %s", hit.get("_id"))
        return None
    # The superseded marker is read here rather than filtered in the query, because on some indices
    # (the ATM registry) the field is returned in ``_source`` but cannot be searched, so a query on it matches nothing.
    if _scalar(source.get(SUPERSEDED_FIELD)):
        return None
    return Candidate(
        lidvid=lidvid,
        lid=_scalar(source.get("lid")) or _lid_of(lidvid),
        product_class=_scalar(source.get("product_class")) or "",
        node=node_of_index(str(hit.get("_index", ""))),
        stamp=_scalar(source.get(STAMP_FIELD)),
        has_ancestor_refs=bool(_string_list(source.get(REFS_FIELD))),
        harvest=_parse_timestamp(source.get(HARVEST_FIELD)),
    )


def iter_candidate_pages(
    client: RegistryClient,
    nodes: Sequence[str] | None,
    ancestry_version: int,
    page_size: int = MAX_PAGE_SIZE,
    max_products: int | None = None,
) -> Iterator[list[Candidate]]:
    """Yield pages of non-aggregate products that lack current ancestry.

    Each node index is paged on its own so that equal ``_id`` values in different indices cannot
    cause documents to be skipped.

    Args:
        client: Registry client.
        nodes: Nodes to limit to, or ``None`` to discover them.
        ancestry_version: Current ancestry version.
        page_size: Hits per request; at most 10,000.
        max_products: Stop after this many candidates across all nodes.

    Raises:
        ValueError: If ``page_size`` is not between 1 and 10,000.
    """
    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE}, got {page_size}")
    return _candidate_pages(client, nodes, ancestry_version, page_size, max_products)


def _candidate_pages(
    client: RegistryClient,
    nodes: Sequence[str] | None,
    ancestry_version: int,
    page_size: int,
    max_products: int | None,
) -> Iterator[list[Candidate]]:
    node_names = list(nodes) if nodes else discover_nodes(client)
    body = {
        "_source": ["lidvid", "lid", "product_class", STAMP_FIELD, REFS_FIELD, HARVEST_FIELD, SUPERSEDED_FIELD],
        **candidate_query(ancestry_version),
    }
    total = 0
    for node in node_names:
        if max_products is not None and total >= max_products:
            return
        for hits in _page_hits(client, registry_index([node]), body, page_size):
            page = [candidate for candidate in map(_candidate_from_hit, hits) if candidate is not None]
            if max_products is not None:
                page = page[: max_products - total]
            total += len(page)
            if page:
                yield page
            if max_products is not None and total >= max_products:
                return


def lookup_refs(client: RegistryClient, product_lidvids: Sequence[str], nodes: Sequence[str] | None) -> dict[str, str]:
    """Find the collection that lists each product in ``registry-refs``.

    Args:
        client: Registry client.
        product_lidvids: Product LIDVIDs to look up.
        nodes: Nodes to limit to, or ``None`` for all.

    Returns:
        ``{product_lidvid: collection_lidvid}`` for the requested products that appear in refs.
    """
    result: dict[str, str] = {}
    if not product_lidvids:
        return result
    index = refs_index(nodes)
    for start in range(0, len(product_lidvids), REFS_PRODUCT_BATCH):
        batch = list(product_lidvids[start : start + REFS_PRODUCT_BATCH])
        wanted = set(batch)
        body = {
            "_source": ["collection_lidvid", "product_lidvid"],
            "query": {"bool": {"filter": [{"terms": {"product_lidvid": batch}}]}},
        }
        for hits in _page_hits(client, index, body, MAX_PAGE_SIZE):
            for hit in hits:
                source = hit.get("_source", {})
                collection_lidvid = _scalar(source.get("collection_lidvid"))
                if collection_lidvid is None:
                    continue
                for product in _string_list(source.get("product_lidvid")):
                    if product not in wanted:
                        continue
                    if product in result:
                        if result[product] != collection_lidvid:
                            logger.debug(
                                "%s is listed under several collections; keeping %s, ignoring %s",
                                product,
                                result[product],
                                collection_lidvid,
                            )
                        continue
                    result[product] = collection_lidvid
    return result


def lookup_refs_by_lid(
    client: RegistryClient, product_lids: Sequence[str], nodes: Sequence[str] | None
) -> dict[str, list[tuple[str, str | None]]]:
    """Find the versions under which ``registry-refs`` lists each product LID, and for which collection.

    Refs are written from a collection's inventory. A refs document of one collection version that lists a
    different version of the product says nothing about another version of the collection, so each listing
    is returned with the collection it comes from.

    Args:
        client: Registry client.
        product_lids: Product LIDs (without version) to look up.
        nodes: Nodes to limit to, or ``None`` for all.

    Returns:
        ``{product_lid: [(listed_product_lidvid, collection_lidvid), ...]}`` for LIDs that refs list under some
        version; ``collection_lidvid`` is ``None`` when the refs document names none. LIDs that refs list only as
        a bare LID, or not at all, are omitted.
    """
    result: dict[str, list[tuple[str, str | None]]] = {}
    if not product_lids:
        return result
    index = refs_index(nodes)
    for start in range(0, len(product_lids), REFS_PRODUCT_BATCH):
        batch = list(product_lids[start : start + REFS_PRODUCT_BATCH])
        wanted = set(batch)
        body = {
            "_source": ["product_lidvid", "collection_lidvid"],
            "query": {"bool": {"filter": [{"terms": {"product_lid": batch}}]}},
        }
        for hits in _page_hits(client, index, body, MAX_PAGE_SIZE):
            for hit in hits:
                source = hit.get("_source", {})
                collection_lidvid = _scalar(source.get("collection_lidvid"))
                for listed in _string_list(source.get("product_lidvid")):
                    lid = _lid_of(listed)
                    if lid in wanted:
                        entry = (listed, collection_lidvid)
                        found = result.setdefault(lid, [])
                        if entry not in found:
                            found.append(entry)
    return result


def find_bundles(
    client: RegistryClient, collection_lids: Sequence[str], nodes: Sequence[str] | None
) -> dict[str, list[str]]:
    """Find the API-visible bundles that reference each collection LID.

    Args:
        client: Registry client.
        collection_lids: Collection LIDs to look up.
        nodes: Nodes to limit to, or ``None`` for all.

    Returns:
        ``{collection_lid: [bundle_lidvid, ...]}``; LIDs with no bundle are omitted.
    """
    result: dict[str, list[str]] = {}
    if not collection_lids:
        return result
    index = registry_index(nodes)
    for start in range(0, len(collection_lids), BUNDLE_LID_BATCH):
        batch = list(collection_lids[start : start + BUNDLE_LID_BATCH])
        wanted = {lid.lower(): lid for lid in batch}
        clauses = api_visible_clauses()
        clauses["filter"].append({"term": {"product_class": "Product_Bundle"}})
        clauses["filter"].append({"terms": {BUNDLE_COLLECTION_REF_FIELD: batch}})
        body = {"_source": ["lidvid", BUNDLE_COLLECTION_REF_FIELD], "query": {"bool": clauses}}
        for hits in _page_hits(client, index, body, MAX_PAGE_SIZE):
            for hit in hits:
                source = hit.get("_source", {})
                bundle = _scalar(source.get("lidvid"))
                if bundle is None:
                    continue
                for ref in _string_list(source.get(BUNDLE_COLLECTION_REF_FIELD)):
                    lid = wanted.get(ref.lower())
                    if lid is None:
                        continue
                    bundles = result.setdefault(lid, [])
                    if bundle not in bundles:
                        bundles.append(bundle)
    return result


def get_refs_coverage(
    client: RegistryClient, collection: Collection, nodes: Sequence[str] | None, ancestry_version: int
) -> RefsCoverage:
    """Compare refs entries with the members of one collection.

    Args:
        client: Registry client.
        collection: Collection to examine.
        nodes: Nodes to limit to, or ``None`` for all.
        ancestry_version: Current ancestry version.

    Returns:
        The number of refs entries, API-visible members found by LID prefix, and members that
        carry current ancestry.
    """
    refs_body = {
        "size": 0,
        "query": {"bool": {"filter": [{"term": {"collection_lidvid": collection.lidvid}}]}},
        "aggs": {"refs": {"value_count": {"field": "product_lidvid"}}},
    }
    data = client.search(refs_index(nodes), refs_body)
    try:
        refs_count = int(data["aggregations"]["refs"]["value"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RegistryQueryError(
            f"Unexpected refs aggregation response for {collection.lidvid}: {str(data)[:_ERROR_BODY_LIMIT]}"
        ) from exc
    index = registry_index(nodes)
    member_count = client.count(index, _members_query(collection.lid, None))
    stamped_member_count = client.count(index, _members_query(collection.lid, ancestry_version))
    return RefsCoverage(refs_count=refs_count, member_count=member_count, stamped_member_count=stamped_member_count)
