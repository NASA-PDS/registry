==============================
Load Data - Harvest
==============================

Harvest extracts metadata from PDS4 product labels and loads it into the Registry (OpenSearch).


Before You Begin
****************

- Connection to the registry service configured per :doc:`/connection-setup`
- Harvest installed per :doc:`/install/install`


Configure a Harvest Job
************************

Harvest uses an XML job configuration file. Example configs ship with the Harvest installation
under ``$HARVEST_HOME/conf/examples/`` (where ``$HARVEST_HOME`` is the directory you extracted
Harvest into per :doc:`/install/install`).

1. Copy the example config to ``$HOME/.pds/``, naming it to include the venue
   (``dev``, ``test``, or ``prod``) and the job (e.g. a mission name like ``lro`` or ``mars2020``):

   .. code:: bash

      cp $HARVEST_HOME/conf/examples/directories.xml $HOME/.pds/registry-harvest-config-{venue}-{job}.xml

2. Open ``$HOME/.pds/registry-harvest-config-{venue}-{job}.xml`` and set the ``<registry>`` element
   to point to your auth file and connection config file for this venue:

   .. code-block:: xml

      <registry auth="$HOME/.pds/registry-auth-{venue}.txt">file://$HOME/.pds/registry-config-{node}-{venue}.xml</registry>

3. Set the path to your PDS4 data:

   .. code-block:: xml

      <load>
        <directories>
          <path>/path/to/your/data</path>
        </directories>
      </load>

4. Set the URL prefix to replace local file paths with the publicly accessible base URL
   where your archive is published:

   .. code-block:: xml

      <fileInfo>
        <fileRef replacePrefix="/local/data/path/" with="https://your-node.example.com/data/" />
      </fileInfo>

   See :doc:`/user/harvest_job_configuration` for all available configuration options.

.. note::
   On Windows, use backslash-style paths. See the example screenshot below:

   .. image:: /_static/images/windows_harvest_conf_file.png


Run Harvest
***********

1. Run Harvest with your job config:

   .. code:: bash

      harvest -c $HOME/.pds/registry-harvest-config-{venue}-{job}.xml

2. Review the log output. A successful run ends with a summary similar to:

   .. code:: text

      [SUMMARY] Summary:
      [SUMMARY] Skipped files: 0
      [SUMMARY] Processed files: 14
      [SUMMARY] File counts by type:
      [SUMMARY]   Product_Bundle: 1
      [SUMMARY]   Product_Collection: 4
      [SUMMARY]   Product_Context: 3
      [SUMMARY]   Product_Document: 2
      [SUMMARY]   Product_Observational: 4
      [SUMMARY] Package ID: e46f6ba9-6151-48ee-b822-b0536e3e4bd9

3. Optionally, verify data was loaded by querying your index per :doc:`/user/test_connection`.

.. warning::
   Due to indexation delays, loaded data may take up to a few hours to become visible.


Next Steps
**********

- See all Harvest options: ``harvest -help``
- Additional job config options: :doc:`/user/harvest_job_configuration`
- Publish loaded data: :doc:`/user/update_status`
