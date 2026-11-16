#!/usr/bin/env python3
r"""Download the label and inventory of PDS4 collections so they can be re-harvested.

For each collection LIDVID the PDS Search API supplies the URL of the collection label and of its
inventory table, plus the checksums and record count the registry holds for them. This script
downloads both files, mirrored under the URL they came from, so that a single Harvest ``fileRef``
per host maps every local path back to the original URL:

    <output-dir>/files/<host>/<url path>   ->   <scheme>://<host>/<url path>

Re-harvesting a collection from these files rewrites the collection document (clearing its ancestry
stamp) and regenerates its ``registry-refs`` documents from the inventory, so the registry sweepers
process the collection and its members again.

Each downloaded file is checked against the registry:

  - MD5 of the label and of the inventory versus the checksums the registry holds. A mismatch means the
    data provider's file has changed since the collection was harvested.
  - Rows in the inventory versus ``pds:Inventory/pds:records`` in the label. A mismatch means the
    provider's own label and inventory disagree, which re-harvesting cannot fix.

Setup:
    pip install requests

Usage:
    python scripts/download_collection_files.py --output-dir DIR [LIDVID ...] [options]

Examples:
    # List the URLs and the Harvest fileRef prefixes without downloading anything
    python scripts/download_collection_files.py --list-only --output-dir ./reharvest/ \\
        --from-file anomalous_collections.txt

    # Download the label and inventory of every collection in a list
    python scripts/download_collection_files.py --output-dir ./reharvest/ \\
        --from-file anomalous_collections.txt

    # Take the collections straight from an unprocessed product audit
    python scripts/download_collection_files.py --output-dir ./reharvest/ \\
        --from-audit-csv ./audit_unprocessed/unprocessed_products.csv.gz

Options:
    --output-dir DIR      Directory for files/, manifest.csv and harvest_config_snippet.xml (required)
    --from-file FILE      Newline-separated collection LIDVIDs; blank lines and '#' comments are ignored
    --from-audit-csv FILE unprocessed_products.csv (or .csv.gz) from audit_unprocessed_products.py
    --rules RULE ...      With --from-audit-csv, the audit rules whose collections to take
                          (default: refs_missing reloaded_after_collection sweeper_miss stale_stamp)
    --list-only           Query the API and write the manifest and snippet, but download nothing
    --skip-existing       Keep files already on disk instead of downloading them again
    --node-name NAME      Use the copy registered under this node_name (for example PDS_ATM). Required for
                          collections registered under more than one node, because each node holds its own
                          copy of the files
    --api-base URL        PDS Search API base URL
    --timeout N           Per-request timeout in seconds (default: 60)
    --log-level LEVEL     debug, info, warn, warning (default: info)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import logging
import posixpath
import re
import sys
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_DEFAULT_API_BASE = "https://pds.mcp.nasa.gov/api/search/1"
_DEFAULT_RULES = ("refs_missing", "reloaded_after_collection", "sweeper_miss", "stale_stamp")
_CHUNK_SIZE = 1024 * 1024
_RECORDS_PATTERN = re.compile(r"<(?:\w+:)?Inventory\b[^>]*>.*?<(?:\w+:)?records>\s*(\d+)\s*</", re.DOTALL)

_LABEL_REF = "ops:Label_File_Info.ops:file_ref"
_LABEL_MD5 = "ops:Label_File_Info.ops:md5_checksum"
_INVENTORY_REF = "ops:Data_File_Info.ops:file_ref"
_INVENTORY_MD5 = "ops:Data_File_Info.ops:md5_checksum"
_RECORDS = "pds:Inventory.pds:records"
_HARVEST_TIME = "ops:Harvest_Info.ops:harvest_date_time"
_NODE_NAME = "ops:Harvest_Info.ops:node_name"
_API_FIELDS = [_LABEL_REF, _LABEL_MD5, _INVENTORY_REF, _INVENTORY_MD5, _RECORDS, _HARVEST_TIME]

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
}

_MANIFEST_FIELDS = [
    "collection_lidvid",
    "status",
    "node_name",
    "label_url",
    "inventory_url",
    "url_base",
    "label_and_inventory_same_dir",
    "local_label",
    "local_inventory",
    "label_md5_registry",
    "label_md5_local",
    "inventory_md5_registry",
    "inventory_md5_local",
    "md5_changed_since_harvest",
    "label_records_registry",
    "label_records_local",
    "inventory_rows",
    "records_match",
    "registry_harvest_date_time",
    "error",
]

logger = logging.getLogger(__name__)


class CollectionFilesError(Exception):
    """The API or the data provider did not give a usable label or inventory for a collection."""


@dataclass
class CollectionFiles:
    """What the registry holds about the files of one collection.

    Attributes:
        lidvid: Collection LIDVID.
        label_url: URL of the collection label.
        inventory_url: URL of the inventory table, ``None`` if the collection has none.
        label_md5: MD5 the registry holds for the label, if any.
        inventory_md5: MD5 the registry holds for the inventory, if any.
        label_records: ``pds:Inventory/pds:records`` from the label, if any.
        harvest_time: Time the collection was last harvested, if known.
        node_name: ``ops:Harvest_Info/ops:node_name`` of the registered copy, if known.
    """

    lidvid: str
    label_url: str
    inventory_url: str | None
    label_md5: str | None
    inventory_md5: str | None
    label_records: int | None
    harvest_time: str | None
    node_name: str | None = None


# ── HTTP ──────────────────────────────────────────────────────────────────────


def make_session() -> requests.Session:
    """Build a requests Session that retries throttling and server errors.

    Returns:
        A configured requests.Session.
    """
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers["User-Agent"] = "pds-collection-downloader/1.0"
    return session


def _first(value: object) -> str | None:
    """Return the first element of a list-valued API property, or the value itself, as text."""
    if isinstance(value, list):
        value = value[0] if value else None
    return None if value is None else str(value)


def fetch_collection_files(
    session: requests.Session, api_base: str, lidvid: str, timeout: int, node_name: str | None = None
) -> CollectionFiles:
    """Ask the API where a collection's label and inventory are.

    The same LIDVID can be registered under several nodes, each with its own copy of the files. The
    search endpoint returns every copy with its ``node_name``, whereas the single-product endpoint
    returns just one of them, so the search endpoint is used and the copy is chosen by node.

    Args:
        session: Shared HTTP session.
        api_base: PDS Search API base URL.
        lidvid: Collection LIDVID.
        timeout: Per-request timeout in seconds.
        node_name: ``ops:Harvest_Info/ops:node_name`` of the copy to use (for example ``PDS_ATM``).
            Required when the LIDVID is registered under more than one node.

    Returns:
        The collection's file URLs, checksums and record count.

    Raises:
        CollectionFilesError: If the request fails, the collection is not registered (under the
            requested node), it is registered under several nodes and none was requested, or the
            API gives no label URL.
    """
    params = {"q": f'lidvid eq "{lidvid}"', "fields": ",".join(_API_FIELDS + [_NODE_NAME]), "limit": 20}
    try:
        resp = session.get(f"{api_base}/products", params=params, timeout=timeout)
        resp.raise_for_status()
        products = resp.json().get("data", [])
    except (requests.exceptions.RequestException, ValueError) as exc:
        raise CollectionFilesError(f"API request for {lidvid} failed: {exc}") from exc

    if not products:
        raise CollectionFilesError(f"The API has no product {lidvid}")
    nodes = [_first(p.get("properties", {}).get(_NODE_NAME)) for p in products]
    if node_name is not None:
        matching = [p for p, n in zip(products, nodes) if n == node_name]
        if not matching:
            raise CollectionFilesError(f"{lidvid} is not registered under node {node_name} (found: {nodes})")
        product = matching[0]
    elif len(products) > 1:
        raise CollectionFilesError(
            f"{lidvid} is registered under several nodes ({', '.join(str(n) for n in nodes)}); "
            "choose one with --node-name"
        )
    else:
        product = products[0]

    props = product.get("properties", {})
    label_url = _first(props.get(_LABEL_REF)) or product.get("metadata", {}).get("label_url")
    if not label_url:
        raise CollectionFilesError(f"The API has no label URL for {lidvid}")

    records_text = _first(props.get(_RECORDS))
    try:
        records = int(records_text) if records_text is not None else None
    except ValueError:
        records = None

    return CollectionFiles(
        lidvid=lidvid,
        label_url=label_url,
        inventory_url=_first(props.get(_INVENTORY_REF)),
        label_md5=_first(props.get(_LABEL_MD5)),
        inventory_md5=_first(props.get(_INVENTORY_MD5)),
        label_records=records,
        harvest_time=_first(props.get(_HARVEST_TIME)),
        node_name=_first(props.get(_NODE_NAME)),
    )


# ── URLs and local paths ──────────────────────────────────────────────────────


def url_directory(url: str) -> str:
    """Return the directory part of a URL with a trailing slash (``https://host/a/b.xml`` -> ``https://host/a/``)."""
    parsed = urllib.parse.urlparse(url)
    directory = posixpath.dirname(parsed.path)
    return f"{parsed.scheme}://{parsed.netloc}{directory.rstrip('/')}/"


def url_origin(url: str) -> str:
    """Return ``scheme://host[:port]`` for a URL."""
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def host_directory(url: str) -> str:
    """Return the name of the local directory that mirrors a URL's host."""
    return urllib.parse.urlparse(url).netloc.replace(":", "_")


def mirror_path(output_dir: Path, url: str) -> Path:
    """Return where a file is stored locally: ``<output-dir>/files/<host>/<url path>``.

    Args:
        output_dir: The output directory.
        url: The file's URL.

    Returns:
        The local path.

    Raises:
        CollectionFilesError: If the URL has no path to a file or tries to leave the host directory.
    """
    parsed = urllib.parse.urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if not parsed.netloc or not parts or any(part in (".", "..") for part in parts):
        raise CollectionFilesError(f"Cannot map {url} to a local path")
    return output_dir / "files" / host_directory(url) / Path(*parts)


def common_url_prefix(urls: list[str]) -> str:
    """Return the longest shared directory prefix of some URLs, ending in ``/``."""
    directories = [url_directory(url).split("/") for url in urls]
    shared: list[str] = []
    for parts in zip(*directories):
        if len(set(parts)) != 1:
            break
        shared.append(parts[0])
    return "/".join(shared).rstrip("/") + "/"


# ── downloading and checking ──────────────────────────────────────────────────


def download_file(session: requests.Session, url: str, dest: Path, timeout: int) -> str:
    """Download a file to ``dest`` and return its MD5.

    The file is written to a temporary name and renamed when complete, so an interrupted download
    never leaves a truncated file under the final name.

    Args:
        session: Shared HTTP session.
        url: File URL.
        dest: Destination path; parent directories are created.
        timeout: Per-request timeout in seconds.

    Returns:
        The MD5 hex digest of the downloaded bytes.

    Raises:
        CollectionFilesError: If the download or the write fails.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    digest = hashlib.md5()  # noqa: S324 - PDS4 checksums are MD5
    try:
        with session.get(url, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            with open(partial, "wb") as f:
                for chunk in resp.iter_content(chunk_size=_CHUNK_SIZE):
                    f.write(chunk)
                    digest.update(chunk)
        partial.replace(dest)
    except (requests.exceptions.RequestException, OSError) as exc:
        partial.unlink(missing_ok=True)
        raise CollectionFilesError(f"Download of {url} failed: {exc}") from exc
    return digest.hexdigest()


def file_md5(path: Path) -> str:
    """Return the MD5 hex digest of a file on disk."""
    digest = hashlib.md5()  # noqa: S324 - PDS4 checksums are MD5
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_inventory_rows(path: Path) -> int:
    """Count the data rows of a PDS4 inventory table, excluding a header row if there is one.

    Args:
        path: Local inventory CSV.

    Returns:
        The number of data rows. Data rows begin with ``P`` or ``S`` (member status).
    """
    rows = 0
    first = True
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if not any(cell.strip() for cell in row):
                continue
            if first:
                first = False
                if row[0].strip().upper() not in ("P", "S"):
                    continue
            rows += 1
    return rows


def label_record_count(path: Path) -> int | None:
    """Read ``pds:Inventory/pds:records`` from a downloaded collection label.

    The label is read as text rather than parsed as XML, since it comes from a data provider.

    Args:
        path: Local collection label.

    Returns:
        The declared record count, or ``None`` if the label has none.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    match = _RECORDS_PATTERN.search(text)
    return int(match.group(1)) if match else None


# ── building the work list ────────────────────────────────────────────────────


def read_lidvids_from_file(path: Path) -> list[str]:
    """Read collection LIDVIDs from a file, skipping blank lines and ``#`` comments."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def read_lidvids_from_audit_csv(path: Path, rules: set[str]) -> list[str]:
    """Read the distinct collections of an audit's products that have one of the given rules.

    Args:
        path: ``unprocessed_products.csv`` or ``.csv.gz`` from ``audit_unprocessed_products.py``.
        rules: Audit rules whose collections to take.

    Returns:
        Sorted collection LIDVIDs.
    """
    opener = gzip.open if path.suffix == ".gz" else open
    found: set[str] = set()
    with opener(path, "rt", encoding="utf-8", newline="") as f:  # type: ignore[operator]
        for row in csv.DictReader(f):
            if row["rule"] in rules and row["collection_lidvid"]:
                found.add(row["collection_lidvid"])
    return sorted(found)


# ── per-collection work ───────────────────────────────────────────────────────


def process_collection(
    session: requests.Session,
    api_base: str,
    lidvid: str,
    output_dir: Path,
    timeout: int,
    list_only: bool,
    skip_existing: bool,
    node_name: str | None = None,
) -> tuple[dict, CollectionFiles | None]:
    """Look up one collection and, unless ``list_only``, download and check its files.

    Args:
        session: Shared HTTP session.
        api_base: PDS Search API base URL.
        lidvid: Collection LIDVID.
        output_dir: Output directory.
        timeout: Per-request timeout in seconds.
        list_only: Skip the downloads.
        skip_existing: Reuse files already on disk.

    Returns:
        A manifest row (keyed by ``_MANIFEST_FIELDS``) and the API's file information, which is
        ``None`` when the API lookup failed.
    """
    row: dict = {field: "" for field in _MANIFEST_FIELDS}
    row["collection_lidvid"] = lidvid
    files: CollectionFiles | None = None
    try:
        files = fetch_collection_files(session, api_base, lidvid, timeout, node_name)
        row.update(
            node_name=files.node_name or "",
            label_url=files.label_url,
            inventory_url=files.inventory_url or "",
            url_base=url_directory(files.label_url),
            label_and_inventory_same_dir=(
                "" if not files.inventory_url else url_directory(files.label_url) == url_directory(files.inventory_url)
            ),
            label_md5_registry=files.label_md5 or "",
            inventory_md5_registry=files.inventory_md5 or "",
            label_records_registry="" if files.label_records is None else files.label_records,
            registry_harvest_date_time=files.harvest_time or "",
        )
        label_path = mirror_path(output_dir, files.label_url)
        inventory_path = mirror_path(output_dir, files.inventory_url) if files.inventory_url else None
        row["local_label"] = str(label_path)
        row["local_inventory"] = str(inventory_path) if inventory_path else ""

        if list_only:
            row["status"] = "listed"
            return row, files

        def fetch(url: str, dest: Path) -> str:
            if skip_existing and dest.exists():
                logger.info("Keeping existing %s", dest)
                return file_md5(dest)
            logger.info("Downloading %s", url)
            return download_file(session, url, dest, timeout)

        row["label_md5_local"] = fetch(files.label_url, label_path)
        changed = bool(files.label_md5) and row["label_md5_local"] != files.label_md5
        if files.inventory_url and inventory_path is not None:
            row["inventory_md5_local"] = fetch(files.inventory_url, inventory_path)
            changed = changed or (bool(files.inventory_md5) and row["inventory_md5_local"] != files.inventory_md5)
            rows = count_inventory_rows(inventory_path)
            row["inventory_rows"] = rows
            local_records = label_record_count(label_path)
            row["label_records_local"] = "" if local_records is None else local_records
            row["records_match"] = "" if local_records is None else rows == local_records
        row["md5_changed_since_harvest"] = changed
        row["status"] = "downloaded"
    except CollectionFilesError as exc:
        logger.error("%s: %s", lidvid, exc)
        row["status"] = "failed"
        row["error"] = str(exc)
    return row, files


# ── outputs ───────────────────────────────────────────────────────────────────


def write_manifest(rows: list[dict], path: Path) -> None:
    """Write the one-row-per-collection manifest CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_harvest_snippet(output_dir: Path, rows: list[dict]) -> str:
    """Build the Harvest configuration fragment for the collections that were looked up.

    Args:
        output_dir: The output directory (made absolute in the snippet).
        rows: Manifest rows.

    Returns:
        XML text with the ``<load>`` directories and the ``<fileInfo>`` ``fileRef`` per host.
    """
    root = output_dir.resolve()
    directories: list[str] = []
    origins: dict[str, str] = {}
    for row in rows:
        if row["status"] == "failed" or not row["local_label"]:
            continue
        label_dir = str(Path(row["local_label"]).resolve().parent)
        if label_dir not in directories:
            directories.append(label_dir)
        origins[host_directory(row["label_url"])] = url_origin(row["label_url"])

    lines = [
        "<!-- Merge into your Harvest configuration: keep your <registry> element and run Harvest",
        "     with its overwrite option so the collection documents are rewritten. -->",
        "<load>",
        "  <directories>",
    ]
    lines += [f"    <path>{directory}</path>" for directory in directories]
    lines += [
        "  </directories>",
        "</load>",
        "",
        '<fileInfo processDataFiles="true" storeLabels="true">',
    ]
    for host_dir, origin in sorted(origins.items()):
        lines.append(f'  <fileRef replacePrefix="{root / "files" / host_dir}" with="{origin}" />')
    lines.append("</fileInfo>")
    return "\n".join(lines) + "\n"


def print_summary(rows: list[dict], files_by_lidvid: dict[str, CollectionFiles], output_dir: Path) -> None:
    """Print the per-host URL prefixes and the checks that need attention."""
    root = output_dir.resolve()
    urls_by_host: dict[str, list[str]] = defaultdict(list)
    not_urls: list[dict] = []
    for row in rows:
        if not row["label_url"]:
            continue
        if urllib.parse.urlparse(row["label_url"]).netloc:
            urls_by_host[url_origin(row["label_url"])].append(row["label_url"])
        else:
            not_urls.append(row)

    print()
    print("Harvest fileRef prefixes (one per host)")
    print("-" * 70)
    for origin, urls in sorted(urls_by_host.items()):
        host_dir = host_directory(urls[0])
        print(f"  {len(urls):>3} collection(s)  with=\"{origin}\"")
        print(f"       replacePrefix=\"{root / 'files' / host_dir}\"")
        print(f"       common URL path of these collections: {common_url_prefix(urls)}")

    if not_urls:
        print()
        print("Registered label file_ref is not a URL (nothing to download; fix the file_ref or supply the files)")
        for row in not_urls:
            print(f"  {row['collection_lidvid']}: {row['label_url']}")

    failed = [r for r in rows if r["status"] == "failed"]
    changed = [r for r in rows if r["md5_changed_since_harvest"] is True]
    mismatched = [r for r in rows if r["records_match"] is False]
    split = [r for r in rows if r["label_and_inventory_same_dir"] is False]
    print()
    print(f"Collections: {len(rows)}   failed: {len(failed)}")
    print(f"  provider file changed since harvest (MD5 differs from registry): {len(changed)}")
    print(f"  label record count differs from inventory rows (provider issue): {len(mismatched)}")
    print(f"  label and inventory in different directories (Harvest needs them together): {len(split)}")
    for title, group in (("Failed", failed), ("Record count mismatch", mismatched), ("Split directories", split)):
        for row in group:
            print(f"    {title}: {row['collection_lidvid']}")


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download collection labels and inventories from their registered URLs for re-harvesting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("lidvids", nargs="*", metavar="LIDVID", help="Collection LIDVIDs to download")
    parser.add_argument("--output-dir", type=Path, required=True, metavar="DIR", help="Directory for all outputs")
    parser.add_argument("--from-file", type=Path, default=None, metavar="FILE", help="File of collection LIDVIDs")
    parser.add_argument(
        "--from-audit-csv", type=Path, default=None, metavar="FILE", help="unprocessed_products.csv or .csv.gz"
    )
    parser.add_argument(
        "--rules",
        nargs="+",
        default=list(_DEFAULT_RULES),
        metavar="RULE",
        help=f"Audit rules whose collections to take (default: {' '.join(_DEFAULT_RULES)})",
    )
    parser.add_argument("--list-only", action="store_true", help="Query the API but download nothing")
    parser.add_argument("--skip-existing", action="store_true", help="Keep files already on disk")
    parser.add_argument(
        "--node-name",
        default=None,
        metavar="NAME",
        help=(
            "Use the copy registered under this ops:Harvest_Info/ops:node_name (for example PDS_ATM). Required "
            "for collections registered under more than one node, since each node holds its own copy of the files"
        ),
    )
    parser.add_argument("--api-base", default=_DEFAULT_API_BASE, metavar="URL", help="PDS Search API base URL")
    parser.add_argument("--timeout", type=int, default=60, metavar="N", help="Per-request timeout in seconds")
    parser.add_argument(
        "--log-level", "-l", default="info", choices=list(_LOG_LEVELS), metavar="LEVEL", help="Logging verbosity"
    )
    return parser.parse_args(argv)


def main() -> int:
    """Entry point.

    Returns:
        0 when every collection was handled, 1 when any failed or no collections were given.
    """
    args = parse_args()
    logging.basicConfig(level=_LOG_LEVELS[args.log_level], stream=sys.stderr, format="%(levelname)s %(message)s")

    lidvids = list(args.lidvids)
    if args.from_file:
        lidvids += read_lidvids_from_file(args.from_file)
    if args.from_audit_csv:
        lidvids += read_lidvids_from_audit_csv(args.from_audit_csv, set(args.rules))
    lidvids = list(dict.fromkeys(lidvids))
    if not lidvids:
        logger.error("No collections given: use LIDVIDs, --from-file or --from-audit-csv")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    session = make_session()
    rows: list[dict] = []
    files_by_lidvid: dict[str, CollectionFiles] = {}
    for index, lidvid in enumerate(lidvids, start=1):
        logger.info("[%d/%d] %s", index, len(lidvids), lidvid)
        row, files = process_collection(
            session,
            args.api_base,
            lidvid,
            args.output_dir,
            args.timeout,
            args.list_only,
            args.skip_existing,
            args.node_name,
        )
        rows.append(row)
        if files is not None:
            files_by_lidvid[lidvid] = files

    write_manifest(rows, args.output_dir / "manifest.csv")
    snippet = build_harvest_snippet(args.output_dir, rows)
    (args.output_dir / "harvest_config_snippet.xml").write_text(snippet, encoding="utf-8")
    print_summary(rows, files_by_lidvid, args.output_dir)
    print(f"\nManifest: {args.output_dir / 'manifest.csv'}")
    print(f"Harvest config fragment: {args.output_dir / 'harvest_config_snippet.xml'}")
    return 1 if any(r["status"] == "failed" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
