===============
Data Dictionary
===============

.. warning:: this task is now done automatically by the `registry-sweepers <https://github.com/NASA-PDS/registry-sweepers>`_

Overview
********

Data Dictionary provides field definitions for all metadata fields which can be stored in PDS Registry.
Data type information is required to properly parse date and numeric fields.

When a registry is created, the registry data dictionary is populated with PDS common and few discipline dictionaries.
Latest versions of PDS4 data dictionaries are available at
`PDS website <https://pds.nasa.gov/datastandards/dictionaries/>`_.

When loading data, the Harvest tool will try to download and install data dictionaries listed in PDS4 label's **xsi:schemaLocation**
attribute::

  <Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1"
      xmlns:cart="http://pds.nasa.gov/pds4/cart/v1"
      xmlns:disp="http://pds.nasa.gov/pds4/disp/v1"
      xmlns:mars2020="http://pds.nasa.gov/pds4/mission/mars2020/v1"
      ...
      xsi:schemaLocation="
          http://pds.nasa.gov/pds4/pds/v1 https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1G00.xsd
          http://pds.nasa.gov/pds4/disp/v1 https://pds.nasa.gov/pds4/disp/v1/PDS4_DISP_1G00_1500.xsd
          http://pds.nasa.gov/pds4/cart/v1 https://pds.nasa.gov/pds4/cart/v1/PDS4_CART_1G00_1950.xsd
          ...

Usually you don't need to load data dictionaries manually if they are listed in PDS4 label's **xsi:schemaLocation** attribute.


Prerequisites
*************

 * The connection to the registry service is set up. See :doc:`/connection-setup`
 * Registry Manager command-line tool is `installed <../install/tools.html#registry-manager>`_.


List Installed Data Dictionaries
********************************

To list all data dictionaries in the Registry run the following command:


.. code-block:: bash

  registry-manager list-dd \
    -es file:///path/to/connection.xml \
    -auth /my/path/auth.cfg


You will see the list similar to this::

  Namespace            File                                        Version   Date
  -----------------------------------------------------------------------------------------------
  cart                 PDS4_CART_1F00_1950.JSON                   1.15.0.0   2020-12-21T21:48:19Z
  disp                 PDS4_DISP_1F00_1500.JSON                   1.15.0.0   2020-12-15T22:09:58Z
  geom                 PDS4_GEOM_1F00_1910.JSON                   1.15.0.0   2021-01-12T00:37:40Z
  img                  PDS4_IMG_1F00_1810.JSON                    1.15.0.0   2020-10-14T02:55:04Z
  img_surface          PDS4_IMG_SURFACE_1F00_1240.JSON            1.15.0.0   2021-01-12T00:56:39Z
  msn                  PDS4_MSN_1F00_1300.JSON                    1.15.0.0   2020-10-14T02:55:21Z
  msn_surface          PDS4_MSN_SURFACE_1F00_1200.JSON            1.15.0.0   2020-10-14T02:55:29Z
  particle             PDS4_PARTICLE_1G00_2010.JSON               1.16.0.0   2021-08-05T21:40:47Z
  pds                  PDS4_PDS_1F00.JSON                         1.15.0.0   2020-12-23T15:16:28Z
  proc                 PDS4_PROC_1F00_1210.JSON                   1.15.0.0   2020-12-09T03:22:22Z
  rings                PDS4_RINGS_1F00_1A00.JSON                  1.15.0.0   2020-12-02T19:08:01Z
  sp                   PDS4_SP_1F00_1300.JSON                     1.15.0.0   2020-11-03T19:47:46Z


Load PDS Data Dictionary Files
******************************

To load standard PDS4 data dictionary JSON file, for example, *orex_ldd_OREX_1300.JSON*,
run the following command:

.. code-block:: bash

  registry-manager load-dd \
    -dd /home/pds/schema/orex_ldd_OREX_1300.JSON
    -es file:///path/to/connection.xml \
    -auth /my/path/auth.cfg



Upgrade Data Dictionary
***********************

Data dictionaries can change between major releases of the registry and/or its tools and APIs, necessitating an
upgrade. To perform this, run the following command:

.. code-block:: bash

  registry-manager upgrade-dd \
    -es file:///path/to/connection.xml \
    -auth /my/path/auth.cfg

The above command will replace entries in the data dictionary on a document by document basis (i.e. those in the
data dictionary having the same _id's as the incoming documents). This is relevant if you have loaded your own data
dictionary files (see 'load-dd' above), in which case the upgrade will retain those additional documents.

If you wish to replace the entire data dictionary, add the '-r' (recreate) command line switch:

.. code-block:: bash

  registry-manager upgrade-dd -r
    -es file:///path/to/connection.xml \
    -auth /my/path/auth.cfg

This ensures that legacy documents that are no longer applicable are removed.
