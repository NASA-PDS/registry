=====================
Update Archive Status
=====================

When a product is ingested into PDS Registry, its archive status is set to *"staged"*.

.. code-block:: javascript

  "ops:Tracking_Meta/ops:archive_status": "staged"

You can change that value to any of the following:

 * archived
 * certified
 * restricted
 * staged

Status *"archived"* and *"certified"* make the products visible to the public, currently through the PDS Web API.

You can use either Registry Manager or Harvest Client (Scalable Harvest deployments only) for this task.

Registry Manager
*****************

Prerequisites
=============

  * Some data is `ingested <./load1.html>`_ into the Registry.
  * Registry Manager command-line tool is `installed <../install/tools.html#registry-manager>`_.


Set status
===========

To set product archive status, execute Registry Manager's "set-archive-status" command.

The following parameters are required:

 * **-status <status>** - New status. Pass one of the following values: "archived", "certified", "restricted", "staged".
 * **-lidvid <id>** - LIDVID of a product to update. If the product is a collection product,
   all primary references from the collection inventory will be also updated.
   If the product is a bundle product, all bundle's collections will be also updated.
 * **-es <url>** - link to the connection configuration file described in :doc:`/connection-setup`
 * **-auth <file>** - OpenSearch authentication configuration file. See :doc:`/connection-setup`.

**Examples:**

On **MacOS/Linux**:

.. code-block:: bash

   registry-manager set-archive-status \
       -es file://path/to/registry_connection.xml \
       -auth /my/path/auth.cfg \
       -status archived \
       -lidvid "urn:nasa:pds:kaguya_grs_spectra:document::1.0"


On **Windows**:

.. code-block:: powershell

    .\registry-manager.bat set-archive-status
        -auth 'C:\Users\loubrieu\Documents\es-auth.txt'
        -es 'file:///C:\Users\loubrieu\Documents\mcp_dev.xml'
        -lidvid 'urn:nasa:pds:insight_rad:data_derived::7.0'
        -status archived



The connection and auth files are described in :doc:`/connection-setup`

Registry API
************

Once data has been ingested and archive status is set to `archived` or `registered`, it is accessible using the Registry
API which is `documented here <https://nasa-pds.github.io/pds-api/guides/search.html>`_.

The base URL of the API https://pds.nasa.gov/api/search/1 also provides an online documentation.
