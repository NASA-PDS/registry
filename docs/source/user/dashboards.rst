===========
Dashbaords
===========

Overview
********

You can view summaries of the datasets available in your registry with Dashboards.

Prerequisites
*************

- be on a whitelisted IP address to access the Registry's OpenSearch database, see :doc:`/cloud_startup`


View the dashboards
********************

#. Go to your dashboard in you favorite web browser, using the URL of your OpenSearch database suffixed by `/_dashboards`

#. Log in with the username/passowrd provided by Engineering Node (see :doc:`/cloud_startup`)

#. Select global tenant

#. Click on the menu on the upper-left

#. In `OpnSearch Dashboards` section, select `Dashboard`

#. You are getting a list of default dashbaords provided to you:

#. You can update the dashbaord and see the underlying OpenSearch requests by clicking the wheel on the top right of each dashboard

#. You can request for new dashboard or any update by creating a ticket in this repository https://github.com/NASA-PDS/archive-analytics/issues


The list of dashboard available by default is:

* Archive Metrics Dashboard: list all products and pie charts and table sorted on various product properties (class, science discipline...)

* Data Type Metrics Dashboard: pie charts and table sorted on various product attributes (class, science discipline...)

* Data Volume Dashboard: Monthly labels and data volumes time series

* Node Operator Dashboard: Bundles and Collections listed by status (staged, archived)

* Product Count Metrics: products counts by references (e.g. target, investigation, instruments...)




