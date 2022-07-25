===========
Delete Data
===========

Overview
********

You can delete data from PDS Registry (OpenSearch) with Registry Manager command-line tool.

Prerequisites
*************

 * OpenSearch server is running.
 * Registry Manager command-line tool is installed.


Delete Data
***********

To delete data, run Registry Manager's "delete-data" command.

You have to pass one of the following parameters:

 * **-lidvid <id>** - Delete data by lidvid
 * **-lid <id>** - Delete data by lid
 * **-packageId <id>** - Delete data by package / job id
 * **-all** - Delete all data

You can also pass optional parameters:

 * **-es <url>** - OpenSearch URL. Default URL is "http://localhost:9200".
 * **-index <name>** - OpenSearch index name. Default value is 'registry'.
 * **-auth <file>** - OpenSearch authentication configuration file. See example below.

Examples
********

**Delete by LIDVID**

.. code-block:: bash

  registry-manager delete-data \
      -lidvid urn:nasa:pds:context:target:asteroid.4_vesta::1.1 \
      -es https://my-server.my-domain.com:9999 \
      -index registry \
      -auth path/to/auth.cfg

.. Note::
   In the -es option value, have always the port especially if the port is 443 (default HTTPS) or 80 (default HTTP) since harvest will believe default port is 9200 which is the default OpenSearch port.

If your OpenSearch server requires authentication, you have to create an authentication configuration file
and provide following parameters:

.. code-block:: python

  # true - trust self-signed certificates; false - don't trust.
  trust.self-signed = true
  user = pds-user1
  password = mypassword

**Delete by LID**

.. code-block:: bash

  registry-manager delete-data \
      -lid urn:nasa:pds:context:target:asteroid.4_vesta
      -es http://localhost:9200

**Delete by Package / Job ID**

.. code-block:: bash

  registry-manager delete-data \
      -packageId 8d8ae96d-044e-473d-a278-62635b1c5977

**Delete all Data**

.. code-block:: bash

  registry-manager delete-data -all -index test1


OpenSearch API
*****************

.. warning::
    Only use this if you really know what you are doing and how to do it.

You can also use OpenSearch
`delete by query API <https://opensearch.org/docs/latest/opensearch/rest-api/document-apis/delete-by-query/>`_
to delete documents from the Registry / OpenSearch.
