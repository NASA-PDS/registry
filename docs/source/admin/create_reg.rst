========================
Create / Delete Registry
========================

Overview
********

Indices must be created in OpenSearch, before running the registry.

The indices used by the registry are:

 * **<node prefix>-registry** - this index stores metadata extracted from PDS4 labels, one ES document per PDS label.
 * **<node prefix>-registry-dd** - this index stores data dictionary - a list of searchable fields and its data types.
   When registry is created, the registry data dictionary is populated with PDS common and few discipline dictionaries.
   Harvest automatically loads new dictionaries from schema location specified in PDS4 labels.
   You can also add more fields and LDDs manually with Registry Manager tool.
 * **<node prefix>-registry-refs** - this index stores product references extracted from collection inventory files.
   There could be 1 or more ES documents per inventory file.

Where the node prefix is: atm, en, geo, img, naif, ppi, psa, rms, sbnpsi or sbnumd.

The indices are created with Registry Manager command-line tool.


Prerequisites
*************

 * The connection to the registry service is set up. See :doc:`/connection-setup`
 * Registry Manager command-line tool is `installed <../install/tools.html#registry-manager>`_.


Create Registry
***************

To create registry indices run Registry Manager's "create-registry" command.
You can pass the following optional parameters:

 * **-es <url>** - link to the connection configuration file described in :doc:`/connection-setup`
 * **-auth <file>** - OpenSearch authentication configuration file. See :doc:`/connection-setup`.

Only applicable for local deployment, e.g. for development of test purpose:

 * **-shards <number>** - Number of shards (partitions) for registry index. Default value is 1.
 * **-replicas <number>** - Number of replicas (extra copies) of registry index. Default value is 0.


Example
========

Create Registry indices in remote OpenSearch.

.. code-block:: python

   registry-manager create-registry \
       -es file:///path/to/connection.xml \
       -auth /my/path/auth.cfg



Check that indices were created
===============================

To check that registry indices were created, call the following OpenSearch REST API:
http://localhost:9200/_cat/indices?v

Update OpenSearch URL and pass user name and password if needed.

.. code-block:: bash

   curl "http://localhost:9200/_cat/indices?v"

The response should look similar to this. Make sure that each index health is "green".

.. code-block:: bash

  health status index         uuid                   pri rep docs.count docs.deleted store.size pri.store.size
  green  open   geo-registry      PY6ObzELRlSx9gHOWbR8dw   1   0          0            0       208b           208b
  green  open   geo-registry-dd   CuJ-nqg1SbKI9hejHrISWA   1   0       2505            0      625kb          625kb
  green  open   geo-registry-refs 1cJLc-9cQj2D_MAYo7gOpw   1   0          0            0       208b           208b


Delete Registry
***************

To delete registry indices, run Registry Manager's "delete-registry" command.
You can pass the following optional parameters:

 * **-es <url>** - link to the connection configuration file described in :doc:`/connection-setup`
 * **-auth <file>** - OpenSearch authentication configuration file. See :doc:`/connection-setup`.
