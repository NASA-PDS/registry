===========
Dashboards
===========

Overview
********

You can view summaries of the datasets available in your registry with Dashboards.

Prerequisites
*************

You need to be on a whitelisted IP address to access the Registry's OpenSearch database, see :doc:`/cloud_startup`


View the dashboards
********************

#. Go to your dashboard in you favorite web browser, using the URL of your OpenSearch database suffixed by ``/_dashboards``

#. Log in with the username/password provided by Engineering Node (see :doc:`/cloud_startup`)

#. Select global tenant

#. Click on the menu on the upper-left

#. In `OpenSearch Dashboards` section, select `Dashboard`

#. You are getting a list of default dashbaords provided to you (see table below)

#. Optionally: You can update the dashboard and see the underlying OpenSearch requests by clicking the wheel on the top right of each dashboard

#. Optionally: You can request a new dashboard or any update by creating a ticket in this repository https://github.com/NASA-PDS/archive-analytics/issues

.. list-table:: List of dashboard available by default
   :widths: 25 50
   :header-rows: 1

   * - Name
     - Description
   * - Archive Metrics Dashboard
     - List all products and pie charts and table sorted on various product properties (class, science discipline...)
   * - Data Type Metrics Dashboard
     - Pie charts and table sorted on various product attributes (class, science discipline...)
   * - Data Volume Dashboard
     - Monthly labels and data volumes time series
   * - Node Operator Dashboard
     - Bundles and Collections listed by status (staged, archived)
   * - Product Count Metrics
     - Products counts by references (e.g. target, investigation, instruments...)




