"""Shared constants and data types for the unprocessed product audit.

Every other module in this package imports from here, so this file is the contract between the
classification logic, the registry queries and the reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum

# ── registry field names (OpenSearch ``_source`` keys use the slash form) ─────

STAMP_FIELD = "ops:Provenance/ops:registry_sweepers_ancestry_version"
"""Ancestry version stamp. Mapped as ``keyword``: compare for equality server-side."""
REFS_FIELD = "ops:Provenance/ops:ancestor_refs"
"""Ancestors of a product. The array can be empty; ``exists`` treats an empty array as absent."""
HARVEST_FIELD = "ops:Harvest_Info/ops:harvest_date_time"
NODE_FIELD = "ops:Harvest_Info/ops:node_name"
ARCHIVE_STATUS_FIELD = "ops:Tracking_Meta/ops:archive_status"
SUPERSEDED_FIELD = "ops:Provenance/ops:superseded_by"
DATA_FILE_REF_FIELD = "ops:Data_File_Info/ops:file_ref"
"""For a collection, the URL of its inventory table."""

API_VISIBLE_ARCHIVE_STATUSES = ["archived", "certified"]
"""Archive-status values that the PDS Search API exposes to callers."""

CURRENT_ANCESTRY_VERSION = 7
"""``SWEEPERS_ANCESTRY_VERSION`` in the registry-sweepers ancestry package."""

AGGREGATE_CLASSES = ("Product_Bundle", "Product_Collection")
"""Product classes the ancestry sweeper selects directly; everything else is a non-aggregate."""

NO_PARENT_CLASSES = ("Product_Service", "Product_Context")
"""Product classes that never belong to a collection, so lacking ancestry is expected."""

REGISTRY_SUFFIX = "-registry"
REFS_SUFFIX = "-registry-refs"
LEGACY_INDEX = "en-legacy-registry"
"""Legacy Solr mirror; it matches ``*-registry`` but holds no sweeper-managed products."""


class Population(str, Enum):
    """Why a product is considered to lack (current) ancestry."""

    NO_STAMP = "A"
    """No ancestry stamp."""
    EMPTY_REFS = "B"
    """Stamped with the current version, but ``ancestor_refs`` is empty or absent."""
    STALE_STAMP = "C"
    """Stamped with a version other than the current one."""


class Severity(str, Enum):
    """Whether a product's missing ancestry is expected to resolve on its own."""

    EXPECTED = "expected"
    ANOMALOUS = "anomalous"


class CollectionState(str, Enum):
    """Ancestry-processing state of a collection."""

    PROCESSED = "processed"
    """Stamp is current and ``ancestor_refs`` is non-empty."""
    STAMPED_EMPTY_REFS = "stamped_empty_refs"
    """Stamp is current but ``ancestor_refs`` is empty or absent."""
    UNPROCESSED_PENDING = "unprocessed_pending"
    """Stamp missing or stale, harvested within the collection grace period."""
    UNPROCESSED_OVERDUE = "unprocessed_overdue"
    """Stamp missing or stale, harvested longer ago than the collection grace period."""


class Rule(str, Enum):
    """Why a product lacks ancestry. Each product gets exactly one."""

    NO_PARENT_BY_DESIGN = "no_parent_by_design"
    COLLECTION_NOT_LOADED_PENDING = "collection_not_loaded_pending"
    COLLECTION_NOT_LOADED_OVERDUE = "collection_not_loaded_overdue"
    COLLECTION_PENDING = "collection_pending"
    COLLECTION_OVERDUE = "collection_overdue"
    RELOADED_AFTER_COLLECTION = "reloaded_after_collection"
    INVENTORY_VERSION_MISMATCH = "inventory_version_mismatch"
    NOT_IN_COLLECTION_INVENTORY = "not_in_collection_inventory"
    SWEEPER_MISS = "sweeper_miss"
    REFS_MISSING_PENDING = "refs_missing_pending"
    REFS_MISSING = "refs_missing"
    STALE_STAMP = "stale_stamp"


@dataclass(frozen=True)
class Thresholds:
    """Run parameters that decide whether something is overdue.

    Attributes:
        now: Reference time for ages. Injected so tests are deterministic.
        collection_grace_days: How long an unprocessed collection is left alone.
        product_grace_days: How long a product waiting for its collection is left alone.
        ancestry_version: The current ancestry version stamp.
    """

    now: datetime
    collection_grace_days: float = 1.0
    product_grace_days: float = 7.0
    ancestry_version: int = CURRENT_ANCESTRY_VERSION


@dataclass
class Collection:
    """An API-visible collection and its ancestry state.

    Attributes:
        lidvid: Collection LIDVID.
        lid: Collection LID (the LIDVID without ``::<version>``).
        node: Node the collection is registered under (the index prefix, e.g. ``atm``).
        stamp: Raw ancestry stamp value, ``None`` when absent.
        ancestor_refs: Values of ``ancestor_refs`` (bundle LIDVIDs and LIDs); empty when absent.
        harvest: Harvest time, ``None`` when absent or unparseable.
        state: Filled in by ``classify.classify_collection``.
        bundle_lidvids: Bundles that reference this collection's LID. Filled in by the registry
            lookup for ``STAMPED_EMPTY_REFS`` collections.
        superseded_by: LIDVID of the newer collection version that superseded this one, ``None`` for a
            current version. Superseded versions are kept so their products are attributed to them.
        inventory_url: URL of the collection's inventory table, ``None`` when the registry has none.
    """

    lidvid: str
    lid: str
    node: str
    stamp: str | None
    ancestor_refs: list[str]
    harvest: datetime | None
    state: CollectionState | None = None
    bundle_lidvids: list[str] = field(default_factory=list)
    superseded_by: str | None = None
    inventory_url: str | None = None


@dataclass
class Candidate:
    """A non-aggregate product that lacks current ancestry (one row of phase 2).

    Attributes:
        lidvid: Product LIDVID.
        lid: Product LID.
        product_class: ``product_class`` value.
        node: Node (index prefix) the product is registered under.
        stamp: Raw ancestry stamp value, ``None`` when absent.
        has_ancestor_refs: Whether ``ancestor_refs`` is non-empty.
        harvest: Harvest time, ``None`` when absent or unparseable.
    """

    lidvid: str
    lid: str
    product_class: str
    node: str
    stamp: str | None
    has_ancestor_refs: bool
    harvest: datetime | None


@dataclass
class Verdict:
    """The outcome of classifying one candidate; one row of ``unprocessed_products.csv``.

    Attributes:
        population: Which population (A/B/C) the candidate is in.
        rule: The rule that applied.
        severity: Expected or anomalous.
        rationale: One-line, human-readable explanation written to the CSV.
        bundle_lid: Bundle LID derived from the product LID, if derivable.
        collection_lidvid: Parent collection LIDVID (from refs, else the matched collection), if known.
        collection_state: State of that collection, if it was found.
        collection_harvest: Harvest time of that collection, if known.
        in_refs: Whether a ``registry-refs`` document lists the product. ``None`` when refs were not
            consulted for this product.
    """

    population: Population
    rule: Rule
    severity: Severity
    rationale: str
    bundle_lid: str | None = None
    collection_lidvid: str | None = None
    collection_state: CollectionState | None = None
    collection_harvest: datetime | None = None
    in_refs: bool | None = None


@dataclass
class RefsCoverage:
    """How well ``registry-refs`` covers one collection's members.

    Attributes:
        refs_count: ``product_lidvid`` values across every refs document of the collection.
        member_count: API-visible members found by LID prefix.
        stamped_member_count: Of those members, how many carry current ancestry.
    """

    refs_count: int
    member_count: int
    stamped_member_count: int


class RegistryQueryError(Exception):
    """A registry (OpenSearch) request failed or returned an unusable response."""
