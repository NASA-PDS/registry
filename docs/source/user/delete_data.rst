===========
Delete Data
===========

Overview
********

You can delete data from PDS Registry (Elasticsearch) with Registry Manager command-line tool.

Prerequisites
*************

 * Elasticsearch server is running.
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

 * **-es <url>** - Elasticsearch URL. Default URL is "http://localhost:9200".
 * **-index <name>** - Elasticsearch index name. Default value is 'registry'.
 * **-auth <file>** - Elasticsearch authentication configuration file. See example below.

Examples
********

**Delete by LIDVID**

.. code-block:: bash

  registry-manager delete-data \
      -lidvid urn:nasa:pds:context:target:asteroid.4_vesta::1.1 \
      -es https://my-server.my-domain.com:9999 \
      -index registry \
      -auth path/to/auth.cfg

If your Elasticsearch server requires authentication, you have to create an authentication configuration file
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


Elasticsearch API
*****************

You can also use Elasticsearch 
`delete by query API <https://www.elastic.co/guide/en/elasticsearch/reference/7.8/docs-delete-by-query.html>`_
to delete documents from the Registry / Elasticsearch.

