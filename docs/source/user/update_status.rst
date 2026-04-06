=====================
Update Archive Status
=====================

When ingested into PDS Registry, products are assigned a status of ``staged``.
Update the status to make products publicly visible or to restrict access.

Archive Status Values
*********************

.. list-table::
   :header-rows: 1
   :widths: 20 80

You can change that value to any of the following:

 * **archived** - Product has been archived and is publicly visible through the Registry API (PDS Search API).
 * **certified** - Product has been certified and is publicly visible through the Registry API (PDS Search API).
 * **restricted** - Product has restricted access and is not publicly visible.
 * **staged** - Product is ingested but not yet publicly available (default status when ingested).

Status *"archived"* and *"certified"* make the products visible to the public through the Registry API (PDS Search API).

You can use either Registry Manager or Harvest Client (Scalable Harvest deployments only) for this task.

Registry Manager
*****************

Prerequisites
=============

  * Some data is `ingested <./load1.html>`_ into the Registry.
  * Registry Manager command-line tool is `installed <../install/tools.html#registry-manager>`_.


Set Archive Status
******************

Before You Begin
~~~~~~~~~~~~~~~~

The following parameters are **required**:

 * **-status <status>** - New status. Pass one of the following values: "archived", "certified", "restricted", "staged".
 * **-lidvid <id>** - LIDVID of a product to update. If the product is a collection product,
   all primary references from the collection inventory will be also updated.
   If the product is a bundle product, all bundle's collections will be also updated.

The following parameters are **optional**:

 * **-registry <url>** - URL to the OpenSearch registry endpoint (replaces deprecated -es option). See :doc:`/connection-setup`.
 * **-auth <file>** - OpenSearch authentication configuration file. See :doc:`/connection-setup`.

Run the Command
~~~~~~~~~~~~~~~

Replace ``{venue}`` with your venue (``dev``, ``test``, ``prod``), and the endpoint and LIDVID with your values.

**Linux / macOS:**

.. code-block:: bash

   registry-manager set-archive-status \
       -registry https://your-opensearch-endpoint.example.com \
       -auth /my/path/auth.cfg \
       -status archived \
       -lidvid "urn:nasa:pds:kaguya_grs_spectra:document::1.0"

**Windows:**

.. code-block:: powershell

    .\registry-manager.bat set-archive-status
        -auth 'C:\Users\loubrieu\Documents\es-auth.txt'
        -registry 'https://your-opensearch-endpoint.example.com'
        -lidvid 'urn:nasa:pds:insight_rad:data_derived::7.0'
        -status archived


Verify via the Registry API
****************************

Once status is set to ``archived`` or ``certified``, products are accessible through the
`Registry API (PDS Search API) <https://nasa-pds.github.io/pds-api/guides/search.html>`_.

Registry API (PDS Search API)
******************************

Once data has been ingested and archive status is set to ``archived`` or ``certified``, it is accessible using the Registry
API which is `documented here <https://nasa-pds.github.io/pds-api/guides/search.html>`_.

The base URL of the API https://pds.nasa.gov/api/search/1 also provides an online documentation.
