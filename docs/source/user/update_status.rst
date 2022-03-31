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


Prerequisites - Registry Manager
********************************

  * Elasticsearch server is running.
  * Registry indices are created in Elasticsearch.
  * Some data is ingested into the Registry.
  * Registry Manager command-line tool is installed.

Prerequisites - Harvest Client
******************************

  * Elasticsearch server is running.
  * Registry indices are created in Elasticsearch.
  * Some data is ingested into the Registry.
  * All server components - RabbitMQ, Crawler Server, Harvest Server - are deployed and running on-prem or in the cloud.
  * Harvest Client command-line tool is installed.


Registry Manager
****************

To set product archive status, execute Registry Manager's "set-archive-status" command.

The following parameters are required:

 * **-status <status>** - New status. Pass one of the following values: "archived", "certified", "restricted", "staged".
 * **-lidvid <id>** - LIDVID of a product to update. If the product is a collection product, 
   all primary references from the collection inventory will be also updated.
   If the product is a bundle product, all bundle's collections will be also updated.

Optional parameters:

 * **-es <url>** - Elasticsearch URL. Default URL is "http://localhost:9200".
 * **-index <name>** - Elasticsearch index name. Default value is 'registry'.
 * **-auth <file>** - Elasticsearch authentication configuration file. See example below.

**Examples:**

Update local Registry / Elasticsearch (http://localhost:9200), no authentication.

.. code-block:: bash

   registry-manager set-archive-status \
       -status archived 
       -lidvid "urn:nasa:pds:kaguya_grs_spectra:document::1.0"

Update remote Registry / Elasticsearch

.. code-block:: bash

   registry-manager set-archive-status \
       -status archived 
       -lidvid "urn:nasa:pds:kaguya_grs_spectra:document::1.0" \
       -es https://my-host.my-domain:9999 \
       -auth /my/path/auth.cfg

If your Elasticsearch server requires authentication, you have to create an authentication configuration 
file and provide following parameters:

.. code-block:: python

   # true - trust self-signed certificates; false - don't trust.
   trust.self-signed = true
   user = pds-user1
   password = mypassword


Harvest Client (Scalable Harvest only)
**************************************

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

