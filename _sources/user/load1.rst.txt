==============================
Load Data - Standalone Harvest
==============================

Overview
********

To load PDS4 data into Registry you have to use Harvest software. There are two versions of Harvest:
a simple standalone command-line tool and a scalable Harvest which can process big data sets in parallel thanks to distributed components comminucating through a message broker.
Both versions extract metadata from PDS4 products (labels) and load extracted
metadata into OpenSearch database.

This document describes how to load data with Standalone Harvest command-line tool.


Prerequisites
*************

  * OpenSearch server is `running <https://opensearch.org/>`_.
  * Registry indices are `created <../admin/create_reg.html#create-registry>`_ in OpenSearch.
  * Standalone Harvest command-line tool is `installed <../install/tools.html#standalone-harvest>`_.


Standalone Harvest Quick Start
******************************

To run Harvest you need a job configuration file (XML).
The configuration file has several sections such as Registry (OpenSearch) configuration
and the path to the data. Example configuration files are located in *<INSTALL_DIR>/conf/examples*.

The most useful configuration for an Harvest's job is *conf/examples/directories.xml*. You will want to update the nodeName:

.. code-block:: xml

  <harvest nodeName="PDS_GEO">


Registry (OpenSearch) configuration:

.. code-block:: xml

  <registry url="http://localhost:9200" index="registry" auth="/path/to/auth.cfg" />

The path to the data:

.. code-block:: xml

  <directories>
    <path>/data/geo/urn-nasa-pds-kaguya_grs_spectra</path>
  </directories>

And the URL prefix for the data:

.. code-block:: xml

  <fileInfo>
    <!-- UPDATE with your own local path and base url where pds4 archive is published -->
    <fileRef replacePrefix="/data/geo/" with="https://pds-geosciences.wustl.edu/lunar/" />
  </fileInfo>

If you save this file as */tmp/kaguya.cfg* and run Harvest

.. code-block:: python

   harvest -c /tmp/kaguya.cfg

all XML files in */data/orex/orex_spice* folder and its subfolders will be processed.
All metadata from PDS4 labels will be extracted and loaded into Registry (OpenSearch).

You will see multiple log messages similar to these:

.. code-block:: python

  ...
  [INFO] Processing C:\Geo\kaguya_grs_spectra\data_ephemerides\kgrs_ephemerides.xml
  [INFO] Processing C:\Geo\kaguya_grs_spectra\data_spectra\kgrs_calibrated_spectra_per1.xml
  [INFO] Processing C:\Geo\kaguya_grs_spectra\data_spectra\kgrs_calibrated_spectra_per2.xml
  [INFO] Processing C:\Geo\kaguya_grs_spectra\data_spectra\kgrs_calibrated_spectra_per3.xml
  [INFO] Processing C:\Geo\kaguya_grs_spectra\data_spectra\spectra_data_collection_inventory.xml
  ...
  [SUMMARY] Summary:
  [SUMMARY] Skipped files: 0
  [SUMMARY] Processed files: 14
  [SUMMARY] File counts by type:
  [SUMMARY]   Product_Bundle: 1
  [SUMMARY]   Product_Collection: 4
  [SUMMARY]   Product_Context: 3
  [SUMMARY]   Product_Document: 2
  [SUMMARY]   Product_Observational: 4
  [SUMMARY] Package ID: e46f6ba9-6151-48ee-b822-b0536e3e4bd9


To quickly check that data was loaded you can query Registry indices in OpenSearch by calling
`OpenSearch Search API <https://opensearch.org/docs/latest/opensearch/query-dsl/index/>`_
or in a web browser. For example,

.. code-block:: python

   # Select all products
   curl "http://localhost:9200/registry/_search?q=*&amp;pretty"

   # Select only collections
   curl "http://localhost:9200/registry/_search?q=product_class:Product_Collection&amp;pretty"

This `page <./harvest_job_configuration.html>`_ describes the job configuration file in detail.
