==============================
Test Your Registry Connection
==============================

Before loading data, verify that you can connect to your Registry OpenSearch index using ``pds-registry-client``.

Before You Begin
~~~~~~~~~~~~~~~~

- Registry Client installed per :doc:`/install/install`
- Configuration files in place per :doc:`/connection-setup`


Activate the Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Linux / macOS:**

1. Activate the Registry Client virtual environment:

   .. code:: bash

      source $HOME/.virtualenvs/pds-registry-client/bin/activate

2. Source your Registry Client environment file:

   .. code:: bash

      source $HOME/.pds/registry-client-{venue}.env

**Windows:**

1. Activate the Registry Client virtual environment:

   .. code:: bat

      %USERPROFILE%\.virtualenvs\pds-registry-client\Scripts\activate

   Environment variables set during :doc:`/connection-setup` are already available.


Run a Heartbeat Check
~~~~~~~~~~~~~~~~~~~~~

Replace ``{node}`` with your node code (e.g. ``en``, ``geo``, ``img``, ``sbnpsi``).

1. Query your index:

   .. code:: bash

      pds-registry-client '/{node}-registry/_search' --pretty

2. A successful response will return JSON with a ``hits`` block, similar to:

   .. code:: text

      {
        "took" : 5,
        "timed_out" : false,
        "hits" : {
          "total" : { "value" : 10000, "relation" : "gte" },
          "hits" : [ ... ]
        }
      }

   .. note::
      If you receive an authentication error or empty response, confirm that:

      - All ``REQUEST_SIGNER_*`` environment variables are set correctly.
      - Your IP address is on the access whitelist (contact pds-operator@jpl.nasa.gov if unsure).
      - Your Cognito password has been changed from the temporary one (see :doc:`/connection-setup`).
