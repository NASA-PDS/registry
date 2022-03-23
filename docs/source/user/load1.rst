==============================
Load Data - Standalone Harvest
==============================

Overview
********

To load PDS4 data into Registry you have to use Harvest software. There are two versions of Harvest:
a simple standalone command-line tool and a scalable Harvest consisting of several server and and
client components. Scalable Harvest can process big data sets in parallel. 
Both versions extract metadata from PDS4 products (labels) and load extracted
metadata into Elasticsearch database. 

This document describes how to load data with Standalone Harvest command-line tool.


Prerequisites
*************

  * Elasticsearch server is running.
  * Registry indices are created in Elasticsearch.
  * Standalone Harvest command-line tool is installed.


Standalone Harvest Quick Start
******************************

To run Harvest you need an XML configuration file. 
The configuration file has several sections such as Registry (Elasticsearch) configuration
and the path to the data. Example configuration files are located in *<INSTALL_DIR>/conf/examples*.
  
The ideal configurations for Harvest is *conf/examples/directories.xml*. You will want to update the nodeName:

.. code-block:: xml

  <harvest nodeName="PDS_GEO">


Registry (Elasticsearch) configuration:

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
All metadata from PDS4 labels will be extracted and loaded into Registry (Elasticsearch).

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


To quickly check that data was loaded you can query Registry indices in Elasticsearch by calling
`Elasticsearch Search API <https://www.elastic.co/guide/en/elasticsearch/reference/current/search-search.html/>`_
or in a web browser. For example,

.. code-block:: python

   # Select all products
   curl "http://localhost:9200/registry/_search?q=*&amp;pretty"

   # Select only collections
   curl "http://localhost:9200/registry/_search?q=product_class:Product_Collection&amp;pretty"


The following sections describe Harvest configuration file in more detail.


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



Registry Integration
********************

Standalone Harvest tool loads extracted PDS4 metadata into Elasticsearch database.
You have to configure following Elasticsearch parameters:

 * **url** - Registry (Elasticsearch) URL
 * **index** - Elasticsearch index name. This is an optional parameter. Default value is 'registry'.
 * **auth** - Registry (Elasticsearch) authentication configuration file. This is an optional parameter.

Below are few examples:

**Local Elasticsearch instance (localhost)**

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <registry url="http://localhost:9200" index="registry" />
    ...
  </harvest>

**Remote Elasticsearch instance (on-prem or cloud)**

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <registry url="https://es-server.mydomain.com:9999" index="registry" auth="/path/to/auth.cfg" />
    ...
  </harvest>

If your Elasticsearch server requires authentication, you have to create an authentication 
configuration file and provide following parameters:

.. code-block:: python

  # true - trust self-signed certificates; false - don't trust.
  trust.self-signed = true
  user = pds-user1
  password = mypassword


Input Directories and Filters
*****************************

Process Directories
===================

To process products from one or more directories, add the following section in Harvest configuration file:

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
   You could not have both <directories> and <bundles> sections at the same time.


Process a List of Files
=======================

First, create a manifest file and list all files you want to process. One file path per line.

.. code-block:: python

  /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ05.xml
  /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ07.xml
  /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ09.xml

Next, add the following section in Harvest configuration file:

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <files>
      <manifest>/some-directory/manifest.txt</manifest>
    </files>
    ...
  </harvest>


Process Bundles
===============

To process products from one or more bundles, add the following section in Harvest configuration file:

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <bundles>
      <bundle dir="/data/geo/urn-nasa-pds-kaguya_grs_spectra" />
      <bundle dir="/data/geo/urn-nasa-pds-trang2020_moon_space_weathering" />
    </bundles>
    ...
  </harvest>

.. note::
   You could not have both <directories> and <bundles> sections at the same time.


Filtering Bundle Versions
=========================

Use "versions" attribute of the <bundle> tag to list versions of bundles to process.
You can separate versions by comma, semicolon or space.

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <bundles>
      <bundle dir="/data/OREX/orex_spice" versions="7.0;8.0" />
    </bundles>
    ...
  </harvest>

To process all versions you can use either versions="all" or no versions attribute at all.

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
    ...
    <bundles>
      <bundle dir="/data/OREX/orex_spice" versions="all" />
    </bundles>
    ...
  </harvest>


Filtering Bundle's Collections
==============================

By default Harvest will process all collections listed in <Bundle_Member_Entry>
section of a bundle. To process a subset of collections you can provide a list of
lids or lidvids as shown below.

.. code-block:: xml

  <!-- Filter by collection LID -->
  <bundle dir="/data/OREX/orex_spice" versions="8.0" >
      <collection lid="urn:nasa:pds:orex.spice:spice_kernels" />
  </bundle>

  <!-- Filter by collection LIDVID -->
  <bundle dir="/data/OREX/orex_spice" versions="8.0;7.0" >
      <collection lidvid="urn:nasa:pds:orex.spice:spice_kernels::8.0" />
      <collection lidvid="urn:nasa:pds:orex.spice:spice_kernels::7.0" />
  </bundle>


Filtering Bundle's Product Directories
======================================

By default Harvest will process all products listed in the collection inventory file.
To process a subset of products you can provide a list of directories.


.. code-block:: xml

  <bundle dir="/data/OREX/orex_spice" versions="8.0" >
      <!-- Specify a substring in a relative (to the bundle root) directory name.  -->
      <product dir="/fk/" />
  </bundle>


Filtering Products by Class
===========================

You can include or exclude products of a particular class. For example, to only process documents, add following 
product filter in Harvest configuration file:

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


Label and Data File Information
*******************************

By default, Harvest extracts label and data file information, such as file name, mime type, size, and MD5 hash. 

Label:

.. code-block:: javascript

  "ops:Label_File_Info/ops:creation_date_time":"2020-11-18T22:25:05Z",
  "ops:Label_File_Info/ops:file_name":"naif0012.xml",
  "ops:Label_File_Info/ops:file_ref":"/C:/tmp/d5/naif0012.xml",
  "ops:Label_File_Info/ops:file_size":"3398",
  "ops:Label_File_Info/ops:md5_checksum":"69ea2974a93854d90399b8b8fc3d1334"

Data file:

.. code-block:: javascript

  "ops:Data_File_Info/ops:creation_date_time":"2020-11-18T22:25:17Z",
  "ops:Data_File_Info/ops:file_name":"naif0012.tls",
  "ops:Data_File_Info/ops:file_ref":"/C:/tmp/d5/naif0012.tls",
  "ops:Data_File_Info/ops:file_size":"5257",
  "ops:Data_File_Info/ops:md5_checksum":"25a2fff30b0dedb4d76c06727b1895b1",
  "ops:Data_File_Info/ops:mime_type":"text/plain",

If you don't want to process data files, add the following flag in Harvest configuration file.

.. code-block:: xml

  <fileInfo processDataFiles="false" />


BLOB Storage
************

By default, Harvest stores PDS product labels as BLOBs (Binary Large OBjects).
Both original PDS product labels in XML format as well as product labels converted to JSON are stored.
The data is compressed and stored in following fields: *"ops/Label_File_Info/ops/blob"* and *"ops/Label_File_Info/ops/json_blob"*.

You can expect up to 900% compression rate for some files. 
For example, many LADEE housekeeping labels are about 45KB. Compressed BLOB size is about 5KB.
For smaller files, such as collection labels, compression rate is about 350% (5.5KB file is compressed to 1.6KB).

After loading data into Elasticsearch, you can extract original labels by running Registry Manager tool:

.. code-block:: python

  registry-manager export-file \
      -lidvid urn:nasa:pds:ladee_ldex:data_calibrated::1.2 \
      -file /tmp/data_calibrated.xml

To disable BLOB storage, modify *fileInfo* section in Harvest configuration file.

.. code-block:: xml

  <fileInfo storeLabels="false" storeJsonLabels="false" />


File Reference / Access URL
***************************

Harvest extracts absolute paths of product and label files, such as

.. code-block:: javascript

  "ops:Label_File_Info/ops:file_ref":"/tmp/d5/naif0012.xml",
  "ops:Data_File_Info/ops:file_ref":"/tmp/d5/naif0012.tls",

Note that on Windows, backslashes are replaced with forward slashes and disk letter is included.

.. code-block:: javascript

  "ops:Label_File_Info/ops:file_ref":"C:/tmp/d4/bundle_orex_spice_v009.xml",

To replace a file path prefix with another value, such as a URL, add <fileRef/> tag in Harvest configuration file:

.. code-block:: xml

  <fileInfo>
    <fileRef replacePrefix="/C:/tmp/d4/" 
             with="https://naif.jpl.nasa.gov/pub/naif/pds/pds4/orex/orex_spice/" />
  </fileInfo>

After running Harvest, you should get different *file_ref* value:

.. code-block:: javascript

  "ops:Label_File_Info/ops:file_ref":
      "https://naif.jpl.nasa.gov/pub/naif/pds/pds4/orex/orex_spice/bundle_orex_spice_v009.xml"


Extract Metadata by XPath
*************************

To extract metadata by XPath, you have to create one or more mapping files and list them 
in Harvest configuration file as shown below.

.. code-block:: xml

  <harvest nodeName="PDS_SBN">
  ...
    <xpathMaps baseDir="/home/pds/harvest/conf">
      <xpathMap filePath="common.xml" />
      <xpathMap rootElement="Product_Observational" filePath="observational.xml" />
    </xpathMaps>
  </harvest>

In the example above there are two *xpathMap* entries. Each entry must have *filePath* attribute 
pointing to a mapping file. A path can be either absolute or relative to the *baseDir* attribute 
of the *xpathMaps* tag. The *baseDir* attribute is optional. The same example with absolute paths
is shown below.

.. code-block:: xml

  <xpathMaps>
    <xpathMap filePath="/home/pds/harvest/conf/common.xml" />
    <xpathMap rootElement="Product_Observational" 
              filePath="/home/pds/harvest/conf/observational.xml" />
  </xpathMaps>

An *xpathMap* entry can have optional *rootElement* attribute. 
Without this attribute, XPaths queries defined in a mapping file (*common.xml*),
will run against every XML document processed by Harvest.
With *rootElement* attribute, only XMLs with that root element will be processed.


Mapping Files
=============

A mapping file has one or more entries which map an output field name to an XPath query.
For example, to extract *start_date_time* and *stop_date_time* from observational products,
you can use the following file.

.. code-block:: xml

  <?xml version="1.0" encoding="UTF-8"?>
  <xpaths>
    <xpath fieldName="start_date_time">/Product_Observational/Observation_Area/Time_Coordinates/start_date_time</xpath>
    <xpath fieldName="stop_date_time">/Product_Observational/Observation_Area/Time_Coordinates/stop_date_time</xpath>
  </xpaths>
  </source>

You can use optional *dataType="date"* attribute to convert valid PDS dates to 
ISO-8601 "instant" format (e.g., "2013-10-24T00:49:37.457Z").

.. code-block:: xml

  <xpaths>
    <xpath fieldName="start_date_time" 
           dataType="date">/Product_Observational/Observation_Area/Time_Coordinates/start_date_time</xpath>
    <xpath fieldName="stop_date_time" 
           dataType="date">/Product_Observational/Observation_Area/Time_Coordinates/stop_date_time</xpath>
  </xpaths>


XML Name Spaces
===============

Harvest ignores namespaces when extracting metadata by XPath.
Below is a fragment of LADEE UVS product label which uses "ladee" namespace for mission area fields.

.. code-block:: xml

  <Observation_Area>
    <Mission_Area>
      <ladee:latitude>17.2367925372247</ladee:latitude>
      <ladee:longitude>194.054477731391</ladee:longitude> 
      ...

To extract latitude and longitude you can use the following XPaths without namespaces.

.. code-block:: xml

  <xpaths>
    <xpath fieldName="latitude">//Mission_Area/latitude</xpath>
    <xpath fieldName="longitude">//Mission_Area/longitude</xpath>
  </xpaths>

