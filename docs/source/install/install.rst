============
Installation
============

Overview
********

This document describes how to install following PDS Registry tools (command-line applications):

 * **Registry Manager** is a tool to create Registry indices in OpenSearch and to
   manage data and LDDs (data dictionaries).
 * **Harvest** extracts metadata from PDS4 labels and loads extracted metadata into PDS Registry.
 * **Registry Client** handle the authentication and request signing requirements to access the OpenSearch API for custom queries.
 * **Supplementer** can be used to load supplemental metadata into PDS Registry.


Prerequisites
*************

Java is required to run many Registry components and tools such as Harvest, Registry Manager,
and API Server.

Only **Java 17** is supported.
Some applications, like Harvest or Registry Manager will not run with **Java 1.8 or 11**.


Test If Java Is Already Installed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To test if Java is already installed on your system, run the following command in a terminal::

   java -version


If Java is already installed, you will see a message similar to this::

    openjdk version "17.0.2" 2022-01-18
    OpenJDK Runtime Environment (build 17.0.2+8-86)
    OpenJDK 64-Bit Server VM (build 17.0.2+8-86, mixed mode, sharing)

.. note::
   Your system might have multiple versions of Java installed, for example, JDK 11 and JDK 17.
   If JDK 17 is not the default, then set **JAVA_HOME** environment variable to point to JDK 17 before running
   Harvest or Registry Manager.


Java Installation
~~~~~~~~~~~~~~~~~

There are several distributions of Java:

* **OpenJDK** (Free) can be downloaded from different sites, for example,
  `adoptopenjdk.net <https://adoptopenjdk.net/>`_ or
  `azul.com <https://www.azul.com/downloads/zulu-community>`_.
  Most Linux distributions have Open JDK in their standard repositories.

* **Oracle JDK** (Commercial) can be downloaded from
  `www.oracle.com <https://www.oracle.com/java/technologies/javase-jdk11-downloads.html>`_.
  You must register and accept a license to download.


We recommend installing **OpenJDK**. Sites listed above have detailed installation instructions.

Python
~~~~~~

Registry Client requires python 3.13 or higher

An installation procedure is proposed in a `GitHub discussion <https://github.com/orgs/NASA-PDS/discussions/64>`_


Tools
*****

Registry Manager
~~~~~~~~~~~~~~~~~

Download latest stable release (tar or zip) from https://github.com/NASA-PDS/registry-mgr/releases/latest.
Extract the **tar** (Linux, Mac) or **zip** (Windows) to a directory without spaces, such as */home/pds*.
On Linux you can use the following command::

  % tar -xzvf registry-manager-x.y.z-bin.tar.gz


Set your environment variables ``REGISTRY_HOME`` and ``PATH`` as described in :ref:`Configure Your Environment`

Test by running::

  % registry-manager --help


Harvest
~~~~~~~

Download latest stable release (tar or zip) from https://github.com/NASA-PDS/harvest/releases/latest.
Extract the **tar** (Linux, Mac) or **zip** (Windows) to a directory without spaces, such as */home/pds*.
On Linux you can use the following command::

  % tar -xzvf harvest-x.y.z-bin.tar.gz

Set your environment variables ``HARVEST_HOME`` and ``PATH`` as described in :ref:`Configure Your Environment`

Test by running::

    % harvest --help


Registry Client
~~~~~~~~~~~~~~~~

To install Registry Client see `documentation <https://nasa-pds.github.io/registry-client/>`_.


Supplementer
~~~~~~~~~~~~~

.. note::
   Only install this if you plan to load supplemental metadata.

.. warning::
   Not tested with latest Registry service.

Download latest stable release (tar or zip) from https://github.com/NASA-PDS/supplementer/releases/latest.
Extract the **tar** (Linux, Mac) or **zip** (Windows) to a directory without spaces, such as */home/pds*.
On Linux you can use the following command::

  % tar -xzvf supplementer-x.y.z-bin.tar.gz



Configure Your Environment
**************************

.. note::
   Optional: Configuring your environment is preferred, but not required. You can always run any of the command-line tools from
   the ``bin/`` directory of the appropriate downloaded package.

Update PATH environment variable to be able to run registry tools from any directory.

**Linux, Mac**

For example, if you are using BASH, add the following to your *.bash_profile*::

  # Update path as needed

  HARVEST_HOME=/path/to/harvest-x.y.z
  HARVEST_CLIENT_HOME=/path/to/harvest-client-x.y.z
  REGISTRY_HOME=/path/to/registry-manager-x.y.z
  SUPPLEMENTER_HOME=/path/to/supplementer-x.y.z

  export PATH=${PATH}:$HARVEST_HOME/bin:$REGISTRY_HOME/bin
  export PATH=${PATH}:$HARVEST_CLIENT_HOME/bin:$SUPPLEMENTER_HOME/bin:

For users not using BASH, see your appropriate shell documentation for setting environment variables.

**Windows**

Open the Start Menu and begin typing "environment". Select "Edit environment variables for your account".

.. image:: /_static/images/win-env.png

"Environment Variables" dialog will open where you can edit "Path" variable.
Add "bin" directory of Harvest, Registry Manager and other tools to "Path" variable.
