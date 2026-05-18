============
Installation
============

Overview
********

Install the following PDS Registry command-line tools:

* **Registry Manager** — creates and manages Registry indices, data, and LDDs in OpenSearch.
* **Harvest** — extracts metadata from PDS4 labels and loads it into PDS Registry.
* **Registry Client** — handles authentication and request signing for OpenSearch API queries.


Prerequisites
*************

Java
~~~~

Harvest, Registry Manager, and API Server require **Java 17–25**. Java 1.8 and 11 are not supported.

1. Check whether a supported version is already installed:

   .. code:: bash

      java -version

   Expected output (version number may vary):

   .. code:: text

      java 25 2025-09-16 LTS
      Java(TM) SE Runtime Environment (build 25+37-LTS-3491)
      Java HotSpot(TM) 64-Bit Server VM (build 25+37-LTS-3491, mixed mode, sharing)

   .. note::
      If multiple Java versions are installed and none defaults to 17–25, set ``JAVA_HOME`` to point to a supported version before running Harvest or Registry Manager.

2. If a supported version is not installed, download and install **OpenJDK** (recommended) from one of:

   * `jdk.java.net <https://jdk.java.net/>`_
   * `Adoptium Temurin <https://adoptium.net/temurin/releases>`_
   * `Azul Zulu <https://www.azul.com/downloads/zulu-community>`_
   * Most Linux distributions include OpenJDK in their standard package repositories.

   Alternatively, **Oracle JDK** is available at `oracle.com <https://www.oracle.com/java/technologies/>`_ (requires registration and license acceptance).


Python
~~~~~~

Registry Client requires Python 3.13 or higher.

1. Check your Python version:

   .. code:: bash

      python3 --version

2. If Python 3.13+ is not installed, follow the `installation guide on GitHub Discussions <https://github.com/orgs/NASA-PDS/discussions/64>`_.


Tools
*****

Registry Manager
~~~~~~~~~~~~~~~~

1. Download the latest stable release from https://github.com/NASA-PDS/registry-mgr/releases/latest.
   Choose the **tar.gz** (Linux/macOS) or **zip** (Windows).

2. Extract to a directory with no spaces in the path (e.g. ``/home/pds``):

   **Linux / macOS:**

   .. code:: bash

      tar -xzvf registry-manager-x.y.z-bin.tar.gz

   **Windows:** Right-click the zip and select **Extract All**.

3. Configure environment variables as described in :ref:`install/install:Configure Your Environment`.

4. Verify the installation:

   .. code:: bash

      registry-manager --help


Harvest
~~~~~~~

1. Download the latest stable release from https://github.com/NASA-PDS/harvest/releases/latest.
   Choose the **tar.gz** (Linux/macOS) or **zip** (Windows).

2. Extract to a directory with no spaces in the path (e.g. ``/home/pds``):

   **Linux / macOS:**

   .. code:: bash

      tar -xzvf harvest-x.y.z-bin.tar.gz

   **Windows:** Right-click the zip and select **Extract All**.

3. Configure environment variables as described in :ref:`install/install:Configure Your Environment`.

4. Verify the installation:

   .. code:: bash

      harvest --help


Registry Client
~~~~~~~~~~~~~~~

1. Follow the installation steps in the `Registry Client documentation <https://nasa-pds.github.io/registry-client/installation/index.html>`_.


Configure Your Environment
**************************

.. note::
   Optional but recommended. Without this step, run tools directly from the ``bin/`` directory of each downloaded package.

**Linux / macOS:**

1. Open your shell profile file (e.g. ``~/.bash_profile``, ``~/.zshrc``).

2. Add the following, updating each path to match your installation directories:

   .. code:: bash

      HARVEST_HOME=/path/to/harvest-x.y.z
      HARVEST_CLIENT_HOME=/path/to/registry-client-x.y.z
      REGISTRY_HOME=/path/to/registry-manager-x.y.z

      export PATH=${PATH}:$HARVEST_HOME/bin:$REGISTRY_HOME/bin:$HARVEST_CLIENT_HOME/bin

3. Reload your profile:

   .. code:: bash

      source ~/.bash_profile

**Windows:**

1. Open the Start Menu and search for **environment**.
2. Select **Edit environment variables for your account**.

   .. image:: /_static/images/win-env.png

3. In the **Environment Variables** dialog, edit the ``Path`` variable.
4. Add the ``bin`` directory for each installed tool (Harvest, Registry Manager, etc.).
