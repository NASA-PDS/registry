==================
Tools Installation
==================

Overview
********

This document describes how to install following PDS Registry tools (command-line applications):

 * **Standalone Harvest** extracts metadata from PDS4 labels and loads extracted metadata into PDS Registry.
 * **Harvest Client** has to be used with Scalable Harvest server components to submit asynchronous jobs
   to the server cluster.
 * **Registry Manager** is a tool to create Registry indices in OpenSearch and to 
   manage data and LDDs (data dictionaries).
 * **Supplementer** can be used to load supplemental metadata into PDS Registry.


Standalone Harvest
******************

Download latest non-snapshot binary release (tar or zip) from https://github.com/NASA-PDS/harvest/releases.
Extract the **tar** (Linux, Mac) or **zip** (Windows) to a directory without spaces, such as */home/pds*.
On Linux you can use the following command::

  % tar -xzvf harvest-x.y.z-bin.tar.gz


Harvest Client
**************

.. note::
   Only install this if you plan to use Scalable Harvest server.

Download latest non-snapshot binary release (tar or zip) from https://github.com/NASA-PDS/registry-harvest-cli/releases.
Extract the **tar** (Linux, Mac) or **zip** (Windows) to a directory without spaces, such as */home/pds*.
On Linux you can use the following command::

  % tar -xzvf registry-harvest-cli-x.y.z-bin.tar.gz


Registry Manager
****************

Download latest non-snapshot binary release (tar or zip) from https://github.com/NASA-PDS/registry-mgr/releases.
Extract the **tar** (Linux, Mac) or **zip** (Windows) to a directory without spaces, such as */home/pds*.
On Linux you can use the following command::

  % tar -xzvf registry-manager-x.y.z-bin.tar.gz


Supplementer
************

.. note::
   Only install this if you plan to load supplemental metadata.

Download latest non-snapshot binary release (tar or zip) from https://github.com/NASA-PDS/supplementer/releases.
Extract the **tar** (Linux, Mac) or **zip** (Windows) to a directory without spaces, such as */home/pds*.
On Linux you can use the following command::

  % tar -xzvf supplementer-x.y.z-bin.tar.gz


Configure your environment
**************************

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

**Windows**

Open the Start Menu and begin typing "environment". Select "Edit environment variables for your account". 

.. image:: /_static/images/win-env.png 

"Environment Variables" dialog will open where you can edit "Path" variable.
Add "bin" directory of Harvest, Registry Manager and other tools to "Path" variable. 

