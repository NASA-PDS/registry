===========
Delete Data
===========

Before You Begin
****************

- Access to the Registry Service configured per :doc:`/connection-setup`
- Registry Manager installed per :doc:`/install/install`


Run the Delete Command
**********************

Run Registry Manager's ``delete-data`` command. Replace ``{venue}``, ``{node}``, and the
identifier with your values.

**Linux / macOS — delete by LIDVID:**

.. code-block:: bash

   registry-manager delete-data \
       -auth $HOME/.pds/registry-auth-{venue}.txt \
       -es file://$HOME/.pds/registry-config-{node}-{venue}.xml \
       -lidvid urn:nasa:pds:context:target:asteroid.4_vesta::1.1

**Linux / macOS — delete by LID:**

.. code-block:: bash

   registry-manager delete-data \
       -auth $HOME/.pds/registry-auth-{venue}.txt \
       -es file://$HOME/.pds/registry-config-{node}-{venue}.xml \
       -lid urn:nasa:pds:context:target:asteroid.4_vesta

**Linux / macOS — delete by package / job ID:**

.. code-block:: bash

   registry-manager delete-data \
       -auth $HOME/.pds/registry-auth-{venue}.txt \
       -es file://$HOME/.pds/registry-config-{node}-{venue}.xml \
       -packageId 8d12a9ba-2ba0-4d80-8ce9-65da271ecf89

**Linux / macOS — delete all data:**

.. code-block:: bash

   registry-manager delete-data -all \
       -auth $HOME/.pds/registry-auth-{venue}.txt \
       -es file://$HOME/.pds/registry-config-{node}-{venue}.xml

**Windows — delete by LIDVID:**

.. code-block:: powershell

   .\registry-manager.bat delete-data `
       -auth '%USERPROFILE%\.pds\registry-auth-{venue}.txt' `
       -es 'file:///%USERPROFILE%\.pds\registry-config-{node}-{venue}.xml' `
       -lidvid 'urn:nasa:pds:insight_rad:data_derived::7.0'

**Windows — delete by package / job ID:**

.. code-block:: powershell

   .\registry-manager.bat delete-data `
       -auth '%USERPROFILE%\.pds\registry-auth-{venue}.txt' `
       -es 'file:///%USERPROFILE%\.pds\registry-config-{node}-{venue}.xml' `
       -packageId 8d12a9ba-2ba0-4d80-8ce9-65da271ecf89
