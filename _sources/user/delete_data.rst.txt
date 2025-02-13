===========
Delete Data
===========

Overview
********

You can delete data from PDS Registry (OpenSearch) with Registry Manager command-line tool.

Prerequisites
*************

 * You have access to the Registry Service, see :doc:`/connection-setup`
 * Registry Manager command-line tool is installed, see :doc:`/install/tools`


Delete Data
***********

To delete data, run Registry Manager's "delete-data" command.

You have to pass one of the following parameters:

 * **-lidvid <id>** - Delete data by lidvid
 * **-lid <id>** - Delete data by lid
 * **-packageId <id>** - Delete data by package / job id
 * **-all** - Delete all data
 * **-es <url>** - link to the connection configuration file described in :doc:`/connection-setup`
 * **-auth <file>** - OpenSearch authentication configuration file. See :doc:`/connection-setup`.

Examples
********

On MacOS/Linux
~~~~~~~~~~~~~~~

**Delete by LIDVID**

.. code-block:: bash

  registry-manager delete-data \
      -lidvid urn:nasa:pds:context:target:asteroid.4_vesta::1.1 \
      -auth /Users/loubrieu/Documents/pds/registry/registry-auth.txt \
      -es file:/Users/loubrieu/Documents/pds/registry/mcp_dev.xml


**Delete by LID**

.. code-block:: bash

  registry-manager delete-data \
      -lid urn:nasa:pds:context:target:asteroid.4_vesta
      -auth /Users/loubrieu/Documents/pds/registry/registry-auth.txt \
      -es file:/Users/loubrieu/Documents/pds/registry/mcp_dev.xml

**Delete by Package / Job ID**

.. code-block:: bash

  registry-manager delete-data \
    -auth /Users/loubrieu/Documents/pds/registry/registry-auth.txt \
    -es file:/Users/loubrieu/Documents/pds/registry/mcp_dev.xml \
    -packageId 8d12a9ba-2ba0-4d80-8ce9-65da271ecf89


**Delete all Data**

.. code-block:: bash

  registry-manager delete-data -all \
    -auth /Users/loubrieu/Documents/pds/registry/registry-auth.txt \
    -es file:/Users/loubrieu/Documents/pds/registry/mcp_dev.xml

On Windows
~~~~~~~~~~~

**Delete by LIDVID**

.. code-block:: powershell

  .\registry-manager.bat delete-data
    -auth 'C:\Users\loubrieu\Documents\es-auth.txt'
    -es 'file:///C:\Users\loubrieu\Documents\mcp_dev.xml'
    -lidvid 'urn:nasa:pds:insight_rad:data_derived::7.0'

**Delete by Package / Job ID**

.. code-block:: powershell

  .\registry-manager delete-data \
    -auth /Users/loubrieu/Documents/pds/registry/registry-auth.txt \
    -es file:///C:\Users\loubrieu\Documents\mcp_dev.xml \
    -packageId 8d12a9ba-2ba0-4d80-8ce9-65da271ecf89
