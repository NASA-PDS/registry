Registry Loading Status
=======================

Reports are automatically generated on a schedule, committed to this repository, and published to GitHub Pages.
They track migration progress from the legacy PDS Solr registry to the new OpenSearch-based registry.

.. note::
   Reports update automatically whenever the scheduled workflow runs (typically daily).
   The burnup chart is published to GitHub Pages on every push to ``main`` or ``develop``.


Burnup Chart
------------

The `Burnup Chart <https://nasa-pds.github.io/registry/status/burnup_chart.html>`_ shows cumulative products loaded
into the new registry over time, broken down by PDS node. It includes:

- Overall and per-node loading progress vs. target
- Both "all versions" and "latest version per LID" views
- An interactive date-range filter (defaults to the last 12 months)

.. raw:: html

   <p>
     <a href="https://nasa-pds.github.io/registry/status/burnup_chart.html" target="_blank">
       &#x1F4CA; Open Burnup Chart in full page
     </a>
   </p>
   <iframe
     src="https://nasa-pds.github.io/registry/status/burnup_chart.html"
     width="100%"
     height="600"
     style="border:1px solid #ccc; border-radius:4px;"
     title="PDS Registry Burnup Chart">
   </iframe>


Status Reports
--------------

All CSV reports and the full metrics summary are in the
`docs/status directory on GitHub <https://github.com/NASA-PDS/registry/tree/main/docs/status>`_.
The `README in that directory <https://github.com/NASA-PDS/registry/blob/main/docs/status/README.md>`_
contains the latest metrics table and detailed field descriptions.

Missing Products
~~~~~~~~~~~~~~~~

Products present in the legacy Solr registry but **not yet loaded** into the new OpenSearch registry.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - File
     - Description
   * - `missing_bundles_in_registry.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/missing_bundles_in_registry.csv>`_
     - All missing Product_Bundle records (all versions)
   * - `missing_collections_in_registry.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/missing_collections_in_registry.csv>`_
     - All missing Product_Collection records (all versions)

Each row includes ``NODE_ID``, ``LIDVID``, ``PRODUCT_CLASS``, and a ``SUPERSEDED`` flag
(``true`` if a newer version of the same LID exists anywhere in the dataset).

Loaded Products
~~~~~~~~~~~~~~~

All products currently in the new OpenSearch registry, regardless of archive status.
Queried with ``search_after`` pagination so counts are not capped at 10,000.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - File
     - Description
   * - `loaded_bundles_in_registry.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/loaded_bundles_in_registry.csv>`_
     - All Product_Bundle records in new OpenSearch
   * - `loaded_collections_in_registry.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/loaded_collections_in_registry.csv>`_
     - All Product_Collection records in new OpenSearch

.. note::
   Loaded counts will exceed the legacy Solr counts because the new registry also contains products
   harvested directly from non-Solr sources (e.g., PSA/ESA ~900 bundles, ~4,000 collections).

Staged Products
~~~~~~~~~~~~~~~

Products loaded into the new registry but with ``archive_status = staged``
(loaded but not yet transitioned to ``archived``). These require operator action.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - File
     - Description
   * - `staged_bundles_in_registry.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/staged_bundles_in_registry.csv>`_
     - Staged Product_Bundle records
   * - `staged_collections_in_registry.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/staged_collections_in_registry.csv>`_
     - Staged Product_Collection records

Historical Counts
~~~~~~~~~~~~~~~~~

Append-only snapshots of missing and staged totals per script run.
Use these files to plot burndown charts externally.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - File
     - Description
   * - `counts_history.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/counts_history.csv>`_
     - Missing/staged totals per run (append-only)
   * - `burnup_history.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/burnup_history.csv>`_
     - Cumulative loaded counts by date (all versions)
   * - `burnup_history_latest.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/burnup_history_latest.csv>`_
     - Cumulative loaded counts by date (latest version per LID only)
   * - `burnup_by_node.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/burnup_by_node.csv>`_
     - Per-node cumulative loaded counts (all versions)
   * - `burnup_by_node_latest.csv <https://github.com/NASA-PDS/registry/blob/main/docs/status/burnup_by_node_latest.csv>`_
     - Per-node cumulative loaded counts (latest version per LID only)


Report Generation
-----------------

Reports are generated by ``scripts/generate_registry_status_reports.py``.
To regenerate locally without committing:

.. code-block:: bash

   ./venv/bin/python scripts/generate_registry_status_reports.py --no-commit

Requires AWS/Cognito credentials configured in ``~/.pds/.registry-client`` or ``.env``.
See :doc:`/developer/developer` for environment setup details.
