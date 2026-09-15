===========
Dashboards
===========

.. warning:: Dashboards are not available with the latest version of the Registry Service.

View summaries of the datasets available in your registry using OpenSearch Dashboards.


Before You Begin
****************

Your IP address must be on the access whitelist. See :doc:`/connection-setup`.


View the Dashboards
********************

1. Open ``https://{your-opensearch-url}/_dashboards`` in a browser.
2. Log in with the username and password provided by the Engineering Node.
3. Select **Global** tenant.
4. Click the menu icon in the upper-left.
5. Under **OpenSearch Dashboards**, select **Dashboard**.
6. Choose a dashboard from the list below.

.. list-table:: Default dashboards
   :widths: 25 75
   :header-rows: 1

   * - Name
     - Description
   * - Archive Metrics Dashboard
     - All products with pie charts and tables sorted by class and science discipline.
   * - Data Type Metrics Dashboard
     - Pie charts and tables sorted by product attributes (class, discipline, etc.).
   * - Data Volume Dashboard
     - Monthly label and data volume time series.
   * - Node Operator Dashboard
     - Bundles and collections listed by status (staged, archived).
   * - Product Count Metrics
     - Product counts by reference type (target, investigation, instrument, etc.).

.. note::
   To inspect the underlying OpenSearch queries for a dashboard, click the gear icon in the top-right of any dashboard panel.
   To request a new or updated dashboard, open an issue at https://github.com/NASA-PDS/archive-analytics/issues.
