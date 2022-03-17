========================
Create / Delete Registry
========================

Overview
********

You must create following registry indices in Elasticsearch, before running any Harvest server or 
client components, such as Crawler Server, Harvest Server, Standalone Harvest CLI or Harvest Client CLI.

 * **registry** - this index stores metadata extracted from PDS4 labels, one ES document per PDS label.
 * **registry-dd** - this index stores data dictionary - a list of searchable fields and its data types.
   When registry is created, the data dictionary is populated with fields (attributes) from PDS common and few discipline dictionaries.
   Harvest automatically loads new dictionaries from schema location specified in PDS4 labels.
   You can also add more fields and LDDs manually as described in <a href="reg-custom.html#DD">Registry Customization / Data Dictionary</a> section.
 * **registry-refs** - this index stores product references extracted from collection inventory files.
   There could be 1 or more ES documents per inventory file.

The indices are created with Registry Manager command-line tool.


Prerequisites
*************

 * Elasticsearch server is running.
 * Registry Manager command-line tool is installed.


Create Registry
***************

To create registry indices in local Elasticsearch (running at *http://localhost:9200*) 
with 1 shard and 0 replicas, run the following Registry Manager command

.. code-block:: python

   registry-manager create-registry

You can customize *create-registry* command by passing several parameters, 
such as Elasticsearch URL, number of shards and replicas, authentication parameters.
To see the list of available parameters and basic usage run

.. code-block:: bash

   registry-manager create-registry -help

To check that registry indices were created open the following URL in 
a browser: *http://localhost:9200/_cat/indices?v* or use *curl*.

.. code-block:: bash

   curl "http://localhost:9200/_cat/indices?v"

The response should look similar to this. Make sure that index status is "green". 

.. code-block:: bash

  health status index         uuid                   pri rep docs.count docs.deleted store.size pri.store.size
  green  open   registry      PY6ObzELRlSx9gHOWbR8dw   1   0          0            0       208b           208b
  green  open   registry-dd   CuJ-nqg1SbKI9hejHrISWA   1   0       2505            0      625kb          625kb
  green  open   registry-refs 1cJLc-9cQj2D_MAYo7gOpw   1   0          0            0       208b           208b


Delete Registry
***************

To delete registry indices from local Elasticsearch run the following command:

.. code-block:: python

   registry-manager delete-registry

You can customize *delete-registry* command by passing several parameters, 
such as Elasticsearch URL, and authentication parameters.

