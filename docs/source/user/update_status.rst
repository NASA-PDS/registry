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

   * - Status
     - Description
   * - ``archived``
     - Publicly visible through the Registry API (PDS Search API).
   * - ``certified``
     - Certified and publicly visible through the Registry API (PDS Search API).
   * - ``restricted``
     - Not publicly visible.
   * - ``staged``
     - Ingested but not yet publicly available (default on ingest).


Set Archive Status
******************

Before You Begin
~~~~~~~~~~~~~~~~

- Data is ingested into the Registry per :doc:`/user/load1`
- Registry Manager installed per :doc:`/install/install`


Run the Command
~~~~~~~~~~~~~~~

Replace ``{venue}`` with your venue (``dev``, ``test``, ``prod``), and the endpoint and LIDVID with your values.

**Linux / macOS:**

.. code-block:: bash

   registry-manager set-archive-status \
       -auth $HOME/.pds/registry-auth-{venue}.txt \
       -registry https://your-opensearch-endpoint.example.com \
       -status archived \
       -lidvid "urn:nasa:pds:kaguya_grs_spectra:document::1.0"

**Windows:**

.. code-block:: powershell

   .\registry-manager.bat set-archive-status `
       -auth '%USERPROFILE%\.pds\registry-auth-{venue}.txt' `
       -registry 'https://your-opensearch-endpoint.example.com' `
       -status archived `
       -lidvid 'urn:nasa:pds:insight_rad:data_derived::7.0'

.. note::
   If the LIDVID targets a collection, all primary products in the collection inventory are updated.
   If it targets a bundle, all collections in the bundle are updated.


Verify via the Registry API
****************************

Once status is set to ``archived`` or ``certified``, products are accessible through the
`Registry API (PDS Search API) <https://nasa-pds.github.io/pds-api/guides/search.html>`_.

The base URL ``https://pds.nasa.gov/api/search/1`` also provides interactive API documentation.
