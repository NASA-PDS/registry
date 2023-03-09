============================
Load Data - Scalable Harvest
============================

Overview
********

To load PDS4 data into Registry you have to use Harvest software. There are two versions of Harvest:
a simple standalone command-line tool and a scalable Harvest consisting of several server and and
client components. Scalable Harvest can process big data sets in parallel.
Both versions extract metadata from PDS4 products (labels) and load extracted
metadata into OpenSearch database.

This document describes how to use Harvest Client command-line tool to submit jobs to Scalable Harvest Server cluster.


Prerequisites
*************

* OpenSearch server is `running <https://opensearch.org/>`_.
* Registry indices are `created <../admin/create_reg.html#create-registry>`_ in OpenSearch.
* All server components - RabbitMQ, Crawler Server, Harvest Server - are deployed and running on-prem or in the cloud.
* Harvest Client command-line tool is installed.


Scalable Harvest Quick Start
****************************

Scalable Harvest consists of several server components: RabbitMQ, Crawler and Harvest servers.
To load data you have to use Harvest Client command-line tool to submit a job to Harvest server cluster.

Configuration File
==================

Harvest Client requires message broker (RabbitMQ) connection to submit jobs to the Harvest server cluster.
Default configuration file, *<INSTALL_DIR>/conf/harvest-client.cfg*, has the following parameters:

.. code-block:: python

   # Message server type. Currently, only 'RabbitMQ' is supported.
   mq.type = RabbitMQ

   # RabbitMQ host(s). One or more host:port tuples (one tuple per line).
   # rmq.host = host1:5672
   # rmq.host = host2:5672
   # rmq.host = host3:5672

   rmq.host = localhost:5672

   # RabbitMQ user
   rmq.user = harvest

   # RabbitMQ password
   rmq.password = harvest

You can either edit default configuration file, or create another file and pass it to Harvest Client CLI as a parameter.


Submit a Job
============

To submit a job to the harvest server cluster you need a job configuration file.
An example configuration file is available in the installation directory:
*<INSTALL_DIR>/examples/directories.xml*.

You will need to update the nodeName:

.. code-block:: xml

    <harvest nodeName="PDS_GEO">

The path to the data.

.. code-block:: xml

  <directories>
    <path>/data/geo/urn-nasa-pds-kaguya_grs_spectra</path>
  </directories>

.. note::
   Crawler and Harvest servers should be able to read this path.

And the URL prefix for the data:

.. code-block:: xml

  <fileInfo>
    <!-- UPDATE with your own local path and base url where pds4 archive is published -->
    <fileRef replacePrefix="/data/geo/" with="https://pds-geosciences.wustl.edu/lunar/" />
  </fileInfo>

If you save this file as */tmp/job1.xml* and run Harvest Client::

   <INSTALL_DIR>/bin/harvest-client harvest -j /tmp/job1.xml

You should see output similar to this::

   [INFO] Reading job from /tmp/job1.xml
   [INFO] Reading configuration from /tmp/big-data-harvest-client-1.0.0/conf/harvest-client.cfg
   [INFO] Creating new job...
   [INFO] Connecting to RabbitMQ
   [INFO] Created job f282a012-115e-429c-b445-f5eed1d81303


After submitting a job, you can monitor progress by querying OpenSearch::

   curl "http://localhost:9200/registry/_search?q=_package_id:f282a012-115e-429c-b445-f5eed1d81303"

.. note::
   For backward compatibility, job ID field is called "_package_id" in OpenSearch.

This `page <./harvest_job_configuration.html>`_ describes the job configuration file in detail.


Next Steps
**********
When ready for public release, you need to `update the archive status <update_status.html>`_
