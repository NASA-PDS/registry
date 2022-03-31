============================
Load Data - Scalable Harvest
============================

Overview
********

To load PDS4 data into Registry you have to use Harvest software. There are two versions of Harvest:
a simple standalone command-line tool and a scalable Harvest consisting of several server and and
client components. Scalable Harvest can process big data sets in parallel. 
Both versions extract metadata from PDS4 products (labels) and load extracted
metadata into Elasticsearch database. 

This document describes how to use Harvest Client command-line tool to submit jobs to Scalable Harvest Server cluster.


Prerequisites
*************

* Elasticsearch server is running.
* Registry indices are created in Elasticsearch.
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


After submitting a job, you can monitor progress by querying Elasticsearch::

   curl "http://localhost:9200/registry/_search?q=_package_id:f282a012-115e-429c-b445-f5eed1d81303"

.. note::
   For backward compatibility, job ID field is called "_package_id" in Elasticsearch.

The following sections describe job configuration file in more detail.


Node Name
*********

Node name is a required parameter which is used to tag ingested data with the node it is ingested by.

.. code-block:: xml

   <harvest nodeName="PDS_SBN">
   ...

One of the following values can be used:

  * **PDS_ATM**  - Planetary Data System: Atmospheres Node
  * **PDS_ENG**  - Planetary Data System: Engineering Node
  * **PDS_GEO**  - Planetary Data System: Geosciences Node
  * **PDS_IMG**  - Planetary Data System: Imaging Node
  * **PDS_NAIF** - Planetary Data System: NAIF Node
  * **PDS_RMS**  - Planetary Data System: Rings Node
  * **PDS_SBN**  - Planetary Data System: Small Bodies Node at University of Maryland
  * **PSA**      - Planetary Science Archive
  * **JAXA**     - Japan Aerospace Exploration Agency
  * **ROSCOSMOS** - Russian State Corporation for Space Activities

This value is saved in "ops:Harvest_Info/ops:node_name" field in Elasticsearch document:

.. code-block:: javascript

   {
      ...
      "ops:Harvest_Info/ops:node_name": "PDS_SBN",
      ...
   }


Input Directories and Filters
*****************************

Process Directories
===================

To process products from one or more directories, add the following section in job configuration file:

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <directories>
      <path>/some-directory/sub-dir-1/</path>
      <path>/some-directory/sub-dir-2/</path>
    </directories>
    ...
  </harvest>

.. note::
   Crawler and Harvest server should be able to read these paths.


Process a List of Files
=======================

First, create a manifest file and list all files you want to process. One file path per line::

   /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ05.xml
   /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ07.xml
   /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ09.xml

Next, add the following section in job configuration file:

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
  ...
  <files>
    <manifest>/some-directory/manifest.txt</manifest>
  </files>
  ...
  </harvest>

.. note::
   Crawler and Harvest server should be able to read these paths (including manifest file).


Filtering Products by Class
===========================

You can include or exclude products of a particular class. For example, to only process documents, add following 
product filter in job configuration file:

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <productFilter>
      <includeClass>Product_Document</includeClass>
    </productFilter>
    ...
  </harvest>

To exclude documents, add following product filter:

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <productFilter>
      <excludeClass>Product_Document</excludeClass>
    </productFilter>
    ...
  </harvest>

.. note::
   You could not have both include and exclude filters at the same time.


File Reference / Access URL
***************************

Harvest extracts absolute paths of product and label files, such as

.. code-block:: javascript

  "ops:Label_File_Info/ops:file_ref":"/tmp/d5/naif0012.xml",
  "ops:Data_File_Info/ops:file_ref":"/tmp/d5/naif0012.tls",

Note that on Windows, backslashes are replaced with forward slashes and disk letter is included.

.. code-block:: javascript

  "ops:Label_File_Info/ops:file_ref":"C:/tmp/d4/bundle_orex_spice_v009.xml",

To replace a file path prefix with another value, such as a URL, add <fileRef/> tag in job configuration file:

.. code-block:: xml

  <fileInfo>
    <fileRef replacePrefix="/C:/tmp/d4/" 
             with="https://naif.jpl.nasa.gov/pub/naif/pds/pds4/orex/orex_spice/" />
  </fileInfo>

After running Harvest, you should get different *file_ref* value:

.. code-block:: javascript

  "ops:Label_File_Info/ops:file_ref":
      "https://naif.jpl.nasa.gov/pub/naif/pds/pds4/orex/orex_spice/bundle_orex_spice_v009.xml"

