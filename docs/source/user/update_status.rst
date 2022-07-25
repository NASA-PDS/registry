=====================
Update Archive Status
=====================

When a product is ingested into PDS Registry, its archive status is set to *"staged"*.

.. code-block:: javascript

  "ops:Tracking_Meta/ops:archive_status": "staged"

You can change that value to any of the following:

 * archived
 * certified
 * restricted
 * staged

You can use either Registry Manager or Harvest Client (Scalable Harvest deployments only) for this task.

Registry Manager
*****************

Prerequisites
=============

  * OpenSearch server is `running <https://opensearch.org/>`_.
  * Registry indices are `created <../admin/create_reg.html#create-registry>`_ in OpenSearch.
  * Some data is `ingested <./load1.html>`_ into the Registry.
  * Registry Manager command-line tool is `installed <../install/tools.html#registry-manager>`_.


Set status
===========

To set product archive status, execute Registry Manager's "set-archive-status" command.

The following parameters are required:

 * **-status <status>** - New status. Pass one of the following values: "archived", "certified", "restricted", "staged".
 * **-lidvid <id>** - LIDVID of a product to update. If the product is a collection product,
   all primary references from the collection inventory will be also updated.
   If the product is a bundle product, all bundle's collections will be also updated.

Optional parameters:

 * **-es <url>** - OpenSearch URL. Default URL is "http://localhost:9200".
 * **-index <name>** - OpenSearch index name. Default value is 'registry'.
 * **-auth <file>** - OpenSearch authentication configuration file. See example below.

**Examples:**

Update local Registry / OpenSearch (http://localhost:9200), no authentication.

.. code-block:: bash

   registry-manager set-archive-status \
       -status archived
       -lidvid "urn:nasa:pds:kaguya_grs_spectra:document::1.0"

Update remote Registry / OpenSearch

.. code-block:: bash

   registry-manager set-archive-status \
       -status archived
       -lidvid "urn:nasa:pds:kaguya_grs_spectra:document::1.0" \
       -es https://my-host.my-domain:9999 \
       -auth /my/path/auth.cfg

.. Note::
   In the -es value, have always the port especially if the port is 443 (default HTTPS) or 80 (default HTTP) since otherwise harvest would make default port 9200, which is the default OpenSearch port.

If your OpenSearch server requires authentication, you have to create an authentication configuration
file and provide following parameters:

.. code-block:: python

   # true - trust self-signed certificates; false - don't trust.
   trust.self-signed = true
   user = pds-user1
   password = mypassword


Harvest Client (Scalable Harvest only)
**************************************

Prerequisites
=============

  * OpenSearch server is `running <https://opensearch.org/>`_.
  * Registry indices are `created <../admin/create_reg.html#create-registry>`_ in OpenSearch.
  * Some data is `ingested <./load2.html>`_ into the Registry.
  * All server components - RabbitMQ, Crawler Server, Harvest Server - are deployed and running on-prem or in the cloud.
  * Harvest Client command-line tool is `installed <../install/tools.html#harvest-client>`_.


Set status
===========

To set product archive status, execute Harvest Client's "set-archive-status" command.

The following parameters are required:

 * **-status <status>** - New status. Pass one of the following values: "archived", "certified", "restricted", "staged".
 * **-lidvid <id>** - LIDVID of a product to update. If the product is a collection product,
   all primary references from the collection inventory will be also updated.
   If the product is a bundle product, all bundle's collections will be also updated.

Optional parameters:

 * **-c <path>** - Harvest Client configuration file. Default is <CLIENT_HOME>/conf/harvest-client.cfg

Usually Harvest Client is configured after the installation. Example configuration is shown below:

.. code-block:: python

  mq.type = RabbitMQ
  # RabbitMQ host(s). One or more host:port tuples (one tuple per line).
  rmq.host = localhost:5672
  # RabbitMQ user
  rmq.user = harvest
  # RabbitMQ password
  rmq.password = harvest


**Examples:**

.. code-block:: bash

   harvest-client set-archive-status \
       -status archived
       -lidvid "urn:nasa:pds:kaguya_grs_spectra:document::1.0"
