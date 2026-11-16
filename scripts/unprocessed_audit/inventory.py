"""Collection inventory tables: download them and index the LIDVIDs they list.

``registry-refs`` documents are written from the collection inventory when the collection is
harvested, so they can be older than the inventory the data provider serves today. The audit reads the
current inventory of a collection, only when it needs to, to tell products the inventory lists from
products it does not list.
"""

from __future__ import annotations

import csv
import hashlib
import logging
from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from unprocessed_audit.model import Collection

logger = logging.getLogger(__name__)

_MEMBER_STATUSES = ("P", "S")
_CHUNK_SIZE = 1024 * 1024
"""Bytes read per chunk; the 512-byte default of ``iter_lines`` is far too slow for large inventories."""
DEFAULT_CACHE_SIZE = 2
"""Inventories kept in memory at once. Candidates arrive sorted by LIDVID, so a collection's products are
contiguous and a small cache is enough."""


class InventoryError(Exception):
    """An inventory table could not be downloaded or read."""


@dataclass
class InventoryIndex:
    """The LIDVIDs a collection inventory lists.

    Attributes:
        lidvids: Every listed LIDVID.
        listed_by_lid: One listed LIDVID per product LID, to find the version the inventory names.
        bare_lids: Members listed by LID only, which stand for every version.
    """

    lidvids: set[str] = field(default_factory=set)
    listed_by_lid: dict[str, str] = field(default_factory=dict)
    bare_lids: set[str] = field(default_factory=set)

    def lists(self, lidvid: str, lid: str) -> bool:
        """Say whether the inventory lists this exact product, by LIDVID or as a bare LID."""
        return lidvid in self.lidvids or lid in self.bare_lids

    def other_version(self, lid: str, lidvid: str) -> str | None:
        """Return the LIDVID the inventory lists for ``lid`` when it is not ``lidvid``, else ``None``."""
        listed = self.listed_by_lid.get(lid)
        return listed if listed is not None and listed != lidvid else None


def parse_inventory(lines: Iterable[str]) -> InventoryIndex:
    """Index the rows of a PDS4 inventory table.

    Rows are ``<member status>,<LIDVID or LID>``. A first row that does not start with ``P`` or ``S``
    is a header and is skipped.

    Args:
        lines: Lines of the CSV table.

    Returns:
        The index of what the table lists.
    """
    index = InventoryIndex()
    first = True
    for row in csv.reader(lines):
        if not any(cell.strip() for cell in row):
            continue
        if first:
            first = False
            if row[0].strip().upper() not in _MEMBER_STATUSES:
                continue
        if len(row) < 2:
            continue
        value = row[1].strip()
        if "::" in value:
            index.lidvids.add(value)
            index.listed_by_lid.setdefault(value.split("::", 1)[0], value)
        elif value:
            index.bare_lids.add(value)
    return index


def make_session() -> requests.Session:
    """Build a session that retries throttling and server errors."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers["User-Agent"] = "pds-registry-audit/1.0"
    return session


def cached_inventory_path(cache_dir: Path, url: str) -> Path:
    """Return the file an inventory is kept in under ``cache_dir`` (named from a hash of its URL)."""
    return cache_dir / (hashlib.sha1(url.encode("utf-8")).hexdigest() + ".csv")  # noqa: S324 - a file name, not security


def download_inventory_file(session: requests.Session, url: str, dest: Path, timeout: int) -> None:
    """Download an inventory table to ``dest``, through a temporary name so a failure leaves no partial file.

    Args:
        session: HTTP session.
        url: Inventory table URL.
        dest: Destination file; parent directories are created.
        timeout: Per-request timeout in seconds.

    Raises:
        InventoryError: If the download or the write fails.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    try:
        with session.get(url, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            with open(partial, "wb") as f:
                for chunk in resp.iter_content(chunk_size=_CHUNK_SIZE):
                    f.write(chunk)
        partial.replace(dest)
    except (requests.exceptions.RequestException, OSError) as exc:
        partial.unlink(missing_ok=True)
        raise InventoryError(f"Could not read the inventory at {url}: {exc}") from exc


def read_inventory_file(path: Path) -> InventoryIndex:
    """Index an inventory table stored on disk."""
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            return parse_inventory(f)
    except OSError as exc:
        raise InventoryError(f"Could not read the cached inventory {path}: {exc}") from exc


def fetch_inventory(session: requests.Session, url: str, timeout: int) -> InventoryIndex:
    """Download an inventory table and index it, without holding the whole file in memory.

    Args:
        session: HTTP session.
        url: Inventory table URL.
        timeout: Per-request timeout in seconds.

    Returns:
        The index of what the table lists.

    Raises:
        InventoryError: If the download fails.
    """
    try:
        with session.get(url, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return parse_inventory(resp.iter_lines(chunk_size=_CHUNK_SIZE, decode_unicode=True))
    except (requests.exceptions.RequestException, UnicodeDecodeError) as exc:
        raise InventoryError(f"Could not read the inventory at {url}: {exc}") from exc


class InventoryCache:
    """Downloads each collection's inventory on first use and keeps a few in memory.

    Call it with a collection to get its ``InventoryIndex``, or ``None`` when the collection has no
    inventory URL or the download failed (a warning is logged once per collection).
    """

    def __init__(
        self,
        session: requests.Session,
        timeout: int,
        max_size: int = DEFAULT_CACHE_SIZE,
        cache_dir: Path | None = None,
    ) -> None:
        """Create the cache.

        Args:
            session: HTTP session.
            timeout: Per-request timeout in seconds.
            max_size: Inventories kept in memory at once; the least recently used is dropped first.
            cache_dir: When given, downloaded inventories are also kept in this directory and reused by later
                runs, which saves the slow downloads. A kept file is never refreshed: delete it to fetch it again.
        """
        self._session = session
        self._timeout = timeout
        self._cache_dir = cache_dir
        self._max_size = max_size
        self._entries: OrderedDict[str, InventoryIndex | None] = OrderedDict()
        self.downloads = 0

    def _load(self, collection: Collection) -> InventoryIndex:
        """Read the inventory from the disk cache when it is there, otherwise download it."""
        url = collection.inventory_url or ""
        if self._cache_dir is None:
            logger.info("Downloading the inventory of %s", collection.lidvid)
            self.downloads += 1
            return fetch_inventory(self._session, url, self._timeout)
        path = cached_inventory_path(self._cache_dir, url)
        if path.exists():
            logger.info("Reading the kept inventory of %s", collection.lidvid)
        else:
            logger.info("Downloading the inventory of %s", collection.lidvid)
            self.downloads += 1
            download_inventory_file(self._session, url, path, self._timeout)
        return read_inventory_file(path)

    def __call__(self, collection: Collection) -> InventoryIndex | None:
        """Return the inventory index of ``collection``, downloading it if it is not cached."""
        key = collection.lidvid
        if key in self._entries:
            self._entries.move_to_end(key)
            return self._entries[key]
        index: InventoryIndex | None = None
        if collection.inventory_url:
            try:
                index = self._load(collection)
            except InventoryError as exc:
                logger.warning("%s", exc)
        else:
            logger.warning("%s has no inventory URL; its products cannot be checked against the inventory", key)
        self._entries[key] = index
        while len(self._entries) > self._max_size:
            self._entries.popitem(last=False)
        return index
