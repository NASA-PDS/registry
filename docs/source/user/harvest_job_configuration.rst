==============================
Detailed Harvest Configuration
==============================

Reference for all Harvest job configuration file options.
For basic setup see :doc:`/user/load1`.


Input: Directories
******************

Load products from one or more directories:

.. code-block:: xml

  <harvest>
    ...
    <load>
      <directories>
        <path>/some-directory/sub-dir-1/</path>
        <path>/some-directory/sub-dir-2/</path>
      </directories>
    </load>
    ...
  </harvest>

.. note::
   ``<directories>`` and ``<bundles>`` cannot both be present in the same config.


Input: File Manifest
********************

To load a specific list of files:

1. Create a manifest file with one file path per line:

   .. code-block:: text

     /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ05.xml
     /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ07.xml
     /data/d1/CCF_0088_0674757853_190FDR_N0040048CACH00100_0A10LLJ09.xml

2. Reference the manifest in the config:

   .. code-block:: xml

     <harvest>
       ...
       <load>
         <files>
           <manifest>/some-directory/manifest.txt</manifest>
         </files>
       </load>
       ...
     </harvest>


Input: Bundles
**************

*(command-line Harvest only)*

Load products from one or more bundles:

.. code-block:: xml

  <harvest>
    ...
    <load>
      <bundles>
        <bundle dir="/data/geo/urn-nasa-pds-kaguya_grs_spectra" />
        <bundle dir="/data/geo/urn-nasa-pds-trang2020_moon_space_weathering" />
      </bundles>
    </load>
    ...
  </harvest>

.. note::
   ``<directories>`` and ``<bundles>`` cannot both be present in the same config.


Filtering by Product Class
**************************

Include only a specific class:

.. code-block:: xml

  <harvest>
    ...
    <productFilter>
      <includeClass>Product_Document</includeClass>
    </productFilter>
    ...
  </harvest>

Exclude a specific class:

.. code-block:: xml

  <harvest>
    ...
    <productFilter>
      <excludeClass>Product_Document</excludeClass>
    </productFilter>
    ...
  </harvest>

.. note::
   ``<includeClass>`` and ``<excludeClass>`` cannot both be present at the same time.


Filtering Bundle Versions
*************************

*(command-line Harvest only)*

Use the ``versions`` attribute to limit which bundle versions are processed.
Separate multiple versions with a comma, semicolon, or space:

.. code-block:: xml

  <bundle dir="/data/OREX/orex_spice" versions="7.0;8.0" />

To process all versions:

.. code-block:: xml

  <bundle dir="/data/OREX/orex_spice" versions="all" />


Filtering Bundle Collections
****************************

*(command-line Harvest only)*

By default all collections in a bundle are processed. Filter by LID or LIDVID:

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


Filtering Product Directories Within a Bundle
*********************************************

*(command-line Harvest only)*

To process only a subset of products, specify a substring of the relative directory path:

.. code-block:: xml

  <bundle dir="/data/OREX/orex_spice" versions="8.0" >
    <product dir="/fk/" />
  </bundle>


File Reference / Access URL
****************************

Harvest records the absolute local path of each file, e.g.:

.. code-block:: text

  "ops:Label_File_Info/ops:file_ref": "/tmp/d5/naif0012.xml"

To replace a local path prefix with a public URL, add a ``<fileRef>`` entry:

.. code-block:: xml

  <fileInfo>
    <fileRef replacePrefix="/tmp/d5/"
             with="https://naif.jpl.nasa.gov/pub/naif/pds/pds4/orex/orex_spice/" />
  </fileInfo>

Result:

.. code-block:: text

  "ops:Label_File_Info/ops:file_ref":
      "https://naif.jpl.nasa.gov/pub/naif/pds/pds4/orex/orex_spice/bundle_orex_spice_v009.xml"

.. note::
   On Windows, backslashes in paths are automatically replaced with forward slashes,
   and the drive letter is included (e.g. ``C:/tmp/d4/...``).


Registry Connection
********************

Configure the OpenSearch connection and auth files (see :doc:`/connection-setup`):

.. code-block:: xml

  <harvest>
    ...
    <registry auth="$HOME/.pds/registry-auth-{venue}.txt">file://$HOME/.pds/registry-config-{node}-{venue}.xml</registry>
    ...
  </harvest>


Label and Data File Information
********************************

*(command-line Harvest only)*

By default, Harvest extracts file metadata (name, MIME type, size, MD5 hash) for both label and data files:

.. code-block:: text

  "ops:Label_File_Info/ops:file_name": "naif0012.xml",
  "ops:Label_File_Info/ops:file_size": "3398",
  "ops:Label_File_Info/ops:md5_checksum": "69ea2974a93854d90399b8b8fc3d1334"

To skip data file processing:

.. code-block:: xml

  <fileInfo processDataFiles="false" />


BLOB Storage
*************

*(command-line Harvest only)*

By default, Harvest stores each PDS4 label as a compressed BLOB in both XML and JSON formats
(fields ``ops/Label_File_Info/ops/blob`` and ``ops/Label_File_Info/ops/json_blob``).

To extract a stored label, use Registry Manager:

.. code-block:: bash

  registry-manager export-file \
      -lidvid urn:nasa:pds:ladee_ldex:data_calibrated::1.2 \
      -file /tmp/data_calibrated.xml

To disable BLOB storage:

.. code-block:: xml

  <fileInfo storeLabels="false" storeJsonLabels="false" />


Extract Metadata by XPath
**************************

*(command-line Harvest only)*

To extract custom fields using XPath, create one or more mapping files and reference them in the config:

.. code-block:: xml

  <harvest>
    ...
    <xpathMaps baseDir="/home/pds/harvest/conf">
      <xpathMap filePath="common.xml" />
      <xpathMap rootElement="Product_Observational" filePath="observational.xml" />
    </xpathMaps>
  </harvest>

- ``filePath`` — path to a mapping file (absolute, or relative to ``baseDir``).
- ``rootElement`` — if set, only XML documents with that root element are processed by this mapping.

Mapping File Format
===================

Each entry maps an output field name to an XPath expression:

.. code-block:: xml

  <?xml version="1.0" encoding="UTF-8"?>
  <xpaths>
    <xpath fieldName="start_date_time">/Product_Observational/Observation_Area/Time_Coordinates/start_date_time</xpath>
    <xpath fieldName="stop_date_time">/Product_Observational/Observation_Area/Time_Coordinates/stop_date_time</xpath>
  </xpaths>

Add ``dataType="date"`` to convert PDS date strings to ISO-8601 format:

.. code-block:: xml

  <xpaths>
    <xpath fieldName="start_date_time"
           dataType="date">/Product_Observational/Observation_Area/Time_Coordinates/start_date_time</xpath>
  </xpaths>

XML Namespaces
==============

Harvest ignores namespaces in XPath expressions. For example, given a label with:

.. code-block:: xml

  <Mission_Area>
    <ladee:latitude>17.2367925372247</ladee:latitude>
    <ladee:longitude>194.054477731391</ladee:longitude>
  </Mission_Area>

Use namespace-free XPaths:

.. code-block:: xml

  <xpaths>
    <xpath fieldName="latitude">//Mission_Area/latitude</xpath>
    <xpath fieldName="longitude">//Mission_Area/longitude</xpath>
  </xpaths>
