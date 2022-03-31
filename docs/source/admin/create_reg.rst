========================
Create / Delete Registry
========================

Overview
********

You must create following registry indices in Elasticsearch, before running any Harvest server or 
client components, such as Crawler Server, Harvest Server, Standalone Harvest CLI or Harvest Client CLI.

 * **registry** - this index stores metadata extracted from PDS4 labels, one ES document per PDS label.
 * **registry-dd** - this index stores data dictionary - a list of searchable fields and its data types.
   When registry is created, the registry data dictionary is populated with PDS common and few discipline dictionaries.
   Harvest automatically loads new dictionaries from schema location specified in PDS4 labels.
   You can also add more fields and LDDs manually with Registry Manager tool.
 * **registry-refs** - this index stores product references extracted from collection inventory files.
   There could be 1 or more ES documents per inventory file.

The indices are created with Registry Manager command-line tool.


Prerequisites
*************

 * Elasticsearch server is running.
 * Registry Manager command-line tool is installed.


Create Registry
***************

To create registry indices run Registry Manager's "create-registry" command.
You can pass the following optional parameters:

 * **-es <url>** - Elasticsearch URL. Default value is http://localhost:9200
 * **-index <name>** - Elasticsearch index name. Default value is "registry".
 * **-auth <file>** - Elasticsearch authentication configuration file. See example below.
 * **-shards <number>** - Number of shards (partitions) for registry index. Default value is 1.
 * **-replicas <number>** - Number of replicas (extra copies) of registry index. Default value is 0.

.. note:: Default number of shards and replicas is not recommended for production.

Examples
========

Create Registry indices in local Elasticsearch (http://localhost:9200) with default number of shards and replicas.

.. code-block:: python

   registry-manager create-registry


Create Registry indices in remote Elasticsearch with 3 shards and 1 replica.

.. code-block:: python

   registry-manager create-registry \
       -es https://my-host.my-domain:9999 \
       -auth /my/path/auth.cfg \
       -shards 3 \
       -replicas 1


If your Elasticsearch server requires authentication, you have to create an authentication configuration 
file and provide following parameters:

.. code-block:: python

   # true - trust self-signed certificates; false - don't trust.
   trust.self-signed = true
   user = pds-user1
   password = mypassword


Check that indices were created
===============================

To check that registry indices were created, call the following Elasticsearch REST API:
http://localhost:9200/_cat/indices?v

Update Elasticsearch URL and pass user name and password if needed. 

.. code-block:: bash

   curl "http://localhost:9200/_cat/indices?v"

The response should look similar to this. Make sure that each index health is "green". 

.. code-block:: bash

  health status index         uuid                   pri rep docs.count docs.deleted store.size pri.store.size
  green  open   registry      PY6ObzELRlSx9gHOWbR8dw   1   0          0            0       208b           208b
  green  open   registry-dd   CuJ-nqg1SbKI9hejHrISWA   1   0       2505            0      625kb          625kb
  green  open   registry-refs 1cJLc-9cQj2D_MAYo7gOpw   1   0          0            0       208b           208b


Delete Registry
***************

To delete registry indices, run Registry Manager's "delete-registry" command.
You can pass the following optional parameters:

 * **-es <url>** - Elasticsearch URL. Default value is http://localhost:9200
 * **-index <name>** - Elasticsearch index name. Default value is "registry".
 * **-auth <file>** - Elasticsearch authentication configuration file.

Examples
========

Delete registry indices from local Elasticsearch (http://localhost:9200)

.. code-block:: python

   registry-manager delete-registry


